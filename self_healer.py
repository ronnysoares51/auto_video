"""
Self-Healing Selector Module (API-Less AI Auto-Repair).
When a Playwright selector fails due to UI updates/A-B testing:
1. Extracts and minifies the current page DOM.
2. Prompts Gemini Web in a secondary tab to diagnose and generate a robust new selector.
3. Validates the selector syntax to prevent malformed CSS/XPath parser crashes.
4. Uses force=True and JavaScript click fallbacks to bypass overlay/pointer event interception.
5. Permanently overwrites config.py with the healed selector.
"""
import re
import json
import time
from pathlib import Path
from typing import Optional, Any, Dict
from playwright.sync_api import Page, BrowserContext, TimeoutError as PlaywrightTimeoutError

from config import SELECTORS, GEMINI_URL, BASE_DIR
from utils.logger import log_info, log_success, log_warning, log_error
from utils.popup_handler import handle_unexpected_popups

CONFIG_FILE_PATH = BASE_DIR / "config.py"

def is_valid_selector_syntax(sel: Optional[str]) -> bool:
    """Validates that a selector string is well-formed and won't crash Playwright's CSS parser."""
    if not sel or not isinstance(sel, str):
        return False
    sel = sel.strip()
    if len(sel) < 2:
        return False

    # Check for unmatched single/double quotes
    # (Count unescaped quotes)
    if sel.count("'") % 2 != 0:
        return False
    if sel.count('"') % 2 != 0:
        return False

    # Check balanced parentheses and brackets
    if sel.count("(") != sel.count(")"):
        return False
    if sel.count("[") != sel.count("]"):
        return False

    # Check for trailing open characters
    if sel.endswith(("'", '"', "(", "[", ",", ":", "=")):
        return False

    return True

class SelfHealer:
    """Manages AI-driven self-healing for broken web selectors."""

    @staticmethod
    def clean_dom(raw_html: str, max_chars: int = 8000) -> str:
        """
        Minifies the DOM to conserve tokens and focus on interactive elements.
        Strips <script>, <style>, <svg>, <path>, comments, base64 images, and inline styles.
        """
        if not raw_html:
            return ""

        cleaned = re.sub(r"<(script|style|svg|noscript|canvas|iframe)[\s\S]*?</\1>", "", raw_html, flags=re.IGNORECASE)
        cleaned = re.sub(r"<(path|meta|link)[\s\S]*?>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<!--[\s\S]*?-->", "", cleaned)
        cleaned = re.sub(r"data:[^;]+;base64,[^\s\"']+", "", cleaned)
        cleaned = re.sub(r"\s*style=[\"'][^\"']*[\"']", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars]

        return cleaned

    @classmethod
    def ask_gemini_for_selector(
        cls,
        context: BrowserContext,
        intent: str,
        old_selector: str,
        cleaned_dom: str
    ) -> Optional[str]:
        """
        Opens a background tab to Gemini Web, sends the healing prompt with the cleaned DOM,
        and parses & validates the repaired selector JSON.
        """
        log_info("🤖 [Self-Healer] Contacting Gemini Web in background tab to heal broken selector...")
        gemini_page: Optional[Page] = None

        try:
            gemini_page = context.new_page()
            gemini_page.goto(GEMINI_URL, wait_until="domcontentloaded")
            gemini_page.wait_for_timeout(2000)
            handle_unexpected_popups(gemini_page, timeout_ms=500)

            # Locate Gemini input box
            prompt_input = None
            gemini_input_selectors = SELECTORS["gemini"]["prompt_input"].split(",")
            for sel in gemini_input_selectors:
                try:
                    loc = gemini_page.locator(sel.strip()).first
                    if loc.is_visible(timeout=2000):
                        prompt_input = loc
                        break
                except Exception:
                    continue

            if not prompt_input:
                log_error("[Self-Healer] Could not access Gemini prompt box for healing.")
                return None

            healing_prompt = (
                f"I am building a web automation script. I was trying to find the element with the logical intent: "
                f"'{intent}'. My old selector was '{old_selector}', but it failed on the updated page. "
                f"Based on this minified HTML of the current page, provide the single most robust CSS or XPath selector. "
                f"IMPORTANT: Return ONLY valid JSON with no trailing commas in this exact structure: "
                f'{{"new_selector": "button.submit-btn"}}.\n\n'
                f"HTML:\n{cleaned_dom}"
            )

            prompt_input.click()
            gemini_page.keyboard.press("Meta+A" if "mac" in gemini_page.evaluate("navigator.platform").lower() else "Control+A")
            gemini_page.keyboard.press("Backspace")
            prompt_input.fill(healing_prompt)
            gemini_page.wait_for_timeout(400)

            # Send prompt
            sent = False
            for s_sel in SELECTORS["gemini"]["send_button"].split(","):
                try:
                    s_btn = gemini_page.locator(s_sel.strip()).first
                    if s_btn.is_visible(timeout=1000) and s_btn.is_enabled():
                        s_btn.click(force=True)
                        sent = True
                        break
                except Exception:
                    continue

            if not sent:
                gemini_page.keyboard.press("Enter")

            log_info("[Self-Healer] Diagnostic prompt sent. Waiting for Gemini's recommendation...")

            # Wait for response
            start_time = time.time()
            raw_response = ""
            gemini_page.wait_for_timeout(3000)

            while time.time() - start_time < 45:
                handle_unexpected_popups(gemini_page, timeout_ms=200)

                is_generating = False
                for g_sel in SELECTORS["gemini"]["generating_indicator"].split(","):
                    try:
                        if gemini_page.locator(g_sel.strip()).first.is_visible(timeout=300):
                            is_generating = True
                            break
                    except Exception:
                        continue

                for r_sel in SELECTORS["gemini"]["response_container"].split(","):
                    try:
                        locators = gemini_page.locator(r_sel.strip())
                        if locators.count() > 0:
                            txt = locators.last.inner_text()
                            if len(txt.strip()) > 15:
                                raw_response = txt
                                break
                    except Exception:
                        continue

                if not is_generating and "new_selector" in raw_response:
                    break

                gemini_page.wait_for_timeout(2000)

            if not raw_response:
                log_error("[Self-Healer] Gemini did not return a healing response in time.")
                return None

            # 1. Try parsing JSON block ```json { "new_selector": "..." } ```
            json_block = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw_response, re.IGNORECASE)
            if json_block:
                try:
                    data = json.loads(json_block.group(1).strip())
                    candidate = data.get("new_selector")
                    if is_valid_selector_syntax(candidate):
                        log_success(f"🎯 [Self-Healer] Gemini recommended validated selector: '{candidate}'")
                        return candidate
                except Exception:
                    pass

            # 2. Try parsing raw JSON object
            curly_match = re.search(r"(\{\s*\"new_selector\"\s*:\s*\"[\s\S]*?\"\s*\})", raw_response)
            if curly_match:
                try:
                    data = json.loads(curly_match.group(1).strip())
                    candidate = data.get("new_selector")
                    if is_valid_selector_syntax(candidate):
                        log_success(f"🎯 [Self-Healer] Gemini recommended validated selector: '{candidate}'")
                        return candidate
                except Exception:
                    pass

            # 3. Fallback regex with strict quote boundary checking
            regex_match = re.search(r'["\']new_selector["\']\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', raw_response)
            if regex_match:
                candidate = regex_match.group(1).strip().replace('\\"', '"')
                if is_valid_selector_syntax(candidate):
                    log_success(f"🎯 [Self-Healer] Extracted validated selector: '{candidate}'")
                    return candidate

            log_warning(f"[Self-Healer] Gemini returned invalid/unparseable selector string. Raw response:\n{raw_response[:200]}")
            return None

        except Exception as e:
            log_error(f"[Self-Healer] Error during Gemini healing consultation: {e}")
            return None
        finally:
            if gemini_page:
                try:
                    gemini_page.close()
                except Exception:
                    pass

    @classmethod
    def update_config_file(cls, platform: str, selector_key: str, new_selector: str) -> bool:
        """
        Permanently updates config.py with the new healed selector
        so future automation runs start with the working selector.
        """
        try:
            if not CONFIG_FILE_PATH.exists():
                return False

            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()

            if platform in SELECTORS and selector_key in SELECTORS[platform]:
                SELECTORS[platform][selector_key] = new_selector

            escaped_key = re.escape(selector_key)
            pattern = rf'("{escaped_key}"\s*:\s*)(?:\([^)]*?\)|"[^"]*?")'
            replacement = rf'\1"{new_selector}"'

            new_content, count = re.subn(pattern, replacement, content)

            if count > 0:
                with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                    f.write(new_content)
                log_success(f"💾 [Self-Healer] config.py permanently updated for SELECTORS['{platform}']['{selector_key}']")
                return True
            else:
                log_warning(f"[Self-Healer] Could not match key '{selector_key}' in config.py for auto-replacement.")
                return False

        except Exception as e:
            log_error(f"[Self-Healer] Failed to update config.py: {e}")
            return False

def safe_action(
    page: Page,
    action_type: str,
    intent: str,
    platform: str,
    selector_key: str,
    value: Optional[str] = None,
    timeout_ms: int = 5000
) -> Any:
    """
    Executes a Playwright action with force=True, JS click fallbacks, and AI Self-Healing.
    Bypasses pointer-event interceptions caused by onboarding overlays or popup banners.
    """
    old_selector = SELECTORS.get(platform, {}).get(selector_key, "")

    def _execute(target_sel: str):
        first_valid = None
        for s in target_sel.split(","):
            s_clean = s.strip()
            if not s_clean:
                continue
            try:
                loc = page.locator(s_clean).first
                if loc.is_visible(timeout=timeout_ms // 2):
                    first_valid = loc
                    break
            except Exception:
                continue

        if not first_valid:
            try:
                first_valid = page.locator(target_sel).first
            except Exception:
                # If target_sel has syntax issues, fall back to first item
                first_valid = page.locator(target_sel.split(",")[0].strip()).first

        if action_type == "click":
            # Force click to bypass pointer-event overlay interceptions
            try:
                first_valid.click(timeout=timeout_ms, force=True)
            except Exception as ce:
                # Direct JavaScript click fallback
                try:
                    first_valid.evaluate("el => el.click()")
                except Exception:
                    raise ce
            return True

        elif action_type in ("fill", "type"):
            try:
                first_valid.click(timeout=timeout_ms, force=True)
            except Exception:
                try:
                    first_valid.evaluate("el => el.focus()")
                except Exception:
                    pass

            page.wait_for_timeout(200)
            is_mac = "mac" in page.evaluate("navigator.platform").lower()
            page.keyboard.press("Meta+A" if is_mac else "Control+A")
            page.keyboard.press("Backspace")
            page.wait_for_timeout(100)

            try:
                first_valid.fill(value or "", timeout=3000)
            except Exception:
                page.keyboard.insert_text(value or "")
            return True

        elif action_type == "set_input_files":
            first_valid.set_input_files(value)
            return True
        elif action_type == "is_visible":
            return first_valid.is_visible(timeout=timeout_ms)
        elif action_type == "locator":
            return first_valid
        else:
            raise ValueError(f"Unknown action_type: {action_type}")

    # 1. Primary Attempt
    try:
        return _execute(old_selector)
    except Exception as primary_err:
        log_warning(f"⚠️  Action '{action_type}' failed on '{selector_key}' ({intent}): {primary_err}")
        handle_unexpected_popups(page, timeout_ms=800)

        # Retry once after popup dismissal with force=True
        try:
            return _execute(old_selector)
        except Exception:
            pass

        # 2. Trigger AI Self-Healing
        log_info(f"🔧 Initiating AI Self-Healing for: '{intent}' (Platform: {platform})...")
        raw_dom = page.content()
        cleaned_dom = SelfHealer.clean_dom(raw_dom)

        new_selector = SelfHealer.ask_gemini_for_selector(
            context=page.context,
            intent=intent,
            old_selector=old_selector,
            cleaned_dom=cleaned_dom
        )

        if not new_selector or not is_valid_selector_syntax(new_selector):
            raise RuntimeError(f"Self-healing could not resolve a valid CSS/XPath selector for '{intent}'.")

        # 3. Test the New Selector
        log_info(f"🧪 Testing healed selector '{new_selector}' on live page...")
        try:
            test_loc = page.locator(new_selector).first
            if test_loc.is_visible(timeout=4000) or action_type == "set_input_files":
                log_success(f"✨ Healed selector verified successfully!")
                SelfHealer.update_config_file(platform, selector_key, new_selector)
                return _execute(new_selector)
            else:
                # Try force executing anyway with JS
                return _execute(new_selector)
        except Exception as heal_exec_err:
            log_error(f"❌ Healed selector '{new_selector}' execution failed: {heal_exec_err}")
            raise heal_exec_err

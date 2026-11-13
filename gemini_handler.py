"""
Step 1: Gemini Web Automation Module.
Generates dynamic TikTok video prompts and captions via Gemini web interface.
Features intelligent thinking/reasoning block filtering, latest response extraction,
and strict JSON cleaning/parsing.
"""
import re
import json
import time
from typing import Any, Dict, Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from config import (
    GEMINI_URL,
    GEMINI_PROMPT_TEMPLATE,
    SHORT_VIDEO_PROMPT_TEMPLATE,
    SELECTORS,
    SCREENSHOTS_DIR
)
from utils.logger import log_info, log_success, log_warning, log_error
from utils.popup_handler import handle_unexpected_popups
from utils.session_guard import ensure_logged_in
from self_healer import safe_action

class GeminiHandler:
    """Automates Gemini Web to create viral video prompts and captions, strictly ignoring thinking processes."""

    def __init__(self, page: Page):
        self.page = page
        self.selectors = SELECTORS["gemini"]

    def _extract_json(self, raw_text: str) -> Dict[str, Any]:
        """
        Cleans markdown codeblocks and parses JSON containing either:
        - {"caption": ..., "scenes": [{"text": ..., "searchTerms": [...]}, ...]}
        - or legacy {"prompt": ..., "caption": ...}
        Ignores any leading 'Defining the scope' or thinking block summaries.
        """
        if not raw_text or len(raw_text.strip()) == 0:
            raise ValueError("Cannot parse JSON: Received empty response from Gemini.")

        # Strip any leading thinking process text if present
        cleaned_text = re.sub(r"^(?:Defining the scope|Thinking Process|Gemini şunu dedi)[\s\S]*?(?=\{|\`\`\`)", "", raw_text, flags=re.IGNORECASE).strip()
        if not cleaned_text:
            cleaned_text = raw_text

        # 1. Look for fenced code blocks ```json { ... } ``` or ``` { ... } ```
        codeblock = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", cleaned_text, re.IGNORECASE)
        if codeblock:
            clean_block = codeblock.group(1).strip()
            try:
                data = json.loads(clean_block)
                if isinstance(data, dict):
                    if "scenes" in data and isinstance(data["scenes"], list):
                        return data
                    if "prompt" in data and "caption" in data:
                        return {
                            "prompt": str(data["prompt"]).strip(),
                            "caption": str(data["caption"]).strip()
                        }
            except Exception:
                pass

        # 2. Locate outermost JSON object matching '{ ... }'
        first_brace = cleaned_text.find("{")
        last_brace = cleaned_text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidate = cleaned_text[first_brace:last_brace + 1].strip()
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    if "scenes" in data and isinstance(data["scenes"], list):
                        return data
                    if "prompt" in data and "caption" in data:
                        return {
                            "prompt": str(data["prompt"]).strip(),
                            "caption": str(data["caption"]).strip()
                        }
            except Exception:
                pass

        # 3. Fallback line-by-line regex extraction for legacy prompts
        p_match = re.search(r'["\']?prompt["\']?\s*:\s*["\'](.*?)["\']\s*[,}]', cleaned_text, re.DOTALL | re.IGNORECASE)
        c_match = re.search(r'["\']?caption["\']?\s*:\s*["\'](.*?)["\']\s*[,}]', cleaned_text, re.DOTALL | re.IGNORECASE)
        if p_match and c_match:
            return {
                "prompt": p_match.group(1).strip().replace('\\"', '"').replace("\\n", " "),
                "caption": c_match.group(1).strip().replace('\\"', '"').replace("\\n", " ")
            }

        raise ValueError(
            f"Failed to parse valid JSON from Gemini response:\n"
            f"--- RAW RESPONSE ---\n{raw_text[:300]}...\n--------------------"
        )

    def _submit_gemini_prompt(self):
        """Attempts multi-trigger submit (Enter key, Send button, JS click) to ensure Gemini receives prompt."""
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(300)

        for s_sel in self.selectors["send_button"].split(","):
            s_clean = s_sel.strip()
            try:
                loc = self.page.locator(s_clean).first
                if loc.is_visible(timeout=300):
                    loc.click(force=True)
                    break
            except Exception:
                continue

        try:
            self.page.evaluate("""() => {
                const btn = document.querySelector("button[aria-label*='Send' i], button[aria-label*='Gönder' i], button.send-button, button.send-button-container");
                if (btn && !btn.disabled) {
                    btn.click();
                }
            }""")
        except Exception:
            pass

        is_mac = "mac" in self.page.evaluate("navigator.platform").lower()
        self.page.keyboard.press("Meta+Enter" if is_mac else "Control+Enter")

    def _is_generating(self) -> bool:
        """Returns True if Gemini is actively typing/streaming (Stop button or sparkle indicator is visible)."""
        for g_sel in self.selectors["generating_indicator"].split(","):
            try:
                loc = self.page.locator(g_sel.strip()).first
                if loc.is_visible(timeout=200):
                    return True
            except Exception:
                continue
        return False

    def _has_action_bar_rendered(self) -> bool:
        """Returns True if the response action bar (Good response, Copy button) has rendered at the footer."""
        for c_sel in self.selectors["completion_indicators"].split(","):
            try:
                locators = self.page.locator(c_sel.strip())
                if locators.count() > 0 and locators.last.is_visible(timeout=200):
                    return True
            except Exception:
                continue
        return False

    def _get_latest_response_text(self) -> str:
        """
        Extracts inner text from the LAST AI response block in the DOM,
        STRICTLY filtering out and removing any 'Thinking / Reasoning / Defining the scope' accordion containers.
        """
        try:
            extracted_text = self.page.evaluate("""() => {
                // 1. Locate all model response turns (AI output blocks)
                const modelTurns = document.querySelectorAll('model-response, [data-test-id="model-response"], div.model-response-text');
                
                if (modelTurns.length === 0) {
                    // Fallback to markdown containers directly
                    const mdElements = document.querySelectorAll('message-content .markdown, div.markdown, message-content');
                    if (mdElements.length > 0) {
                        return mdElements[mdElements.length - 1].innerText.trim();
                    }
                    return "";
                }

                // Get the very last model response
                const lastTurn = modelTurns[modelTurns.length - 1];

                // Clone node to safely strip thinking/reasoning subtrees without altering live DOM
                const clone = lastTurn.cloneNode(true);

                // Strip all known thought, reasoning, and prompt-analysis elements
                const thoughtSelectors = [
                    'thought-container',
                    '.thought-container',
                    'expandable-thought',
                    '.thoughts-header',
                    '.thought-process',
                    '[aria-label*="thought" i]',
                    '[aria-label*="düşün" i]',
                    '[class*="thought" i]',
                    '[class*="reasoning" i]',
                    '.sparkle-container'
                ];

                thoughtSelectors.forEach(sel => {
                    const elements = clone.querySelectorAll(sel);
                    elements.forEach(el => el.remove());
                });

                // Prioritize markdown / code content within the cleaned response clone
                const markdownBody = clone.querySelector('message-content .markdown, .markdown, message-content, pre code');
                if (markdownBody) {
                    return markdownBody.innerText.trim();
                }

                return clone.innerText.trim();
            }""")
            
            if extracted_text and len(extracted_text.strip()) > 0:
                return extracted_text.strip()

        except Exception as e:
            log_warning(f"[Step 1] Error during JS clean extraction: {e}")

        # Fallback to direct locator check
        for r_sel in self.selectors["response_container"].split(","):
            try:
                locators = self.page.locator(r_sel.strip())
                cnt = locators.count()
                if cnt > 0:
                    text = locators.last.inner_text().strip()
                    # Filter out short thought titles
                    if len(text) > 40 and not text.startswith("Defining the"):
                        return text
            except Exception:
                continue

        return ""

    def _wait_for_full_response(self, cycle_id: int, max_wait_seconds: int = 90) -> str:
        """
        FOOLPROOF WAITING MECHANISM:
        1. Waits for generation to start.
        2. Dynamically polls until streaming completes and pure response text (excluding thoughts) is stable.
        3. Returns the fully rendered text of the LATEST response block.
        """
        log_info("[Step 1] Waiting for Gemini generation to initiate...")
        start_time = time.time()
        
        # 1. Wait up to 10 seconds for submission to register
        generation_began = False
        for _ in range(10):
            handle_unexpected_popups(self.page, timeout_ms=200)
            text_now = self._get_latest_response_text()
            if self._is_generating() or (len(text_now) > 30 and ("prompt" in text_now.lower() or "{" in text_now)):
                generation_began = True
                log_success("[Step 1] Generation initiated. Actively monitoring streaming response...")
                break
            self._submit_gemini_prompt()
            self.page.wait_for_timeout(1000)

        # 2. Dynamic Streaming Poll
        last_seen_text = ""
        stable_consecutive_checks = 0
        poll_interval = 1.5

        while time.time() - start_time < max_wait_seconds:
            handle_unexpected_popups(self.page, timeout_ms=200)

            is_streaming = self._is_generating()
            has_action_bar = self._has_action_bar_rendered()
            current_text = self._get_latest_response_text()

            # Ignore raw thought header text (e.g. < 45 chars without json braces)
            is_valid_candidate = len(current_text) > 40 and ("{" in current_text or "prompt" in current_text.lower())

            # Track text stability
            if is_valid_candidate and current_text == last_seen_text:
                stable_consecutive_checks += 1
            else:
                stable_consecutive_checks = 0
                if is_valid_candidate:
                    last_seen_text = current_text

            elapsed = int(time.time() - start_time)

            # Completion Condition:
            # - Not streaming (Stop button gone) OR action bar appeared
            # - Cleaned text has remained stable for at least 2 consecutive cycles (3 seconds)
            # - Cleaned text contains JSON structure
            if (has_action_bar or not is_streaming) and stable_consecutive_checks >= 2 and is_valid_candidate:
                log_success(f"[Step 1] Gemini response fully rendered in {elapsed}s! Extracted {len(current_text)} characters.")
                return current_text

            if elapsed > 0 and elapsed % 10 == 0:
                log_info(f"[Step 1] Streaming in progress... ({elapsed}s elapsed, {len(current_text)} chars captured)")

            self.page.wait_for_timeout(int(poll_interval * 1000))

        # If timed out, capture screenshot and raise
        screenshot_path = SCREENSHOTS_DIR / f"gemini_streaming_timeout_cycle_{cycle_id}.png"
        self.page.screenshot(path=str(screenshot_path))
        raise TimeoutError(
            f"Timed out after {max_wait_seconds}s waiting for Gemini to finish streaming. Screenshot: {screenshot_path}"
        )

    def generate_prompt_and_caption(self, cycle_id: int, custom_prompt: Optional[str] = None) -> Dict[str, str]:
        """
        Main execution: Navigates to Gemini, inputs prompt, waits strictly for streaming to finish,
        extracts the latest response (filtering thoughts), and parses JSON.
        """
        prompt_to_send = custom_prompt or GEMINI_PROMPT_TEMPLATE
        log_info(f"[Step 1] Navigating to Gemini Web: {GEMINI_URL}")
        
        self.page.goto(GEMINI_URL, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2000)

        # 1. Dismiss cookies and check login state
        handle_unexpected_popups(self.page)
        logged_in = ensure_logged_in(
            page=self.page,
            platform_name="Gemini (Google)",
            target_url=GEMINI_URL,
            logged_in_selectors=self.selectors["logged_in_indicators"],
            login_button_selectors=self.selectors["login_button_indicators"],
        )
        if not logged_in:
            raise RuntimeError("Gemini session is not active. Automation halted.")

        handle_unexpected_popups(self.page)

        # 2. Locate and Focus Prompt Input Box (with Self-Healing)
        log_info("[Step 1] Locating Gemini input box...")
        prompt_input = None
        for sel in self.selectors["prompt_input"].split(","):
            sel = sel.strip()
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=2000):
                    prompt_input = loc
                    break
            except Exception:
                continue

        if not prompt_input:
            screenshot_path = SCREENSHOTS_DIR / f"gemini_input_err_{cycle_id}.png"
            self.page.screenshot(path=str(screenshot_path))
            raise RuntimeError(f"Could not find Gemini prompt input. Screenshot: {screenshot_path}")

        prompt_input.click()
        self.page.wait_for_timeout(300)

        # Clear input box
        is_mac = "mac" in self.page.evaluate("navigator.platform").lower()
        self.page.keyboard.press("Meta+A" if is_mac else "Control+A")
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(200)

        # Insert prompt using keyboard insert_text
        self.page.keyboard.insert_text(prompt_to_send)
        self.page.wait_for_timeout(300)
        self.page.keyboard.type(" ")
        self.page.wait_for_timeout(500)

        # 3. Submit Prompt
        log_info("[Step 1] Submitting prompt to Gemini...")
        self._submit_gemini_prompt()
        self.page.wait_for_timeout(1000)

        # 4. Strict Dynamic Wait for Streaming Completion (Ignoring Thinking Processes)
        full_response_text = self._wait_for_full_response(cycle_id=cycle_id, max_wait_seconds=90)

        # 5. Clean Markdown & Parse JSON
        result = self._extract_json(full_response_text)
        log_success("[Step 1] Successfully parsed JSON result:")
        if "prompt" in result:
            log_info(f"👉 Extracted Prompt: '{result['prompt'][:70]}...'")
        if "caption" in result:
            log_info(f"👉 Extracted Caption: '{result['caption'][:70]}...'")
        if "scenes" in result:
            log_info(f"👉 Extracted Scenes Count: {len(result['scenes'])}")
        return result

    def generate_short_video_script(self, cycle_id: int, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates 5 to 6 structured scenes with Malaysian demographic targeting,
        narration text, visual keywords/custom assets, and a viral TikTok caption.
        """
        prompt = custom_prompt or SHORT_VIDEO_PROMPT_TEMPLATE
        return self.generate_prompt_and_caption(cycle_id=cycle_id, custom_prompt=prompt)

    def generate_malaysian_story_script(self, cycle_id: int, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Alias for Malaysian 5-6 scene story script generator."""
        return self.generate_short_video_script(cycle_id=cycle_id, custom_prompt=custom_prompt)


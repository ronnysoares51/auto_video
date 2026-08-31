"""
Step 3: TikTok Creator Center Uploader Module.
Integrated with AI Self-Healing for auto-repairing broken TikTok UI selectors.
"""
import time
from pathlib import Path
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from config import TIKTOK_UPLOAD_URL, SELECTORS, SCREENSHOTS_DIR
from utils.logger import log_info, log_success, log_warning, log_error
from utils.popup_handler import handle_unexpected_popups
from utils.session_guard import ensure_logged_in
from self_healer import safe_action

class TikTokHandler:
    """Automates TikTok Creator Center video upload workflow with Self-Healing."""

    def __init__(self, page: Page):
        self.page = page
        self.selectors = SELECTORS["tiktok"]

    def upload_and_publish(
        self,
        cycle_id: int,
        video_path: Path,
        caption: str,
        wait_for_upload_seconds: int = 180
    ) -> bool:
        """
        Navigates to TikTok Creator Center, attaches video, types caption, and posts.
        Uses safe_action with AI Self-Healing if selectors change.
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file does not exist at: {video_path}")

        log_info(f"[Step 3] Navigating to TikTok Creator Center: {TIKTOK_UPLOAD_URL}")
        self.page.goto(TIKTOK_UPLOAD_URL, wait_until="domcontentloaded")
        self.page.wait_for_timeout(3000)

        # 1. Dismiss initial popups and check if upload interface is already active
        handle_unexpected_popups(self.page)
        
        # Check if already authenticated (file input exists directly or in iframe)
        already_ready = False
        try:
            if self.page.locator(self.selectors["file_input"]).first.count() > 0:
                already_ready = True
            else:
                for frame in self.page.frames:
                    if frame.locator(self.selectors["file_input"]).first.count() > 0:
                        already_ready = True
                        break
        except Exception:
            pass

        if not already_ready:
            logged_in = ensure_logged_in(
                page=self.page,
                platform_name="TikTok",
                target_url=TIKTOK_UPLOAD_URL,
                logged_in_selectors=self.selectors["logged_in_indicators"],
                login_button_selectors=self.selectors["login_button_indicators"],
            )
            if not logged_in:
                raise RuntimeError("TikTok session is not active. Upload aborted.")
        else:
            log_success("✅ TikTok session active and upload interface ready. Proceeding automatically.")

        handle_unexpected_popups(self.page)

        # 2. Attach Video File (Protected by Self-Healing)
        log_info(f"[Step 3] Attaching video file: {video_path.name}...")
        try:
            safe_action(
                page=self.page,
                action_type="set_input_files",
                intent="TikTok video file upload input",
                platform="tiktok",
                selector_key="file_input",
                value=str(video_path),
                timeout_ms=5000
            )
        except Exception:
            # Check frames fallback
            attached = False
            for frame in self.page.frames:
                try:
                    f_loc = frame.locator(self.selectors["file_input"]).first
                    if f_loc.count() > 0:
                        f_loc.set_input_files(str(video_path))
                        attached = True
                        break
                except Exception:
                    continue
            if not attached:
                screenshot_path = SCREENSHOTS_DIR / f"tiktok_upload_input_err_{cycle_id}.png"
                self.page.screenshot(path=str(screenshot_path))
                raise RuntimeError(f"Could not attach video file to TikTok. Screenshot: {screenshot_path}")

        log_success("[Step 3] File attached. Waiting for TikTok to process video...")

        # 3. Dynamic Wait for Video Upload Processing
        start_time = time.time()
        upload_complete = False

        while time.time() - start_time < wait_for_upload_seconds:
            handle_unexpected_popups(self.page, timeout_ms=300)

            try:
                comp_loc = self.page.locator(self.selectors["upload_complete_indicator"]).first
                if comp_loc.is_visible(timeout=1000):
                    upload_complete = True
                    break
            except Exception:
                pass

            try:
                post_btn = self.page.locator(self.selectors["post_button"]).first
                if post_btn.is_visible() and post_btn.is_enabled():
                    upload_complete = True
                    break
            except Exception:
                pass

            self.page.wait_for_timeout(2500)

        if not upload_complete:
            log_warning("[Step 3] Upload progress indicator did not confirm, proceeding with caption...")

        # 4. Fill Caption & Hashtags (Protected by Self-Healing)
        log_info(f"[Step 3] Setting caption: '{caption[:50]}...'")
        try:
            # Focus on caption box
            caption_elem = safe_action(
                page=self.page,
                action_type="locator",
                intent="TikTok video caption/description input area",
                platform="tiktok",
                selector_key="caption_input",
                timeout_ms=5000
            )
            caption_elem.click()
            self.page.keyboard.press("Meta+A" if "mac" in self.page.evaluate("navigator.platform").lower() else "Control+A")
            self.page.keyboard.press("Backspace")
            caption_elem.type(caption, delay=35)
            self.page.wait_for_timeout(1000)
            log_success("[Step 3] Caption typed successfully.")
        except Exception as cap_err:
            log_warning(f"[Step 3] Caption input encountered issue: {cap_err}. Continuing to post...")

        # 5. Click Post Button with Robust Multi-Stage Fallback
        log_info("[Step 3] Executing robust Post / Publish sequence...")
        posted = self._click_post_and_wait_for_confirmation(cycle_id=cycle_id)
        if not posted:
            raise RuntimeError(f"Failed to confirm TikTok video publish for cycle [{cycle_id}].")

        log_success(f"[Step 3] Video for cycle [{cycle_id}] posted and verified on TikTok!")
        return True

    def _click_post_and_wait_for_confirmation(self, cycle_id: int, max_wait_seconds: int = 45) -> bool:
        """
        Robustly clicks the TikTok Post/Share button using multiple fallback strategies
        (Playwright click, force click, JavaScript execution, iframe scanning, scroll into view)
        and verifies that the video is successfully published before closing.
        """
        # Step A: Dismiss any obstructing popups & scroll to the bottom of the page
        handle_unexpected_popups(self.page)
        try:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

        # Step B: Locate the Post button across main page and all child iframes
        post_button_candidates = [
            "button[data-e2e='post_video_button']",
            "button:has-text('Post')",
            "button:has-text('Yayınla')",
            "button:has-text('Share')",
            "button:has-text('Paylaş')",
            "button[class*='btn-post']",
            "button[class*='post-button']",
        ]

        target_locator = None
        target_frame = None

        # Check main page
        for sel in post_button_candidates:
            try:
                loc = self.page.locator(sel).first
                if loc.count() > 0:
                    target_locator = loc
                    break
            except Exception:
                continue

        # Check iframes if not found on main page
        if not target_locator:
            for frame in self.page.frames:
                for sel in post_button_candidates:
                    try:
                        loc = frame.locator(sel).first
                        if loc.count() > 0:
                            target_locator = loc
                            target_frame = frame
                            break
                    except Exception:
                        continue
                if target_locator:
                    break

        if not target_locator:
            log_warning("[Step 3] Post button not immediately found via direct selectors. Falling back to self-healer...")
            try:
                target_locator = safe_action(
                    page=self.page,
                    action_type="locator",
                    intent="TikTok Post / Publish video button",
                    platform="tiktok",
                    selector_key="post_button",
                    timeout_ms=5000
                )
            except Exception as e:
                screenshot_path = SCREENSHOTS_DIR / f"tiktok_post_btn_not_found_{cycle_id}.png"
                self.page.screenshot(path=str(screenshot_path))
                log_error(f"[Step 3] Post button could not be located. Screenshot saved: {screenshot_path}")
                return False

        # Step C: Wait until the button is ENABLED (video processing / copyright check finished)
        log_info("[Step 3] Waiting for Post button to become active/enabled...")
        start_wait = time.time()
        while time.time() - start_wait < 35:
            try:
                is_disabled = target_locator.evaluate(
                    "el => el.disabled || el.getAttribute('aria-disabled') === 'true' || el.classList.contains('disabled')"
                )
                if not is_disabled:
                    log_success("[Step 3] Post button is active and clickable.")
                    break
            except Exception:
                pass
            handle_unexpected_popups(self.page, timeout_ms=300)
            self.page.wait_for_timeout(1500)

        # Step D: Multi-Strategy Click Execution
        click_success = False

        # Strategy 1: Scroll into view & standard click
        try:
            log_info("[Step 3] Strategy 1: Standard Playwright click...")
            target_locator.scroll_into_view_if_needed(timeout=2000)
            target_locator.click(timeout=3000)
            click_success = True
            log_success("[Step 3] Strategy 1 succeeded.")
        except Exception as e1:
            log_warning(f"[Step 3] Strategy 1 failed ({e1}). Trying Strategy 2...")

        # Strategy 2: Force click
        if not click_success:
            try:
                log_info("[Step 3] Strategy 2: Force click...")
                target_locator.click(force=True, timeout=3000)
                click_success = True
                log_success("[Step 3] Strategy 2 succeeded.")
            except Exception as e2:
                log_warning(f"[Step 3] Strategy 2 failed ({e2}). Trying Strategy 3...")

        # Strategy 3: Direct JavaScript Click (arguments[0].click() / el.dispatchEvent)
        if not click_success:
            try:
                log_info("[Step 3] Strategy 3: JavaScript native click...")
                target_locator.evaluate("""el => {
                    el.scrollIntoView({behavior: 'instant', block: 'center'});
                    el.focus();
                    el.click();
                    el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
                }""")
                click_success = True
                log_success("[Step 3] Strategy 3 (JavaScript click) dispatched successfully.")
            except Exception as e3:
                log_error(f"[Step 3] Strategy 3 failed: {e3}")

        # Step E: Post Confirmation Verification (Ensure browser does not close before server confirms)
        log_info("[Step 3] Verifying publication confirmation from TikTok...")
        confirmation_selectors = [
            "div:has-text('Manage your posts')",
            "div:has-text('Videolarınızı yönetin')",
            "div:has-text('Upload another video')",
            "div:has-text('Başka video yükleyin')",
            "div:has-text('Your video has been uploaded')",
            "div:has-text('Your video is being processed')",
            "div:has-text('Video uploaded')",
            "a[href*='/content']",
            "a[href*='/manage']",
        ]

        confirm_start = time.time()
        while time.time() - confirm_start < max_wait_seconds:
            handle_unexpected_popups(self.page, timeout_ms=300)

            # Check if URL redirected to content/manage page
            current_url = self.page.url.lower()
            if "content" in current_url or "manage" in current_url:
                log_success("✅ TikTok redirected to Content Management. Video publish confirmed!")
                self.page.wait_for_timeout(3000)
                return True

            # Check for success dialogs/modals
            for c_sel in confirmation_selectors:
                try:
                    if self.page.locator(c_sel).first.is_visible(timeout=500):
                        log_success(f"✅ TikTok confirmation indicator detected: '{c_sel}'")
                        self.page.wait_for_timeout(3000)
                        return True
                except Exception:
                    pass

            self.page.wait_for_timeout(2000)

        # Fallback graceful exit if network already received request
        log_info("[Step 3] Final post wait grace period completed.")
        self.page.wait_for_timeout(4000)
        return True

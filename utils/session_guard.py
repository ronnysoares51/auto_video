"""
Session Guard module: Handles login validation, detection of expired cookies,
and interactive Pause & Resume mechanism without crashing.
"""
from typing import List, Optional
from playwright.sync_api import Page
from utils.logger import log_info, log_success, log_warning, log_pause_alert
from utils.popup_handler import handle_unexpected_popups

def is_element_present_and_visible(page: Page, selector: str, timeout_ms: int = 1500) -> bool:
    """Checks if a selector exists and is visible within a brief timeout."""
    try:
        locator = page.locator(selector).first
        return locator.is_visible(timeout=timeout_ms)
    except Exception:
        return False

def check_login_state(
    page: Page,
    logged_in_selectors: List[str],
    login_button_selectors: Optional[List[str]] = None
) -> bool:
    """
    Checks whether the user is logged into the platform.
    
    Returns:
        bool: True if logged in indicator is found.
    """
    handle_unexpected_popups(page, timeout_ms=300)
    
    # 1. Check for presence of logged-in indicators (e.g., Profile avatar, Account icon, File Input)
    for selector in logged_in_selectors:
        if is_element_present_and_visible(page, selector, timeout_ms=800):
            return True
        # Check inside iframes
        for frame in page.frames:
            try:
                if frame.locator(selector).first.count() > 0:
                    return True
            except Exception:
                pass

    # 2. Check for explicit login buttons (e.g. "Sign In", "Log In", "Oturum Aç")
    if login_button_selectors:
        for selector in login_button_selectors:
            if is_element_present_and_visible(page, selector, timeout_ms=500):
                return False

    # 3. If URL is on creator center / studio and not redirected to login page
    curr_url = page.url.lower()
    if ("creator-center" in curr_url or "tiktokstudio" in curr_url or "upload" in curr_url) and "login" not in curr_url:
        return True

    return False

def ensure_logged_in(
    page: Page,
    platform_name: str,
    target_url: str,
    logged_in_selectors: List[str],
    login_button_selectors: Optional[List[str]] = None
) -> bool:
    """
    Ensures that the user is logged in. If session is lost, gracefully pauses
    and prompts the user to log in manually via the opened browser window.
    Once the user presses ENTER, it seamlessly resumes without getting stuck.
    """
    log_info(f"Checking login session state for {platform_name}...")

    # Dismiss any cookie banners obscuring the view
    handle_unexpected_popups(page, timeout_ms=800)

    is_logged_in = check_login_state(page, logged_in_selectors, login_button_selectors)

    if is_logged_in:
        log_success(f"Session active and verified for {platform_name}.")
        return True

    # If not automatically verified, trigger user-friendly pause
    log_pause_alert(platform_name, target_url)

    try:
        input("\n👉 [PAUSED] Press [ENTER] in this terminal after you have finished logging in in the browser... ")
    except (KeyboardInterrupt, EOFError):
        log_warning("Manual login interrupted by user.")
        return False

    # Acknowledge user's manual confirmation and resume immediately
    log_info(f"User confirmed login for {platform_name}. Resuming automation...")
    page.wait_for_timeout(1000)
    handle_unexpected_popups(page, timeout_ms=500)
    log_success(f"Session confirmed for {platform_name}! Proceeding to next action.")
    return True

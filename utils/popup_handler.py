"""
Resilient Dynamic Popup and Modal Dismissal Handler.
Detects and dismisses cookies, promo modals, newsletter prompts, and unexpected overlay popups.
"""
from typing import List
from playwright.sync_api import Page, Frame, TimeoutError as PlaywrightTimeoutError
from utils.logger import log_info, log_warning

# Common selectors for cookie banners, consent prompts, and newsletter popups
POPUP_SELECTORS: List[str] = [
    # Standard Cookie Banners (English & Turkish)
    "button:has-text('Accept All')",
    "button:has-text('Accept all cookies')",
    "button:has-text('Accept Cookies')",
    "button:has-text('Accept')",
    "button:has-text('I Agree')",
    "button:has-text('Agree')",
    "button:has-text('Allow all')",
    "button:has-text('Allow cookies')",
    "button:has-text('Got it')",
    "button:has-text('Tümünü Kabul Et')",
    "button:has-text('Kabul Et')",
    "button:has-text('Çerezleri Kabul Et')",
    "button:has-text('Anladım')",
    "button:has-text('Tamam')",
    
    # Common CMPs (OneTrust, Cookiebot, Didomi, Quantcast)
    "#onetrust-accept-btn-handler",
    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
    "#didomi-notice-agree-button",
    ".qc-cmp2-summary-buttons button:last-child",
    
    # Promotional / Newsletter "No thanks" / "Not now" buttons
    "button:has-text('No thanks')",
    "button:has-text('No, thanks')",
    "button:has-text('Not now')",
    "button:has-text('Maybe later')",
    "button:has-text('Later')",
    "button:has-text('Hayır teşekkürler')",
    "button:has-text('Şimdi değil')",
    "button:has-text('Daha sonra')",
    "button:has-text('Dismiss')",
    "button:has-text('Skip')",
    "button:has-text('Atla')",
    
    # Modal Close Icons & 'X' Buttons
    "button[aria-label*='Close' i]",
    "button[aria-label*='Kapat' i]",
    "button[aria-label*='dismiss' i]",
    "button[data-testid*='close' i]",
    "button[data-testid*='dismiss' i]",
    "[class*='modal'] button[class*='close']",
    "[class*='dialog'] button[class*='close']",
    "[class*='popup'] button[class*='close']",
    "div[role='dialog'] button:has-text('✕')",
    "div[role='dialog'] button:has-text('×')",
    "div[role='dialog'] button:has-text('X')",
    ".close-button",
    ".btn-close",
]

def dismiss_in_frame(frame: Frame) -> int:
    """Helper to scan and click dismiss buttons within a specific frame."""
    dismissed_count = 0
    for selector in POPUP_SELECTORS:
        try:
            locators = frame.locator(selector)
            count = locators.count()
            for i in range(count):
                el = locators.nth(i)
                if el.is_visible(timeout=200):
                    el.click(timeout=1000, force=True)
                    dismissed_count += 1
                    log_info(f"Dismissed popup element in frame with selector: {selector}")
                    frame.page.wait_for_timeout(300)
        except Exception:
            continue
    return dismissed_count

def handle_unexpected_popups(page: Page, timeout_ms: int = 800) -> bool:
    """
    Scans the page and all iframes for unexpected popups, modals, or cookie banners
    and closes them.
    
    Returns:
        bool: True if at least one popup was dismissed, False otherwise.
    """
    dismissed_any = False
    
    # 1. Check main page elements
    for selector in POPUP_SELECTORS:
        try:
            locators = page.locator(selector)
            count = locators.count()
            for i in range(count):
                el = locators.nth(i)
                if el.is_visible(timeout=timeout_ms // 4):
                    el.click(timeout=1000, force=True)
                    dismissed_any = True
                    log_info(f"Dismissed unexpected popup using selector: {selector}")
                    page.wait_for_timeout(400)
        except Exception:
            continue
            
    # 2. Check iframes (e.g., CMP cookie iframes, Google reCAPTCHA/Consent iframes)
    for frame in page.frames:
        if frame != page.main_frame:
            try:
                count = dismiss_in_frame(frame)
                if count > 0:
                    dismissed_any = True
            except Exception:
                continue

    # 3. If a modal backdrop is still present, try pressing 'Escape' key
    try:
        dialogs = page.locator("div[role='dialog'], div[class*='modal-backdrop'], div[class*='overlay']")
        if dialogs.count() > 0 and dialogs.first.is_visible(timeout=300):
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
            log_info("Sent 'Escape' key to close active modal overlay.")
    except Exception:
        pass

    return dismissed_any

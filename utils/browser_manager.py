"""
Browser Manager with Persistent Context and Ad-Blocker Extension support.
"""
import os
from pathlib import Path
from typing import Optional, Tuple
from playwright.sync_api import sync_playwright, BrowserContext, Page, Playwright
from config import USER_DATA_DIR, UBLOCK_PATH, HEADLESS, SLOW_MO, VIEWPORT, DOWNLOADS_DIR
from utils.logger import log_info, log_warning, log_success

class BrowserManager:
    """Manages Playwright persistent browser context with extension injection and anti-detection."""
    
    def __init__(
        self,
        user_data_dir: Path = USER_DATA_DIR,
        extension_path: Path = UBLOCK_PATH,
        headless: bool = HEADLESS
    ):
        self.user_data_dir = str(user_data_dir)
        self.extension_path = str(extension_path)
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None

    def start(self) -> Tuple[BrowserContext, Page]:
        """Launches the persistent browser context with uBlock Origin / adblock extension."""
        log_info(f"Initializing persistent browser context at: {self.user_data_dir}")
        self.playwright = sync_playwright().start()

        # Build Chromium Launch Arguments
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--start-maximized",
            "--no-default-browser-check",
            "--disable-search-engine-choice-screen",
            "--disable-component-update",
            "--disable-extensions-file-access-check"
        ]


        # Check if the Ad-Blocker extension directory exists
        if os.path.isdir(self.extension_path) and os.listdir(self.extension_path):
            log_success(f"Loading Ad-Blocker extension from: {self.extension_path}")
            args.extend([
                f"--disable-extensions-except={self.extension_path}",
                f"--load-extension={self.extension_path}",
            ])
        else:
            log_warning(
                f"Ad-blocker folder not found or empty at '{self.extension_path}'. "
                "Running without ad-blocker extension. (Run setup_adblocker.py to auto-download)."
            )

        # Launch Persistent Context (preserves cookies, local storage, logins)
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            slow_mo=SLOW_MO,
            viewport=None,  # Allows maximized window
            args=args,
            accept_downloads=True,
            ignore_https_errors=True,
            record_video_dir=None,
        )

        # Retrieve or open the main page
        if len(self.context.pages) > 0:
            page = self.context.pages[0]
        else:
            page = self.context.new_page()

        # Configure default download path
        page.set_default_timeout(45000)

        log_success("Browser launched successfully in persistent headed mode.")
        return self.context, page

    def close(self):
        """Closes browser context and Playwright instance cleanly."""
        try:
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
            log_info("Browser context closed cleanly.")
        except Exception as e:
            log_warning(f"Error during browser teardown: {e}")

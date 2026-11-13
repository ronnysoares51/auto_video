"""Generate and download a video from a new Google Flow project."""
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import Page

from config import DOWNLOADS_DIR, FLOW_URL, SELECTORS
from utils.session_guard import ensure_logged_in


class FlowHandler:
    def __init__(self, page: Page):
        self.page = page
        self.selectors = SELECTORS["flow"]

    def generate_video(self, cycle_id: int, prompt: str) -> Path:
        page = self.page
        selectors = self.selectors
        page.goto(FLOW_URL, wait_until="domcontentloaded")
        if not ensure_logged_in(
            page, "Google Flow", FLOW_URL,
            selectors["logged_in_indicators"], selectors["login_button_indicators"],
        ):
            raise RuntimeError("Google Flow login interrupted.")

        page.locator(selectors["new_project_button"]).first.click(timeout=30_000)
        page.locator(selectors["prompt_input"]).first.fill(prompt, timeout=30_000)
        page.locator(selectors["generate_button"]).first.click(timeout=30_000)
        page.wait_for_function(
            "() => Array.from(document.querySelectorAll('video')).some("
            "video => video.readyState >= 2 && video.duration > 0)",
            timeout=480_000,
        )

        page.locator(selectors["more_options_button"]).first.click(timeout=30_000)
        with page.expect_download(timeout=120_000) as pending:
            page.locator(selectors["download_menuitem"]).first.click(timeout=30_000)
        download = pending.value
        if Path(download.suggested_filename).suffix.lower() != ".mp4":
            download.delete()
            raise RuntimeError("Google Flow download did not return an MP4.")

        path = DOWNLOADS_DIR / f"flow_{cycle_id}_{uuid4().hex}.mp4"
        download.save_as(path)
        if not path.stat().st_size:
            path.unlink()
            raise RuntimeError("Google Flow downloaded an empty MP4.")
        return path

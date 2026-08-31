"""
Step 2 (Alternative/Enhanced): Short Video Maker API Handler.
Connects directly to local/remote short-video-maker REST API (Kokoro TTS + Whisper captions + Pexels b-roll + Remotion).
"""
import os
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import (
    SHORT_VIDEO_MAKER_URL,
    DOWNLOADS_DIR,
    SHORT_VIDEO_VOICE,
    SHORT_VIDEO_MUSIC,
    SHORT_VIDEO_ORIENTATION,
    SHORT_VIDEO_CAPTION_POS,
    SHORT_VIDEO_CAPTION_BG,
)
from utils.logger import log_info, log_success, log_warning, log_error

class ShortVideoMakerHandler:
    """Handles communications with the short-video-maker REST API service."""

    def __init__(self, base_url: str = SHORT_VIDEO_MAKER_URL):
        self.base_url = base_url.rstrip("/")

    def is_service_ready(self, timeout_seconds: int = 5) -> bool:
        """Checks if the short-video-maker server is running and healthy."""
        try:
            res = requests.get(f"{self.base_url}/health", timeout=timeout_seconds)
            return res.status_code == 200 and res.json().get("status") == "ok"
        except Exception:
            return False

    def get_available_custom_assets(self) -> Dict[str, List[str]]:
        """Fetches list of custom video clips, screenshots, and music from the server."""
        try:
            res = requests.get(f"{self.base_url}/api/custom-assets", timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return {"videos": [], "images": [], "music": []}

    def create_video(
        self,
        scenes: List[Dict[str, Any]],
        voice: Optional[str] = None,
        music: Optional[str] = None,
        orientation: Optional[str] = None,
        caption_position: Optional[str] = None,
        caption_bg_color: Optional[str] = None,
        padding_back_ms: int = 1500,
        music_volume: str = "medium"
    ) -> str:
        """
        Sends video creation request to POST /api/short-video.
        Returns the created videoId.
        """
        payload = {
            "scenes": scenes,
            "config": {
                "voice": voice or SHORT_VIDEO_VOICE,
                "music": music or SHORT_VIDEO_MUSIC,
                "orientation": orientation or SHORT_VIDEO_ORIENTATION,
                "captionPosition": caption_position or SHORT_VIDEO_CAPTION_POS,
                "captionBackgroundColor": caption_bg_color or SHORT_VIDEO_CAPTION_BG,
                "paddingBack": padding_back_ms,
                "musicVolume": music_volume
            }
        }

        log_info(f"[ShortVideoMaker] Submitting video creation request ({len(scenes)} scenes)...")
        res = requests.post(
            f"{self.base_url}/api/short-video",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if res.status_code not in (200, 201):
            raise RuntimeError(f"ShortVideoMaker API error ({res.status_code}): {res.text}")

        data = res.json()
        video_id = data.get("videoId")
        if not video_id:
            raise RuntimeError(f"Invalid API response, missing videoId: {data}")

        log_success(f"[ShortVideoMaker] Video job enqueued successfully. Job ID: {video_id}")
        return video_id

    def wait_for_completion(
        self,
        video_id: str,
        timeout_seconds: int = 360,
        poll_interval: int = 4
    ) -> bool:
        """
        Polls GET /api/short-video/{videoId}/status until status is 'ready' or 'failed'.
        """
        log_info(f"[ShortVideoMaker] Waiting for video render [{video_id}] to finish (Timeout: {timeout_seconds}s)...")
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                res = requests.get(f"{self.base_url}/api/short-video/{video_id}/status", timeout=10)
                if res.status_code == 200:
                    status_info = res.json()
                    status = status_info.get("status")

                    if status == "ready":
                        elapsed = round(time.time() - start_time, 1)
                        log_success(f"[ShortVideoMaker] Video [{video_id}] rendered successfully in {elapsed}s!")
                        return True
                    elif status == "failed":
                        log_error(f"[ShortVideoMaker] Video rendering failed on server: {status_info}")
                        return False
                    else:
                        elapsed = int(time.time() - start_time)
                        log_info(f"[ShortVideoMaker] Status: {status}... ({elapsed}s elapsed)")
                else:
                    log_warning(f"[ShortVideoMaker] Non-200 status check response: {res.status_code}")
            except Exception as e:
                log_warning(f"[ShortVideoMaker] Polling warning: {e}")

            time.sleep(poll_interval)

        log_error(f"[ShortVideoMaker] Timed out waiting for video [{video_id}] render after {timeout_seconds}s.")
        return False

    def download_video(self, video_id: str, cycle_id: int = 1) -> Path:
        """
        Downloads the rendered MP4 file from GET /api/short-video/{videoId} and saves to downloads directory.
        """
        timestamp = int(time.time())
        dest_file = DOWNLOADS_DIR / f"website_short_{cycle_id}_{video_id[:8]}_{timestamp}.mp4"

        log_info(f"[ShortVideoMaker] Downloading rendered video to: {dest_file.name}...")
        res = requests.get(f"{self.base_url}/api/short-video/{video_id}", stream=True, timeout=60)

        if res.status_code != 200:
            raise RuntimeError(f"Failed to download video ({res.status_code}): {res.text}")

        with open(dest_file, "wb") as f:
            for chunk in res.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)

        if not dest_file.exists() or dest_file.stat().st_size == 0:
            raise RuntimeError("Downloaded video file is empty or missing.")

        size_mb = round(dest_file.stat().st_size / (1024 * 1024), 2)
        log_success(f"[ShortVideoMaker] Download complete! File size: {size_mb} MB -> {dest_file}")
        return dest_file

    def generate_and_download(
        self,
        scenes: List[Dict[str, Any]],
        cycle_id: int = 1,
        timeout_seconds: int = 360,
        **render_kwargs
    ) -> Path:
        """
        Complete end-to-end wrapper: Submits job, waits for render, downloads finished MP4.
        """
        if not self.is_service_ready():
            raise ConnectionError(
                f"Short Video Maker service is not responding at {self.base_url}. "
                "Please start the service (e.g., via Docker or npm start) before running the pipeline."
            )

        video_id = self.create_video(scenes, **render_kwargs)
        ready = self.wait_for_completion(video_id, timeout_seconds=timeout_seconds)
        if not ready:
            raise RuntimeError(f"Video generation failed or timed out for job ID: {video_id}")

        return self.download_video(video_id, cycle_id=cycle_id)

#!/usr/bin/env python3
"""
Batch Video Generator: Creates 5 unique promotional short videos for WebResume.live
using uploaded custom videos and template screenshot assets.
"""
import time
from pathlib import Path
from typing import List, Dict, Any

from short_video_maker_handler import ShortVideoMakerHandler
import config
from utils.logger import log_info, log_success, log_warning, log_error, print_banner

VIDEOS_CONFIG = [
    {
        "id": 1,
        "title": "Developer & Tech Theme",
        "voice": "af_heart",
        "music": "chill",
        "scenes": [
            {
                "text": "Still applying for top jobs with a boring PDF resume from 2015?",
                "asset": "Laptop_displaying_resume_templates_202608242030.mp4"
            },
            {
                "text": "WebResume live transforms your CV into an interactive AI portfolio recruiters actually love.",
                "asset": "065-terminal.png"
            },
            {
                "text": "Choose from 148 modern layouts and get hired faster. Link in bio!",
                "asset": "148-classic-1.png"
            }
        ]
    },
    {
        "id": 2,
        "title": "Speed & Automation Theme",
        "voice": "am_adam",
        "music": "happy",
        "scenes": [
            {
                "text": "Why waste hours formatting a resume when AI can build your website in seconds?",
                "asset": "Continuing_the_same_woman_now.mp4"
            },
            {
                "text": "WebResume creates a stunning personal website with tailored AI cover letters on autopilot.",
                "asset": "071-atelier.png"
            },
            {
                "text": "Claim your 7-day free trial at WebResume live and stand out today!",
                "asset": "live_olacak_sonunda_birde_bir.mp4"
            }
        ]
    },
    {
        "id": 3,
        "title": "Recruiter Attention Theme",
        "voice": "af_bella",
        "music": "hopeful",
        "scenes": [
            {
                "text": "Recruiters spend only six seconds on traditional CVs. Give them something unforgettable.",
                "asset": "bu_kadın_iş_başvurusu_yapmış_v.mp4"
            },
            {
                "text": "Turn your career into an interactive web experience with 148 dynamic themes.",
                "asset": "bir_sürü_resume_yan_yana_geçsi.mp4"
            },
            {
                "text": "Try WebResume live for free and level up your career opportunities instantly.",
                "asset": "güzel_bir_resume_yap_sevinsin.mp4"
            }
        ]
    },
    {
        "id": 4,
        "title": "Remote Job & Career Theme",
        "voice": "am_michael",
        "music": "chill",
        "scenes": [
            {
                "text": "Landing a high paying remote job starts with a portfolio that grabs instant attention.",
                "asset": "A_young_Malaysian_woman_wearin.mp4"
            },
            {
                "text": "WebResume gives you dynamic interactive links, modern styles, and AI cover letters.",
                "asset": "087-workspace.png"
            },
            {
                "text": "Start building your interactive website resume right now at WebResume live!",
                "asset": "Vertical_aspect_ratio_HD.mp4"
            }
        ]
    },
    {
        "id": 5,
        "title": "Executive & Minimalist Theme",
        "voice": "af_sky",
        "music": "excited",
        "scenes": [
            {
                "text": "Stop getting ghosted by companies. Upgrade to a modern AI web resume.",
                "asset": "güzel_bir_animation_yap_ve_sad.mp4"
            },
            {
                "text": "Choose from 148 executive layouts with instant AI cover letter generation.",
                "asset": "145-classic-4.png"
            },
            {
                "text": "Unlock your dream job with a 7-day free trial at WebResume live!",
                "asset": "138-richard-sanchez-resume.png"
            }
        ]
    }
]

def main():
    print_banner(
        title="🎬 BATCH PRODUCTION: 5 CUSTOM AI VIDEOS FOR WEBRESUME.LIVE",
        subtitle="Engine: Custom Video Clips + Template Screenshots + Kokoro Voice + Whisper Subtitles"
    )

    handler = ShortVideoMakerHandler(config.SHORT_VIDEO_MAKER_URL)
    if not handler.is_service_ready():
        log_error(f"Service not running at {config.SHORT_VIDEO_MAKER_URL}. Please start ./start_short_video_server.sh")
        return

    available_assets = handler.get_available_custom_assets()
    log_success(f"Loaded {len(available_assets.get('videos', []))} Custom Videos & {len(available_assets.get('images', []))} Custom Screenshots.")

    generated_videos: List[Path] = []
    total_start = time.time()

    for item in VIDEOS_CONFIG:
        vid = item["id"]
        title = item["title"]
        voice = item["voice"]
        music = item["music"]
        scenes = item["scenes"]

        log_info("\n" + "=" * 65)
        log_info(f"🚀 GENERATING VIDEO [{vid}/5] - {title}")
        log_info(f"🎙️ Voice: {voice} | 🎵 Music: {music}")
        for idx, sc in enumerate(scenes, 1):
            log_info(f"   Scene {idx}: \"{sc['text'][:45]}...\" | Asset: {sc.get('asset')}")
        log_info("=" * 65)

        try:
            video_path = handler.generate_and_download(
                scenes=scenes,
                cycle_id=vid,
                voice=voice,
                music=music,
                orientation="portrait",
                caption_position="bottom",
                caption_bg_color="blue"
            )
            generated_videos.append(video_path)
            log_success(f"✅ Video [{vid}/5] Finished: {video_path.name}")
        except Exception as e:
            log_error(f"❌ Failed to generate Video [{vid}/5]: {e}")

        # Brief cooldown between jobs
        if vid < len(VIDEOS_CONFIG):
            time.sleep(3)

    total_time = round(time.time() - total_start, 1)
    log_info("\n" + "=" * 65)
    log_success(f"🎉 ALL 5 VIDEOS GENERATED SUCCESSFULLY IN {total_time}s!")
    log_info("=" * 65)
    for idx, vpath in enumerate(generated_videos, 1):
        size_mb = round(vpath.stat().st_size / (1024 * 1024), 2)
        log_info(f"  {idx}. [{size_mb} MB] {vpath.name}")
    log_info(f"\n📁 Directory: {config.DOWNLOADS_DIR}")

if __name__ == "__main__":
    main()

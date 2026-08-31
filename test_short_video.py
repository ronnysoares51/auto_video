#!/usr/bin/env python3
"""
Test script to generate a sample promotional video for your website using short-video-maker.
"""
import time
from pathlib import Path
from short_video_maker_handler import ShortVideoMakerHandler
import config

def main():
    print("🎬 Testing Short Video Maker API for Website Marketing Video...")
    handler = ShortVideoMakerHandler(config.SHORT_VIDEO_MAKER_URL)

    if not handler.is_service_ready():
        print(f"❌ Error: Service is not reachable at {config.SHORT_VIDEO_MAKER_URL}")
        print("Please start the server first: ./start_short_video_server.sh")
        return

    print("✅ Service is ONLINE!")

    # Check and list available custom assets
    assets = handler.get_available_custom_assets()
    print(f"\n📂 Custom Assets Available in custom_assets/:")
    print(f"   • Videos: {assets.get('videos', []) or 'None (using Pexels)'}")
    print(f"   • Images: {assets.get('images', []) or 'None (using Pexels)'}")
    print(f"   • Music:  {assets.get('music', []) or 'Default tracks'}")
    sample_scenes = [
        {
            "text": f"Are you still submitting boring paper resumes in {time.strftime('%Y')}?",
            "searchTerms": ["resume", "job interview", "frustrated person"]
        },
        {
            "text": f"Meet {config.TARGET_WEBSITE_NAME}! Create a stunning, interactive AI website portfolio in minutes.",
            "searchTerms": ["coding laptop", "modern website", "futuristic technology"]
        },
        {
            "text": f"Choose from 148 templates and start your 7-day free trial at {config.TARGET_WEBSITE_NAME}!",
            "searchTerms": ["success", "happy person", "working remotely"]
        }
    ]

    print("\n📝 Submitting scenes for rendering:")
    for i, s in enumerate(sample_scenes, 1):
        print(f"  Scene {i}: {s['text']} | Keywords: {s['searchTerms']}")

    video_path = handler.generate_and_download(
        scenes=sample_scenes,
        cycle_id=999,
        voice=config.SHORT_VIDEO_VOICE,
        music=config.SHORT_VIDEO_MUSIC,
        orientation="portrait",
        caption_position="bottom",
        caption_bg_color="blue"
    )

    print(f"\n🎉 Video generated and saved successfully at:\n👉 {video_path}")

if __name__ == "__main__":
    main()

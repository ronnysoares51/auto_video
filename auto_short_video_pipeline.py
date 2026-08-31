#!/usr/bin/env python3
"""
================================================================================
Autonomous Storytelling Marketing Video Pipeline (Malaysian Demographic Focus)
Architecture:
  1. Prompt Splitting & Storytelling: Gemini AI creates a 5 to 6 scene story.
  2. Strict Demographic Targeting: Explicitly features Malaysian actors & urban settings.
  3. Multi-Video Generation Loop: Renders 5-6 individual HD scene clips.
  4. MoviePy Merging with Transitions: Stitches scenes with smooth crossfades into
     a master story video and publishes to TikTok Creator Center.
================================================================================
"""
import sys
import time
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import config
from utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    print_banner,
    print_summary_table
)
from utils.browser_manager import BrowserManager
from utils.popup_handler import handle_unexpected_popups
from utils.video_merger import merge_scene_clips_with_transitions
from gemini_handler import GeminiHandler
from short_video_maker_handler import ShortVideoMakerHandler
from tiktok_handler import TikTokHandler
from notifier import send_telegram_alert

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Autonomous 5-6 Scene Story Video Creator with Malaysian Demographic Targeting & MoviePy Transitions"
    )
    parser.add_argument("--cycles", type=int, default=config.LOOP_COUNT, help="Number of story videos to generate and publish.")
    parser.add_argument("--skip-tiktok", action="store_true", default=False, help="Generate and merge story videos locally without TikTok upload.")
    parser.add_argument("--headless", action="store_true", default=False, help="Run browser in headless mode.")
    parser.add_argument("--voice", type=str, default=config.SHORT_VIDEO_VOICE, help="TTS voice (e.g. af_heart, am_adam).")
    parser.add_argument("--music", type=str, default=config.SHORT_VIDEO_MUSIC, help="Background music mood (e.g. chill, happy, hopeful).")
    parser.add_argument("--website-name", type=str, default=config.TARGET_WEBSITE_NAME, help="Website brand name.")
    parser.add_argument("--website-url", type=str, default=config.TARGET_WEBSITE_URL, help="Website URL.")
    parser.add_argument("--transition-duration", type=float, default=0.35, help="Crossfade transition duration between scenes (in seconds).")
    return parser.parse_args()

def run_marketing_pipeline():
    args = parse_arguments()
    start_time = time.time()
    success_count = 0
    fail_count = 0

    print_banner(
        title=f"🎬 5-SCENE STORYTELLING VIDEO PIPELINE: {args.website_name.upper()}",
        subtitle=f"Target: {args.cycles} Stories | Demographic: Malaysia | Transitions: MoviePy Crossfade"
    )

    # 1. Check Short Video Maker service health
    video_maker = ShortVideoMakerHandler(config.SHORT_VIDEO_MAKER_URL)
    log_info(f"Checking Short Video Maker connection at {config.SHORT_VIDEO_MAKER_URL}...")
    if not video_maker.is_service_ready():
        log_error(
            f"❌ Short Video Maker server is NOT running at {config.SHORT_VIDEO_MAKER_URL}.\n"
            "   Please start it using: ./start_short_video_server.sh"
        )
        sys.exit(1)

    available_assets = video_maker.get_available_custom_assets()
    log_success(
        f"✅ Short Video Maker is ONLINE. Loaded {len(available_assets.get('videos', []))} Custom Videos "
        f"and {len(available_assets.get('images', []))} Template Screenshots."
    )

    # 2. Launch browser for Gemini (and TikTok if enabled)
    browser_mgr = BrowserManager()
    context, page = browser_mgr.start()

    gemini = GeminiHandler(page)
    tiktok = TikTokHandler(page)

    results_summary: List[Dict[str, Any]] = []

    try:
        for cycle_id in range(1, args.cycles + 1):
            log_info("\n" + "=" * 70)
            log_info(f"🚀 STARTING STORY PRODUCTION CYCLE [{cycle_id}/{args.cycles}]")
            log_info(f"🎯 Target Audience: Malaysian Job Seekers & Professionals")
            log_info(f"🌐 Product: {args.website_name} ({args.website_url})")
            log_info("=" * 70 + "\n")

            cycle_data = {
                "task_id": f"Story-{cycle_id}",
                "prompt": "N/A",
                "gen_status": "❌ Failed",
                "upload_status": "⏭️ Skipped",
                "final_status": "FAILED"
            }

            # ------------------------------------------------------------------
            # STEP 1: Prompt Splitting & Malaysian Story Script Generation
            # ------------------------------------------------------------------
            script_data = None
            for attempt in range(1, config.MAX_RETRIES_PER_STEP + 1):
                try:
                    log_info(f"[Step 1] Directing 5-6 Scene Malaysian Story Script (Attempt {attempt}/{config.MAX_RETRIES_PER_STEP})...")
                    script_data = gemini.generate_malaysian_story_script(cycle_id=cycle_id)
                    if script_data and "scenes" in script_data and len(script_data["scenes"]) >= 3:
                        break
                except Exception as e:
                    log_warning(f"[Step 1] Script generation error (Attempt {attempt}): {e}")
                    handle_unexpected_popups(page)
                    page.wait_for_timeout(2000)

            if not script_data or "scenes" not in script_data or len(script_data["scenes"]) == 0:
                log_error(f"Failed to generate valid scenes in Cycle [{cycle_id}]. Skipping cycle.")
                fail_count += 1
                results_summary.append(cycle_data)
                continue

            scenes = script_data["scenes"]
            caption = script_data.get(
                "caption",
                f"Tukar resume PDF biasa jadi dynamic website resume! 🚀 Link in bio. #kerjamalaysia #jobsearchmy #kualalumpur #tech"
            )
            cycle_data["prompt"] = f"[{len(scenes)} Scenes] {scenes[0].get('text', '')[:45]}..."

            log_success(f"[Step 1] Storyboard Directed with {len(scenes)} Cohesive Scenes:")
            for idx, sc in enumerate(scenes, 1):
                log_info(f"   Scene {idx}: \"{sc.get('text', '')}\" | Asset/Keywords: {sc.get('asset') or sc.get('searchTerms')}")
            log_info(f"   Caption: \"{caption}\"")

            # ------------------------------------------------------------------
            # STEP 2 & 3: Multi-Video Generation Loop (Scene-by-Scene)
            # ------------------------------------------------------------------
            scene_clips: List[Path] = []
            log_info(f"\n[Step 2] Rendering {len(scenes)} Individual Scene Clips...")

            for s_idx, scene in enumerate(scenes, 1):
                log_info(f"   🎬 Rendering Scene [{s_idx}/{len(scenes)}]: \"{scene.get('text', '')[:40]}...\"")
                try:
                    # Render individual scene clip
                    scene_file = video_maker.generate_and_download(
                        scenes=[scene],
                        cycle_id=f"c{cycle_id}_sc{s_idx}",
                        voice=args.voice,
                        music=args.music,
                        orientation=config.SHORT_VIDEO_ORIENTATION,
                        caption_position=config.SHORT_VIDEO_CAPTION_POS,
                        caption_bg_color=config.SHORT_VIDEO_CAPTION_BG
                    )
                    if scene_file and scene_file.exists():
                        # Move/organize into SCENES_DIR
                        target_scene_path = config.SCENES_DIR / f"story_{cycle_id}_scene_{s_idx}.mp4"
                        shutil.move(str(scene_file), str(target_scene_path))
                        scene_clips.append(target_scene_path)
                        log_success(f"   ✅ Scene [{s_idx}/{len(scenes)}] Ready: {target_scene_path.name}")
                except Exception as sc_err:
                    log_warning(f"   ⚠️ Scene [{s_idx}] rendering warning: {sc_err}")

            if len(scene_clips) == 0:
                log_error(f"No scene clips were generated for Cycle [{cycle_id}].")
                fail_count += 1
                results_summary.append(cycle_data)
                continue

            # ------------------------------------------------------------------
            # STEP 4: Merging with Smooth Transitions (MoviePy Integration)
            # ------------------------------------------------------------------
            timestamp = int(time.time())
            final_story_path = config.DOWNLOADS_DIR / f"final_malaysian_story_cycle_{cycle_id}_{timestamp}.mp4"
            log_info(f"\n[Step 3] Merging {len(scene_clips)} clips with MoviePy smooth crossfades...")

            try:
                final_video_path = merge_scene_clips_with_transitions(
                    clip_paths=scene_clips,
                    output_path=final_story_path,
                    transition_duration=args.transition_duration
                )
                cycle_data["gen_status"] = f"✅ {len(scene_clips)} Sc Merged"
            except Exception as merge_err:
                log_error(f"MoviePy stitching error: {merge_err}")
                # Fallback to the first generated clip if merging fails
                final_video_path = scene_clips[0]
                cycle_data["gen_status"] = "⚠️ Partial Merge"

            log_success(f"🎉 Master Story Video Generated: {final_video_path.name}")

            # ------------------------------------------------------------------
            # STEP 5: TikTok Creator Center Publishing
            # ------------------------------------------------------------------
            if args.skip_tiktok:
                log_info("[Step 4] --skip-tiktok flag enabled. Skipping TikTok upload.")
                cycle_data["upload_status"] = "⏭️ Skipped (Local Only)"
                cycle_data["final_status"] = "SUCCESS"
                success_count += 1
                results_summary.append(cycle_data)
                continue

            upload_success = False
            for attempt in range(1, config.MAX_RETRIES_PER_STEP + 1):
                try:
                    log_info(f"[Step 4] Uploading Story to TikTok (Attempt {attempt}/{config.MAX_RETRIES_PER_STEP})...")
                    upload_success = tiktok.upload_and_publish(
                        cycle_id=cycle_id,
                        video_path=final_video_path,
                        caption=caption
                    )
                    if upload_success:
                        cycle_data["upload_status"] = "✅ Published"
                        cycle_data["final_status"] = "SUCCESS"
                        success_count += 1
                        break
                except Exception as e:
                    log_warning(f"[Step 4] TikTok upload error (Attempt {attempt}): {e}")
                    handle_unexpected_popups(page)
                    page.wait_for_timeout(3000)

            if not upload_success:
                log_error(f"TikTok upload failed for Cycle [{cycle_id}].")
                fail_count += 1
                cycle_data["upload_status"] = "❌ Failed"
                cycle_data["final_status"] = "PARTIAL (Rendered, not published)"

            results_summary.append(cycle_data)

            if cycle_id < args.cycles:
                log_info("Cooling down for 5 seconds before next story cycle...")
                time.sleep(5)

    except KeyboardInterrupt:
        log_warning("\n⚠️ Automation interrupted by user.")
    except Exception as e:
        log_error(f"Fatal error in automation pipeline: {e}")
    finally:
        browser_mgr.close()

    # Summary & Telegram Reporting
    total_elapsed = round(time.time() - start_time, 2)
    print_summary_table(results_summary)

    runtime_mins = total_elapsed / 60
    send_telegram_alert(
        success_count=success_count,
        fail_count=fail_count,
        runtime_mins=runtime_mins
    )

if __name__ == "__main__":
    run_marketing_pipeline()

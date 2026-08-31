"""
Main Orchestrator for Fully Autonomous 3-Step Video Pipeline.
Loop Workflow (N cycles):
  [Step 1] Gemini Web: Generate viral prompt & TikTok caption (JSON)
  [Step 2] Google Flow Web: Generate AI video & download MP4
  [Step 3] TikTok Web: Upload MP4, type caption & publish

Notification:
  Sends summary report to Telegram at the end of the run.
"""
import sys
import time
from typing import List, Dict, Any

from config import (
    LOOP_COUNT,
    MAX_RETRIES_PER_STEP,
    SCREENSHOTS_DIR
)
from utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    print_banner,
    print_summary_table
)
from utils.popup_handler import handle_unexpected_popups
from utils.browser_manager import BrowserManager
from gemini_handler import GeminiHandler
from flow_handler import FlowHandler
from tiktok_handler import TikTokHandler
from notifier import send_telegram_alert

def run_end_to_end_pipeline():
    """Main execution loop for all cycles."""
    start_time = time.time()
    success_count = 0
    fail_count = 0

    print_banner(
        title="🤖 AUTONOMOUS RPA: GEMINI -> GOOGLE FLOW -> TIKTOK",
        subtitle=f"Target: {LOOP_COUNT} Cycles | 100% Free & API-Less | Ad-Blocker Active"
    )

    # 1. Initialize Persistent Browser Context
    browser_mgr = BrowserManager()
    context, page = browser_mgr.start()

    # 2. Instantiate Step Handlers
    gemini = GeminiHandler(page)
    flow = FlowHandler(page)
    tiktok = TikTokHandler(page)

    results_summary: List[Dict[str, Any]] = []

    try:
        for cycle_id in range(1, LOOP_COUNT + 1):
            log_info("\n" + "=" * 65)
            log_info(f"🎬 STARTING AUTOMATION CYCLE [{cycle_id}/{LOOP_COUNT}]")
            log_info("=" * 65 + "\n")

            cycle_data = {
                "task_id": f"Cycle-{cycle_id}",
                "prompt": "N/A",
                "gen_status": "❌ Failed",
                "upload_status": "⏭️ Skipped",
                "final_status": "FAILED"
            }

            # ------------------------------------------------------------------
            # STEP 1: Gemini Prompt & Caption Generation
            # ------------------------------------------------------------------
            gemini_result = None
            for attempt in range(1, MAX_RETRIES_PER_STEP + 1):
                try:
                    log_info(f"[Step 1] Generating prompt via Gemini (Attempt {attempt}/{MAX_RETRIES_PER_STEP})...")
                    gemini_result = gemini.generate_prompt_and_caption(cycle_id=cycle_id)
                    if gemini_result and "prompt" in gemini_result and "caption" in gemini_result:
                        break
                except Exception as e:
                    log_warning(f"[Step 1] Error during Gemini generation (Attempt {attempt}): {e}")
                    screenshot_path = SCREENSHOTS_DIR / f"err_step1_gemini_c{cycle_id}_att{attempt}.png"
                    try:
                        page.screenshot(path=str(screenshot_path))
                        log_info(f"Diagnostic screenshot saved to: {screenshot_path}")
                    except Exception:
                        pass
                    handle_unexpected_popups(page)
                    page.wait_for_timeout(2000)

            if not gemini_result:
                log_error(f"Failed to obtain prompt from Gemini in Cycle [{cycle_id}]. Skipping cycle.")
                fail_count += 1
                results_summary.append(cycle_data)
                continue

            prompt_text = gemini_result["prompt"]
            caption_text = gemini_result["caption"]
            cycle_data["prompt"] = prompt_text

            # ------------------------------------------------------------------
            # STEP 2: Google Flow Video Generation & Download
            # ------------------------------------------------------------------
            video_file = None
            for attempt in range(1, MAX_RETRIES_PER_STEP + 1):
                try:
                    log_info(f"[Step 2] Generating video on Google Flow (Attempt {attempt}/{MAX_RETRIES_PER_STEP})...")
                    video_file = flow.generate_video(cycle_id=cycle_id, prompt=prompt_text)
                    if video_file and video_file.exists():
                        cycle_data["gen_status"] = "✅ Done"
                        break
                except Exception as e:
                    log_warning(f"[Step 2] Error during Flow video generation (Attempt {attempt}): {e}")
                    screenshot_path = SCREENSHOTS_DIR / f"err_step2_flow_c{cycle_id}_att{attempt}.png"
                    try:
                        page.screenshot(path=str(screenshot_path))
                        log_info(f"Diagnostic screenshot saved to: {screenshot_path}")
                    except Exception:
                        pass
                    handle_unexpected_popups(page)
                    page.wait_for_timeout(3000)

            if not video_file or not video_file.exists():
                log_error(f"Failed to generate video in Cycle [{cycle_id}]. Skipping TikTok upload.")
                fail_count += 1
                results_summary.append(cycle_data)
                continue

            # ------------------------------------------------------------------
            # STEP 3: TikTok Video Upload & Publishing
            # ------------------------------------------------------------------
            upload_success = False
            for attempt in range(1, MAX_RETRIES_PER_STEP + 1):
                try:
                    log_info(f"[Step 3] Uploading to TikTok (Attempt {attempt}/{MAX_RETRIES_PER_STEP})...")
                    upload_success = tiktok.upload_and_publish(
                        cycle_id=cycle_id,
                        video_path=video_file,
                        caption=caption_text
                    )
                    if upload_success:
                        cycle_data["upload_status"] = "✅ Posted"
                        break
                except Exception as e:
                    log_warning(f"[Step 3] Error during TikTok upload (Attempt {attempt}): {e}")
                    screenshot_path = SCREENSHOTS_DIR / f"err_step3_tiktok_c{cycle_id}_att{attempt}.png"
                    try:
                        page.screenshot(path=str(screenshot_path))
                        log_info(f"Diagnostic screenshot saved to: {screenshot_path}")
                    except Exception:
                        pass
                    handle_unexpected_popups(page)
                    page.wait_for_timeout(3000)

            if upload_success:
                success_count += 1
                cycle_data["final_status"] = "SUCCESS"
                log_success(f"🎉 Cycle [{cycle_id}/{LOOP_COUNT}] completed successfully!")
            else:
                fail_count += 1
                cycle_data["final_status"] = "PARTIAL"
                log_warning(f"⚠️  Cycle [{cycle_id}/{LOOP_COUNT}] finished with partial upload status.")

            results_summary.append(cycle_data)
            time.sleep(3)

    except KeyboardInterrupt:
        log_warning("\nPipeline paused/interrupted by user (Ctrl+C). Exiting safely...")
    finally:
        print_summary_table(results_summary)
        browser_mgr.close()

        # Calculate total runtime and send Telegram notification
        end_time = time.time()
        runtime_mins = (end_time - start_time) / 60
        send_telegram_alert(
            success_count=success_count,
            fail_count=fail_count,
            runtime_mins=runtime_mins
        )

        log_info("Pipeline execution closed cleanly.")

if __name__ == "__main__":
    run_end_to_end_pipeline()

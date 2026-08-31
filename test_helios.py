#!/usr/bin/env python3
"""
Test script to generate a sample video using Helios AI Video Generator on Mac / MPS.
"""
import time
from pathlib import Path
from helios_handler import HeliosVideoGenerator
from utils.logger import log_info, log_success, log_error, print_banner

def main():
    print_banner(
        title="🎬 TESTING HELIOS AI VIDEO GENERATOR",
        subtitle="Model: PKU-YuanGroup/Helios | Target: Text-to-Video Generation"
    )

    output_dir = Path(__file__).parent / "downloads"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"helios_test_video_{int(time.time())}.mp4"

    log_info("Initializing Helios generator...")
    
    try:
        generator = HeliosVideoGenerator(
            model_id_or_path="BestWishYsh/Helios-Distilled",
            dtype="float16",
            enable_cpu_offload=True,
            enable_vae_optimization=True
        )

        test_prompt = (
            "A confident young Malaysian professional woman smiling and working on an interactive "
            "AI website on a modern laptop in a bright Kuala Lumpur office, cinematic lighting, photorealistic 4k"
        )

        log_info(f"Submitting prompt:\n👉 \"{test_prompt}\"\n")
        log_info("Generating video frames (this may take a couple minutes on first run)...")

        video_path = generator.generate_video(
            prompt=test_prompt,
            num_frames=33,         # ~1.5 - 2 seconds of high quality video
            height=512,            # Resolution optimized for local inference
            width=384,             # 9:16 vertical short format
            num_inference_steps=25,
            guidance_scale=6.0,
            fps=24,
            output_path=output_file
        )

        log_success(f"\n🎉 Video generated successfully!")
        log_info(f"📁 Output file saved at:\n👉 {video_path}")

    except Exception as e:
        log_error(f"Helios generation encountered an error: {e}")

if __name__ == "__main__":
    main()

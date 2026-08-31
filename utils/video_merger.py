"""
Video Stitching & Transition Module using MoviePy v2.
Merges multiple scene video clips into a single cohesive story with smooth transitions.
"""
import os
import sys
from pathlib import Path
from typing import List, Optional

try:
    from moviepy import VideoFileClip, concatenate_videoclips, vfx, CompositeVideoClip
except ImportError:
    from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx, CompositeVideoClip

from utils.logger import log_info, log_success, log_warning, log_error

def merge_scene_clips_with_transitions(
    clip_paths: List[Path],
    output_path: Path,
    transition_duration: float = 0.4,
    fps: int = 30
) -> Path:
    """
    Stitches 5 to 6 individual scene clips into a seamless story video.
    Applies crossfade transitions between scene cuts so the transition is fluid and cinematic.
    """
    if not clip_paths:
        raise ValueError("No video clips provided to merge.")

    valid_paths = [p for p in clip_paths if p.exists() and p.stat().st_size > 0]
    if not valid_paths:
        raise FileNotFoundError("None of the provided clip paths exist or have data.")

    if len(valid_paths) == 1:
        # Only one clip, copy or return directly
        import shutil
        shutil.copy(valid_paths[0], output_path)
        return output_path

    log_info(f"[VideoMerger] Stitching {len(valid_paths)} scenes into master video...")
    clips = []

    try:
        for idx, cp in enumerate(valid_paths):
            log_info(f"   🎬 Loading Scene {idx + 1}: {cp.name}")
            c = VideoFileClip(str(cp))
            
            # Ensure standard vertical 1080x1920 portrait dimensions
            if c.size != (1080, 1920):
                try:
                    c = c.resized((1080, 1920))
                except Exception:
                    pass

            # Apply smooth Fade-In / Fade-Out effects for cinematic blending
            try:
                # MoviePy v2 effect syntax
                if hasattr(vfx, "CrossFadeIn") and idx > 0:
                    c = c.with_effects([vfx.CrossFadeIn(transition_duration)])
                elif hasattr(c, "crossfadein") and idx > 0:
                    c = c.crossfadein(transition_duration)
            except Exception:
                pass

            clips.append(c)

        # Concatenate clips with compose method
        log_info("[VideoMerger] Rendering seamless composite video...")
        try:
            final_clip = concatenate_videoclips(
                clips,
                method="compose",
                padding=-transition_duration
            )
        except Exception:
            # Fallback to standard concatenation if overlap fails
            final_clip = concatenate_videoclips(clips, method="compose")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        final_clip.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            fps=fps,
            preset="fast",
            threads=4,
            logger=None # Suppress raw moviepy output for clean logs
        )

        log_success(f"[VideoMerger] Master Story Video saved successfully at: {output_path.name}")
        return output_path

    finally:
        # Always close clips to free system resources and file descriptors
        for c in clips:
            try:
                c.close()
            except Exception:
                pass

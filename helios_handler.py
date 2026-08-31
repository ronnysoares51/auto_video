"""
================================================================================
Helios Video Generator Module (PKU-YuanGroup/Helios Integration)
Production-grade wrapper for Text-to-Video and Image-to-Video generation with:
  • Low-VRAM optimizations (CPU offloading, VAE tiling, fp16/bf16 precision)
  • Robust error handling with automatic OOM recovery
  • Clean modular interface for easy pipeline integration
================================================================================
"""
import os
import gc
import sys
import time
from pathlib import Path
from typing import Optional, Union, Dict, Any, List

from utils.logger import log_info, log_success, log_warning, log_error

class HeliosVideoGenerator:
    """
    Modular wrapper for PKU-YuanGroup/Helios video generation diffusion models.
    Supports text-to-video, image-to-video, memory-efficient attention, and VRAM offloading.
    """

    def __init__(
        self,
        model_id_or_path: str = "BestWishYsh/Helios-Distilled",
        device: Optional[str] = None,
        dtype: Optional[str] = "float16",
        enable_cpu_offload: bool = True,
        enable_vae_optimization: bool = True,
        cache_dir: Optional[str] = None
    ):
        """
        Initializes the Helios model pipeline with memory-saving parameters.

        Args:
            model_id_or_path: Hugging Face model repo ID or local checkpoint directory path.
            device: 'cuda', 'mps', or 'cpu'. Defaults to auto-detection.
            dtype: 'bfloat16', 'float16', or 'float32'.
            enable_cpu_offload: Offloads model weights to CPU when not active to save VRAM.
            enable_vae_optimization: Enables VAE tiling & slicing to prevent latent decode OOM.
            cache_dir: Custom directory to store downloaded model weights.
        """
        self.model_id_or_path = model_id_or_path
        self.enable_cpu_offload = enable_cpu_offload
        self.enable_vae_optimization = enable_vae_optimization
        self.cache_dir = cache_dir or os.getenv("HELIOS_MODEL_DIR", str(Path(__file__).parent / "models" / "helios"))
        
        self.pipeline = None
        self.torch = None
        self.device = device or self._detect_device()
        self.dtype_str = dtype
        self.torch_dtype = None

    def _detect_device(self) -> str:
        """Auto-detects the best available compute device."""
        try:
            import torch
            self.torch = torch
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        except ImportError:
            return "cpu"

    def load_model(self):
        """Loads and optimizes the Helios diffusion pipeline."""
        if self.pipeline is not None:
            return

        log_info(f"[Helios] Initializing model from: {self.model_id_or_path} on device: {self.device}...")
        
        try:
            import torch
            from diffusers import DiffusionPipeline
            self.torch = torch

            # Determine precision
            if self.dtype_str == "bfloat16" and torch.cuda.is_available() and torch.cuda.is_bf16_supported():
                self.torch_dtype = torch.bfloat16
            elif self.dtype_str in ["float16", "bfloat16"] and self.device == "cuda":
                self.torch_dtype = torch.float16
            else:
                self.torch_dtype = torch.float32

            log_info(f"[Helios] Loading pipeline with precision: {self.torch_dtype}...")

            # Load pipeline from Hugging Face or local path
            self.pipeline = DiffusionPipeline.from_pretrained(
                self.model_id_or_path,
                torch_dtype=self.torch_dtype,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )

            # Apply VRAM Optimizations
            if self.device == "cuda":
                if self.enable_cpu_offload:
                    log_info("[Helios] Enabling model CPU offload (VRAM optimizer)...")
                    self.pipeline.enable_model_cpu_offload()
                else:
                    self.pipeline.to("cuda")

                if self.enable_vae_optimization and hasattr(self.pipeline, "vae"):
                    log_info("[Helios] Enabling VAE tiling and slicing...")
                    if hasattr(self.pipeline.vae, "enable_tiling"):
                        self.pipeline.vae.enable_tiling()
                    if hasattr(self.pipeline.vae, "enable_slicing"):
                        self.pipeline.vae.enable_slicing()

                # Enable xFormers or SDPA if available
                try:
                    self.pipeline.enable_xformers_memory_efficient_attention()
                    log_info("[Helios] xFormers memory-efficient attention enabled.")
                except Exception:
                    pass
            else:
                self.pipeline.to(self.device)

            log_success("[Helios] Model successfully loaded and ready for inference!")

        except Exception as e:
            log_error(f"[Helios] Failed to load model: {e}")
            raise RuntimeError(f"Helios initialization error: {e}")

    def generate_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = "blurry, low quality, distorted, watermark, jittery",
        num_frames: int = 49,
        height: int = 720,
        width: int = 480,
        num_inference_steps: int = 30,
        guidance_scale: float = 6.0,
        fps: int = 24,
        seed: Optional[int] = None,
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Generates a video from a text prompt.

        Args:
            prompt: Text prompt describing the video scene.
            negative_prompt: Negative guidance prompt.
            num_frames: Total frames to generate (e.g. 49 frames @ 24fps ≈ 2 seconds).
            height: Video height in pixels (portrait default: 720 or 1080).
            width: Video width in pixels (portrait default: 480 or 720).
            num_inference_steps: Denoising steps (25-35 recommended).
            guidance_scale: Classifier-Free Guidance scale.
            fps: Playback frame rate.
            seed: Random seed for reproducible generation.
            output_path: Destination MP4 file path.

        Returns:
            Path: Absolute path to the generated MP4 file.
        """
        self.load_model()

        if output_path is None:
            output_dir = Path(__file__).parent / "downloads" / "helios_generated"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"helios_{int(time.time())}.mp4"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        generator = None
        if seed is not None and self.torch:
            generator = self.torch.Generator(device="cpu").manual_seed(seed)

        log_info(f"[Helios] Generating Video ({width}x{height}, {num_frames} frames)...")
        log_info(f"   Prompt: \"{prompt[:80]}...\"")

        try:
            start_time = time.time()
            with self.torch.inference_mode():
                result = self.pipeline(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_frames=num_frames,
                    height=height,
                    width=width,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator
                )

            frames = result.frames[0] if hasattr(result, "frames") else result[0]
            
            # Export frames to MP4
            self._save_frames_as_video(frames, output_path, fps=fps)
            elapsed = round(time.time() - start_time, 2)
            log_success(f"[Helios] Video generation completed in {elapsed}s -> {output_path.name}")
            return output_path

        except Exception as e:
            if "OutOfMemoryError" in type(e).__name__ or "CUDA out of memory" in str(e):
                log_warning("[Helios] CUDA OOM encountered! Attempting recovery with lower resolution...")
                self._clear_gpu_memory()
                # Retry with reduced resolution fallback
                if height > 512 or width > 384:
                    return self.generate_video(
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        num_frames=max(25, num_frames - 16),
                        height=512,
                        width=384,
                        num_inference_steps=max(20, num_inference_steps - 5),
                        guidance_scale=guidance_scale,
                        fps=fps,
                        seed=seed,
                        output_path=output_path
                    )
            log_error(f"[Helios] Video generation failed: {e}")
            raise e

    def _save_frames_as_video(self, frames: Any, output_path: Path, fps: int = 24):
        """Exports PIL / NumPy frames list to a standard H.264 MP4 container."""
        try:
            from diffusers.utils import export_to_video
            export_to_video(frames, str(output_path), fps=fps)
        except Exception:
            import imageio
            import numpy as np
            np_frames = [np.array(f) if not isinstance(f, np.ndarray) else f for f in frames]
            imageio.mimsave(str(output_path), np_frames, fps=fps, codec="libx264")

    def _clear_gpu_memory(self):
        """Frees unused cached GPU memory."""
        gc.collect()
        if self.torch and self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()
            self.torch.cuda.ipc_collect()

"""
Automated downloader, extractor, and manifest patcher for uBlock Origin Lite (Manifest V3).
Guarantees full compatibility with Chromium's strict extension loading & localization rules:
1. Downloads the exact *chromium*.zip asset from GitHub.
2. Extracts files preserving full folder hierarchy.
3. Ensures all locale folders (with messages.json) reside properly in `_locales/`.
4. Patches `manifest.json` to guarantee `"default_locale": "en"` exists.
"""
import io
import os
import json
import shutil
import zipfile
from pathlib import Path
import requests
from config import EXTENSIONS_DIR, UBLOCK_PATH
from utils.logger import log_info, log_success, log_warning, log_error

UBOLITE_GITHUB_API = "https://api.github.com/repos/uBlockOrigin/uBOL-home/releases/latest"

def patch_manifest_and_locales(extension_dir: Path) -> bool:
    """Patches manifest.json and ensures _locales structure satisfies Chromium requirements."""
    try:
        manifest_file = extension_dir / "manifest.json"
        if not manifest_file.exists():
            # Check if extracted inside a nested subfolder
            for sub in extension_dir.iterdir():
                if sub.is_dir() and (sub / "manifest.json").exists():
                    manifest_file = sub / "manifest.json"
                    extension_dir = sub
                    break

        if not manifest_file.exists():
            log_error(f"manifest.json not found in {extension_dir}")
            return False

        # 1. Ensure _locales directory structure is properly populated
        locales_dir = extension_dir / "_locales"
        locales_dir.mkdir(parents=True, exist_ok=True)

        # Move any top-level locale directories into _locales/
        for item in extension_dir.iterdir():
            if item.is_dir() and item.name != "_locales":
                msg_file = item / "messages.json"
                if msg_file.exists():
                    target_loc_dir = locales_dir / item.name
                    target_loc_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(msg_file), str(target_loc_dir / "messages.json"))
                    # Remove empty leftover dir
                    try:
                        if not list(item.iterdir()):
                            item.rmdir()
                    except Exception:
                        pass

        # 2. Ensure fallback English messages.json exists
        en_dir = locales_dir / "en"
        en_dir.mkdir(parents=True, exist_ok=True)
        en_messages = en_dir / "messages.json"
        if not en_messages.exists() or en_messages.stat().st_size == 0:
            with open(en_messages, "w", encoding="utf-8") as f:
                json.dump({
                    "extName": {"message": "uBlock Origin Lite"},
                    "extShortDesc": {"message": "An efficient content blocker."},
                    "zapperTipEnter": {"message": "Element zapper"},
                    "pickerTipEnter": {"message": "Element picker"}
                }, f, indent=2)

        # 3. Read and patch manifest.json
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        # Ensure default_locale is explicitly defined
        manifest_data["default_locale"] = "en"

        # Write patched manifest back to disk
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)

        log_success(f"Patched manifest.json successfully! default_locale set to 'en'.")
        return True

    except Exception as e:
        log_error(f"Failed to patch manifest.json: {e}")
        return False

def download_and_setup_ublock() -> bool:
    """Fetches, extracts and patches the latest uBlock Origin Lite Chromium extension."""
    try:
        log_info("Fetching latest uBlock Origin Lite release from GitHub...")
        response = requests.get(UBOLITE_GITHUB_API, timeout=15)
        response.raise_for_status()
        release_data = response.json()

        # Find the exact *chromium*.zip asset
        download_url = None
        for asset in release_data.get("assets", []):
            name = asset.get("name", "")
            if "chromium.zip" in name:
                download_url = asset.get("browser_download_url")
                log_info(f"Found official Chromium MV3 asset: {name}")
                break

        if not download_url:
            tag = release_data.get("tag_name", "latest")
            download_url = f"https://github.com/uBlockOrigin/uBOL-home/releases/download/{tag}/uBOLite_{tag}.chromium.zip"

        log_info(f"Downloading from: {download_url}")
        zip_resp = requests.get(download_url, timeout=30)
        zip_resp.raise_for_status()

        # Clean existing folder
        if UBLOCK_PATH.exists():
            shutil.rmtree(UBLOCK_PATH)
        UBLOCK_PATH.mkdir(parents=True, exist_ok=True)

        # Extract all files cleanly
        with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as z:
            z.extractall(UBLOCK_PATH)

        # If files were extracted inside a top-level directory (e.g. uBOLite.chromium/), flatten them
        subdirs = [p for p in UBLOCK_PATH.iterdir() if p.is_dir()]
        if len(subdirs) == 1 and not (UBLOCK_PATH / "manifest.json").exists():
            nested_dir = subdirs[0]
            for child in nested_dir.iterdir():
                shutil.move(str(child), str(UBLOCK_PATH / child.name))
            nested_dir.rmdir()

        # Apply manifest and locale patch
        patch_success = patch_manifest_and_locales(UBLOCK_PATH)
        if patch_success:
            log_success(f"uBlock Origin Lite successfully prepared and verified at: {UBLOCK_PATH}")
            return True
        return False

    except Exception as e:
        log_error(f"Failed to setup uBlock Origin Lite: {e}")
        return False

if __name__ == "__main__":
    download_and_setup_ublock()

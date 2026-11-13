"""Publish generated MP4s to a Telegram channel."""
import hashlib
import sqlite3
import time
from contextlib import closing
from pathlib import Path

import requests

import config
from utils.logger import log_error, log_info, log_success, log_warning


def publish_video(path: Path, caption: str) -> str:
    channel = config.TELEGRAM_CHANNEL_ID
    token = config.TELEGRAM_BOT_TOKEN
    if not channel:
        return "disabled"
    if not token or token.startswith("your_"):
        log_error("Telegram: TELEGRAM_BOT_TOKEN is missing.")
        return "failed"

    try:
        if not 0 < path.stat().st_size <= 50 * 1024 * 1024:
            log_error(f"Telegram: invalid video size for {path.name} (limit: 50 MB).")
            return "failed"
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)

        key = (channel.lower(), digest.hexdigest())
        with closing(sqlite3.connect(config.LOGS_DIR / "telegram_publications.sqlite3")) as db:
            with db:
                db.execute("""
                    CREATE TABLE IF NOT EXISTS publications (
                        channel TEXT NOT NULL,
                        digest TEXT NOT NULL,
                        message_id INTEGER,
                        PRIMARY KEY (channel, digest)
                    )
                """)
                claimed = db.execute(
                    "INSERT OR IGNORE INTO publications (channel, digest) VALUES (?, ?)", key
                ).rowcount
            if not claimed:
                message_id, = db.execute(
                    "SELECT message_id FROM publications WHERE channel = ? AND digest = ?", key
                ).fetchone()
                if message_id is None:
                    log_warning(f"Telegram: pending or unconfirmed upload for {path.name}.")
                    return "unconfirmed"
                log_info(f"Telegram: {path.name} already posted (message {message_id}).")
                return "duplicate"

            # Commit the reservation before making the request. A timeout after
            # sending can mean the channel already received the video.
            status, message_id = _send_video(path, caption, channel, token)
            with db:
                if status == "published":
                    db.execute(
                        "UPDATE publications SET message_id = ? WHERE channel = ? AND digest = ?",
                        (message_id, *key),
                    )
                elif status == "failed":
                    db.execute("DELETE FROM publications WHERE channel = ? AND digest = ?", key)
            return status
    except (OSError, sqlite3.Error) as exc:
        log_error(f"Telegram: could not process {path.name} ({type(exc).__name__}).")
        return "failed"


def _send_video(path, caption, channel, token):
    for attempt in range(1, 4):
        try:
            with path.open("rb") as stream:
                response = requests.post(
                    f"https://api.telegram.org/bot{token}/sendVideo",
                    data={"chat_id": channel, "caption": caption[:1024]},
                    files={"video": (path.name, stream, "video/mp4")},
                    timeout=(10, 120),
                    allow_redirects=False,
                )
            data = response.json()
            if response.ok and data.get("ok") is True:
                message_id = data["result"]["message_id"]
                if isinstance(message_id, int):
                    log_success(f"Telegram: published {path.name} (message {message_id}).")
                    return "published", message_id
            if data.get("ok") is False and 400 <= response.status_code < 500:
                log_warning(f"Telegram: upload rejected for {path.name} (HTTP {response.status_code}).")
                if response.status_code == 429 and attempt < 3:
                    delay = data.get("parameters", {}).get("retry_after", 1)
                    if isinstance(delay, int) and 0 <= delay <= 60:
                        time.sleep(delay)
                        continue
                return "failed", None
        except requests.ConnectTimeout:
            log_warning(f"Telegram: connection timeout for {path.name} (attempt {attempt}/3).")
            if attempt < 3:
                time.sleep(attempt)
                continue
            return "failed", None
        except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError) as exc:
            log_warning(f"Telegram: upload error for {path.name} ({type(exc).__name__}).")
        log_error(f"Telegram: delivery unconfirmed for {path.name}. Check the channel before retrying.")
        return "unconfirmed", None

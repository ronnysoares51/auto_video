import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from telegram_publisher import publish_video


class TelegramPublisherTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.video = Path(temp.name) / "video.mp4"
        self.video.write_bytes(b"video")
        config_patch = patch("telegram_publisher.config")
        self.config = config_patch.start()
        self.addCleanup(config_patch.stop)
        self.config.LOGS_DIR = Path(temp.name)
        self.config.TELEGRAM_CHANNEL_ID = "@canal"
        self.config.TELEGRAM_BOT_TOKEN = "test-token"
        post_patch = patch("telegram_publisher.requests.post")
        self.post = post_patch.start()
        self.addCleanup(post_patch.stop)
        self.post.return_value = Mock(
            ok=True, status_code=200,
            **{"json.return_value": {"ok": True, "result": {"message_id": 42}}},
        )

    def test_published_content_is_deduplicated_even_if_renamed(self):
        self.assertEqual(publish_video(self.video, "caption"), "published")
        renamed = self.video.rename(self.video.with_name("renamed.mp4"))
        self.assertEqual(publish_video(renamed, "new caption"), "duplicate")
        self.assertEqual(self.post.call_count, 1)
        self.assertEqual(self.post.call_args.kwargs["data"]["chat_id"], "@canal")

    def test_unconfirmed_upload_is_not_repeated(self):
        self.post.side_effect = requests.ReadTimeout()
        self.assertEqual(publish_video(self.video, "caption"), "unconfirmed")
        self.assertEqual(publish_video(self.video, "caption"), "unconfirmed")
        self.assertEqual(self.post.call_count, 1)

    def test_rate_limit_is_retried(self):
        rejected = Mock(ok=False, status_code=429)
        rejected.json.return_value = {"ok": False, "parameters": {"retry_after": 2}}
        self.post.side_effect = [rejected, self.post.return_value]
        with patch("telegram_publisher.time.sleep") as sleep:
            self.assertEqual(publish_video(self.video, "caption"), "published")
        sleep.assert_called_once_with(2)

    def test_rejection_releases_reservation(self):
        rejected = Mock(ok=False, status_code=403)
        rejected.json.return_value = {"ok": False}
        self.post.side_effect = [rejected, self.post.return_value]
        self.assertEqual(publish_video(self.video, "caption"), "failed")
        self.assertEqual(publish_video(self.video, "caption"), "published")

    def test_missing_channel_disables_upload(self):
        self.config.TELEGRAM_CHANNEL_ID = ""
        self.assertEqual(publish_video(self.video, "caption"), "disabled")
        self.post.assert_not_called()

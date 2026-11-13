"""
Lightweight Telegram Notification Module.
Sends end-of-run summary alerts directly to your Telegram via HTTP POST.
"""
import requests
import config
from utils.logger import log_info, log_success, log_warning, log_error

def send_telegram_alert(
    success_count: int = 0,
    fail_count: int = 0,
    runtime_mins: float = 0.0,
    message: str = None
):
    """Sends a formatted summary report to your Telegram chat."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID or config.TELEGRAM_CHAT_ID.startswith("your_"):
        return

    if not message:
        message = (
            f"🤖 WebResume.live Bot Report\n\n"
            f"✅ Successful cycles: {success_count}\n"
            f"❌ Failed: {fail_count}\n"
            f"⏱️ Total Runtime: {runtime_mins:.1f} minutes\n\n"
            f"Daily task completed. Logs saved on the server."
        )

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        log_info("Sending Telegram notification summary...")
        response = requests.post(url, json=payload, timeout=10)
        if response.ok and response.json().get("ok") is True:
            log_success("📲 Telegram report successfully sent to your phone!")
        else:
            log_warning(f"Telegram notification error (HTTP {response.status_code}).")
    except (requests.RequestException, ValueError, AttributeError) as e:
        log_error(f"Telegram notification error ({type(e).__name__}).")

if __name__ == "__main__":
    # Test notification directly
    print("Testing Telegram alert...")
    send_telegram_alert(success_count=1, fail_count=0, runtime_mins=2.5)


# import os
# import requests
# from dotenv import load_dotenv

# load_dotenv()

# BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# def send_telegram_message(text: str):
#     url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

#     payload = {
#         "chat_id": CHAT_ID,
#         "text": text
#     }

#     response = requests.post(url, json=payload)
#     response.raise_for_status()
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram credentials missing")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        print("📨 Telegram response:", r.status_code, r.text)
    except Exception as e:
        print("❌ Telegram send failed:", e)

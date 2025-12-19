import asyncio
import requests
import re
import time
import platform
import psutil
import phonenumbers
from phonenumbers import geocoder
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from datetime import datetime
from collections import deque
import logging

# =========================
# BASIC SETUP
# =========================
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8437087674:AAEEBJDfEkxl0MbA__lsSF4A7qc7UpwzGU4"   # <-- yahan apna token lagana

GROUP_IDS = [-1003361941052]

START_TIME = datetime.utcnow()
SEEN_IDS = deque(maxlen=500)

# =========================
# APIs
# =========================
CR_API_URL = "http://51.77.216.195/crapi/dgroup/viewstats"
CR_TOKEN = "RFdVNEVBg2mHV21KhGFwZlN2j3JYZYJlRpZSiUZvdVVemG-He2M="
CR_RECORD_LIMIT = 20

MAIT_API_URL = "http://51.77.216.195/crapi/mait/viewstats"
MAIT_TOKEN = "SFFRRDRSQmtgUFCJYoBidEFoYEJdeGNFcpZwXXhjUmpkkINfc095"
MAIT_RECORD_LIMIT = 20


# =========================
# FETCH
# =========================
def fetch_api(url, token, limit):
    try:
        r = requests.get(url, params={"token": token, "records": limit}, timeout=10)
        data = r.json()
        if data.get("status") != "success":
            return None
        x = data["data"][0]
        return {
            "time": x.get("dt", ""),
            "number": x.get("num", ""),
            "service": x.get("cli", ""),
            "message": x.get("message", ""),
        }
    except:
        return None


# =========================
# HELPERS
# =========================
def extract_otp(msg):
    m = re.search(r"\d{4,6}", msg or "")
    return m.group(0) if m else "N/A"


def mask_number(n):
    try:
        s = "+" + n
        return s[:5] + "*" * (len(s) - 9) + s[-4:]
    except:
        return "+" + n


def format_message(d):
    otp = extract_otp(d["message"])
    return f"""
<b>🔐 New OTP</b>

🕐 Time: {d['time']}
📲 Service: {d['service']}
📞 Number: {mask_number(d['number'])}
🔑 OTP: <code>{otp}</code>

<pre>{d['message']}</pre>
"""


# =========================
# WORKERS
# =========================
async def cr_worker(app):
    while True:
        d = fetch_api(CR_API_URL, CR_TOKEN, CR_RECORD_LIMIT)
        if d:
            uid = d["number"] + d["message"]
            if uid not in SEEN_IDS:
                SEEN_IDS.append(uid)
                for gid in GROUP_IDS:
                    await app.bot.send_message(
                        chat_id=gid,
                        text=format_message(d),
                        parse_mode="HTML",
                    )
        await asyncio.sleep(3)


async def mait_worker(app):
    while True:
        d = fetch_api(MAIT_API_URL, MAIT_TOKEN, MAIT_RECORD_LIMIT)
        if d:
            uid = d["number"] + d["message"]
            if uid not in SEEN_IDS:
                SEEN_IDS.append(uid)
                for gid in GROUP_IDS:
                    await app.bot.send_message(
                        chat_id=gid,
                        text=format_message(d),
                        parse_mode="HTML",
                    )
        await asyncio.sleep(3)


# =========================
# COMMANDS
# =========================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running ✅")


async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = datetime.utcnow() - START_TIME
    await update.message.reply_text(f"Uptime: {uptime}")


# =========================
# MAIN
# =========================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))

    asyncio.create_task(cr_worker(app))
    asyncio.create_task(mait_worker(app))

    app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())

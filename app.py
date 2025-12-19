import asyncio
import requests
import re
import time
import platform
import psutil
import phonenumbers
from phonenumbers import geocoder
from telegram import (
    Bot,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
from datetime import datetime
from collections import deque
import logging

# =========================
# BASIC SETUP
# =========================
logging.basicConfig(level=logging.INFO)

# ✅ TOKEN (FIXED SYNTAX)
BOT_TOKEN = "8437087674:AAEEBJDfEkxl0MbA__lsSF4A7qc7UpwzGU4"

bot = Bot(token=BOT_TOKEN)

GROUP_IDS = [-1003361941052]

START_TIME = datetime.utcnow()
SEEN_IDS = deque(maxlen=500)

# =========================
# CR API
# =========================
CR_API_URL = "http://51.77.216.195/crapi/dgroup/viewstats"
CR_TOKEN = "RFdVNEVBg2mHV21KhGFwZlN2j3JYZYJlRpZSiUZvdVVemG-He2M="
CR_RECORD_LIMIT = 20

# =========================
# MAIT API
# =========================
MAIT_API_URL = "http://51.77.216.195/crapi/mait/viewstats"
MAIT_TOKEN = "SFFRRDRSQmtgUFCJYoBidEFoYEJdeGNFcpZwXXhjUmpkkINfc095"
MAIT_RECORD_LIMIT = 20

# =========================
# FILTER
# =========================
CLI_FILTER_MODE = "off"
ALLOWED_CLIS = []
BLOCKED_CLIS = []


def cli_passes_filter(cli):
    if not cli:
        return True
    c = cli.lower()
    if CLI_FILTER_MODE == "allow":
        return any(x.lower() in c for x in ALLOWED_CLIS)
    if CLI_FILTER_MODE == "block":
        return not any(x.lower() in c for x in BLOCKED_CLIS)
    return True


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
            "message": x.get("message", "")
        }
    except:
        return None


# =========================
# HELPERS
# =========================
def extract_otp(msg):
    for p in [r"\d{6}", r"\d{4}"]:
        m = re.search(p, msg or "")
        if m:
            return m.group(0)
    return "N/A"


def mask_number(n):
    try:
        s = "+" + n
        return s[:5] + "*" * (len(s) - 9) + s[-4:]
    except:
        return "+" + n


def country_info(num):
    try:
        if not num.startswith("+"):
            num = "+" + num
        p = phonenumbers.parse(num)
        name = geocoder.description_for_number(p, "en")
        return name or "Unknown", "🌍"
    except:
        return "Unknown", "🌍"


def format_message(d):
    otp = extract_otp(d["message"])
    country, flag = country_info(d["number"])
    return f"""
<b>{flag} New {d['service']} OTP!</b>

🕐 Time: {d['time']}
🌍 Country: {country}
📞 Number: {mask_number(d['number'])}
🔐 OTP: <code>{otp}</code>

<pre>{d['message']}</pre>

Powered by Junaid Niz 💗
"""


# =========================
# SEND
# =========================
async def send_groups(msg):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Channel", url="https://t.me/jndtech1")],
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Junaidniz786")]
    ])
    for gid in GROUP_IDS:
        try:
            await bot.send_message(
                gid,
                msg,
                parse_mode="HTML",
                reply_markup=kb
            )
        except:
            pass


# =========================
# WORKERS
# =========================
async def cr_worker():
    while True:
        d = fetch_api(CR_API_URL, CR_TOKEN, CR_RECORD_LIMIT)
        if d:
            uid = d["number"] + d["message"]
            if uid not in SEEN_IDS:
                SEEN_IDS.append(uid)
                await send_groups(format_message(d))
        await asyncio.sleep(3)


async def mait_worker():
    while True:
        d = fetch_api(MAIT_API_URL, MAIT_TOKEN, MAIT_RECORD_LIMIT)
        if d:
            uid = d["number"] + d["message"]
            if uid not in SEEN_IDS:
                SEEN_IDS.append(uid)
                await send_groups(format_message(d))
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

    asyncio.create_task(cr_worker())
    asyncio.create_task(mait_worker())

    app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())

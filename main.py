import requests, logging, re, asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TimedOut

# =========================
# DIRECT CONFIG (FIXED)
# =========================
BOT_TOKEN = "7966170259:AAGB5-1CnHvM6Ej9EtlphzhUxb9s8DWRpu0"
CHAT_ID = "-1003361941052"

USERNAME = "Junaidali786"
PASSWORD = "Junaidali786"

BASE_URL = "http://51.89.99.105/NumberPanel"
LOGIN_PAGE_URL = BASE_URL + "/ints/login"
LOGIN_POST_URL = BASE_URL + "/ints/signin"
DATA_URL = BASE_URL + "/ints/client/res/data_smscdr.php"

# =========================
bot = Bot(token=BOT_TOKEN)
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android) Chrome Mobile"
})

logging.basicConfig(level=logging.INFO, format="%(message)s")

# =========================
COUNTRY_MAP = {
    "92": "🇵🇰 Pakistan",
    "91": "🇮🇳 India",
    "880": "🇧🇩 Bangladesh",
    "1": "🇺🇸 USA / 🇨🇦 Canada"
}

def country(num):
    for c in sorted(COUNTRY_MAP, key=len, reverse=True):
        if num.startswith(c):
            return COUNTRY_MAP[c]
    return "🌍 Unknown"

def esc(t):
    return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

# =========================
def login():
    try:
        r = session.get(LOGIN_PAGE_URL, timeout=10)
        m = re.search(r"What is (\d+) \+ (\d+)", r.text)
        if not m:
            logging.error("❌ Captcha not found")
            return False

        capt = int(m.group(1)) + int(m.group(2))

        payload = {
            "username": USERNAME,
            "password": PASSWORD,
            "capt": capt
        }

        r = session.post(LOGIN_POST_URL, data=payload, timeout=10)

        if "logout" in r.text.lower():
            logging.info("✅ Login successful")
            return True

        logging.error("❌ Login failed")
        return False

    except Exception as e:
        logging.error(f"Login error: {e}")
        return False

# =========================
def fetch_sms():
    url = (
        f"{DATA_URL}"
        "?fdate1=2025-01-01%2000:00:00"
        "&fdate2=2026-01-01%2023:59:59"
        "&fg=0&sEcho=1&iDisplayStart=0&iDisplayLength=25"
    )

    r = session.get(url, headers={"X-Requested-With": "XMLHttpRequest"}, timeout=10)

    if "login" in r.text.lower():
        login()
        return fetch_sms()

    return r.json()

# =========================
async def loop():
    sent = set()

    while True:
        data = fetch_sms()
        if not data or "aaData" not in data:
            await asyncio.sleep(3)
            continue

        for row in data["aaData"]:
            time_ = str(row[0])
            number = str(row[2])
            service = str(row[3])
            msg = str(row[4])

            otp = re.search(r"\b\d{4,6}\b", msg)
            otp = otp.group() if otp else "N/A"

            key = f"{number}|{otp}"
            if key in sent:
                continue
            sent.add(key)

            text = (
                "<b>🔔 NEW OTP RECEIVED</b>\n\n"
                f"<b>⏰ Time:</b> {esc(time_)}\n"
                f"<b>📞 Number:</b> {esc(number)}\n"
                f"<b>🌍 Country:</b> {country(number)}\n"
                f"<b>📱 Service:</b> {esc(service)}\n\n"
                f"<b>🔑 OTP:</b> <code>{otp}</code>\n\n"
                f"<blockquote>{esc(msg)}</blockquote>"
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Main Channel", url="https://t.me/jndtech1")]
            ])

            try:
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                logging.info(f"📤 OTP sent: {otp}")
            except TimedOut:
                logging.error("Telegram timeout")

        await asyncio.sleep(3)

# =========================
async def main():
    if login():
        await loop()
    else:
        logging.error("❌ Initial login failed")

asyncio.run(main())

import requests, logging, os, re, asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TimedOut

# ======================
# ENV (Railway Variables)
# ======================
BOT_TOKEN = os.getenv("8550802106:AAHhbkIS8Svn5_6qjlT8xmKUbhsZVY_YT2Q")
CHAT_ID = os.getenv("-1003361941052")
USERNAME = os.getenv("Junaidali786")
PASSWORD = os.getenv("Junaidali786")

BASE_URL = "http://51.89.99.105/NumberPanel"
LOGIN_PAGE_URL = BASE_URL + "/ints/login"
LOGIN_POST_URL = BASE_URL + "/ints/signin"
DATA_URL = BASE_URL + "/ints/client/res/data_smscdr.php"

bot = Bot(token=BOT_TOKEN)
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android) Chrome Mobile"
})

logging.basicConfig(level=logging.INFO, format="%(message)s")

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

def login():
    r = session.get(LOGIN_PAGE_URL)
    m = re.search(r"What is (\d+) \+ (\d+)", r.text)
    if not m:
        return False
    capt = int(m.group(1)) + int(m.group(2))
    payload = {"username": USERNAME, "password": PASSWORD, "capt": capt}
    r = session.post(LOGIN_POST_URL, data=payload)
    return "logout" in r.text.lower()

def fetch_sms():
    url = (
        f"{DATA_URL}?fdate1=2025-01-01%2000:00:00&"
        f"fdate2=2026-01-01%2023:59:59&fg=0&iDisplayLength=25"
    )
    r = session.get(url, headers={"X-Requested-With":"XMLHttpRequest"})
    if "login" in r.text.lower():
        login()
        return fetch_sms()
    return r.json()

async def loop():
    sent=set()
    while True:
        data = fetch_sms()
        if not data or "aaData" not in data:
            await asyncio.sleep(3)
            continue

        for r in data["aaData"]:
            t, num, srv, msg = r[0], r[2], r[3], r[4]
            otp = re.search(r"\b\d{4,6}\b", msg)
            otp = otp.group() if otp else "N/A"
            key=f"{num}|{otp}"
            if key in sent: continue
            sent.add(key)

            text = (
                "<b>🔔 NEW OTP</b>\n\n"
                f"<b>📞 Number:</b> {esc(num)}\n"
                f"<b>🌍 Country:</b> {country(num)}\n"
                f"<b>📱 Service:</b> {esc(srv)}\n"
                f"<b>🔑 OTP:</b> <code>{otp}</code>\n\n"
                f"<blockquote>{esc(msg)}</blockquote>"
            )

            try:
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Main Channel", url="https://t.me/jndtech1")]]
                    )
                )
                logging.info("OTP sent")
            except TimedOut:
                pass
        await asyncio.sleep(3)

async def main():
    if login():
        await loop()

asyncio.run(main())

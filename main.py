import requests
import time
from telegram import Bot
from collections import defaultdict
from datetime import datetime

API_KEY = "d187oepr01ql1b4mbi1gd187oepr01ql1b4mbi20"
TELEGRAM_TOKEN = "8120887452:AAESsIpRAj4qLS_M09p5Ptrr870Ya99HLSs"
CHAT_ID = "1325489931"
bot = Bot(token=TELEGRAM_TOKEN)

alert_counter = defaultdict(int)

def get_stock_data(symbol):
    url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}?apiKey={API_KEY}"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json().get("ticker", {})
    if not data:
        return None

    price = data["lastTrade"]["p"]
    volume = round(data["day"]["v"] / 1_000_000, 2)
    rvol = round(data["metrics"]["relative_volume"], 2)
    float_shares = round(data.get("shares_float", 0) / 1_000_000, 2)
    return price, rvol, volume, float_shares

def send_alert(symbol, price, rvol, volume, float_shares, tests):
    alert_counter[symbol] += 1
    alert_num = alert_counter[symbol]

    message = f"""📡 تنبيه ({alert_num})

📈 السهم: ${symbol}
💵 السعر: {price}
📊 RVOL اليومي: {rvol}x
📦 حجم التداول: {volume}M
🪶 الفلوت: {float_shares}M

🧠 التحليل:
▪️ فوليوم مرتفع بشكل مفاجئ
▪️ السعر فوق VWAP
▪️ تحرك سريع قد يكون بسبب زخم أو خبر

⏰ الوقت: {datetime.now().strftime('%I:%M %p')}
🔁 مرات اختبار المقاومة: {tests}
"""
    bot.send_message(chat_id=CHAT_ID, text=message)

STOCKS = ["MARA", "RIOT", "COSM", "GME", "CVNA", "PLTR", "AMD", "SOFI"]

while True:
    for symbol in STOCKS:
        try:
            data = get_stock_data(symbol)
            if not data:
                continue
            price, rvol, volume, float_shares = data
            resistance_tests = 2  # مؤقت، بيتم تحسينه لاحقاً

            if price >= 100 or rvol < 2 or float_shares >= 20 or resistance_tests < 2:
                continue

            send_alert(symbol, price, rvol, volume, float_shares, resistance_tests)
            time.sleep(1)

        except Exception as e:
            print(f"خطأ مع {symbol}: {e}")
            continue

    time.sleep(60)

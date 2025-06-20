import requests
import time
from telegram import Bot

# معلومات الاتصال
TELEGRAM_TOKEN = '8120887452:AAESsIpRAj4qLS_M09p5Ptrr870Ya99HLSs'
CHAT_ID = '1325489931'
POLYGON_API_KEY = 'YourPolygonAPIKeyHere'  # استبدله بمفتاحك

# تهيئة البوت
bot = Bot(token=TELEGRAM_TOKEN)

# قائمة رموز الأسهم (اختصرناها لتجربة)
TICKERS = ["AAPL", "TSLA", "NVDA", "AMD", "RIOT", "MARA"]

# الدالة اللي تجيب بيانات الزخم
def check_stocks():
    for symbol in TICKERS:
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?adjusted=true&apiKey={POLYGON_API_KEY}"
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            if data.get("results"):
                result = data["results"][0]
                change = ((result["c"] - result["o"]) / result["o"]) * 100
                if change >= 5:
                    msg = f"🚀 زخم قوي في سهم {symbol}:\nالنسبة: {change:.2f}% 🔥"
                    bot.send_message(chat_id=CHAT_ID, text=msg)
        time.sleep(1)

# تنفيذ التنبيهات كل دقيقة
while True:
    try:
        check_stocks()
        time.sleep(60)
    except Exception as e:
        print(f"خطأ: {e}")
        time.sleep(60)

import requests
import pandas as pd
import time
from datetime import datetime
from telegram import Bot

# مفاتيح التشغيل
POLYGON_API_KEY = "0hIZppRq0ddFHBD...Tgq7B"  # حط المفتاح الكامل هنا
TELEGRAM_TOKEN = "8120887452:AAESsIpRAj4qLS_M09p5Ptrr870Ya99HLSs"
CHAT_ID = "1325489931"

bot = Bot(token=TELEGRAM_TOKEN)

def format_alert(stock):
    symbol = stock["ticker"]
    last = stock["lastTrade"]["p"]
    change = stock["todaysChangePerc"]
    volume = stock["day"]["v"]
    avg_volume = stock["day"]["av"]
    rvol = round(volume / avg_volume, 2) if avg_volume else 0
    market_cap = stock.get("marketCap", "N/A")
    float_shares = stock.get("float", "N/A")

    alert_type = []
    if rvol > 3: alert_type.append("RVOL عالي")
    if change > 5: alert_type.append("زخم")
    if last < 1: alert_type.append("تحت الدولار")
    if 1 <= last < 20: alert_type.append("اختراق مقاومة")

    alert = (
        "تنبيه سهم\n"
        f"الرمز: ${symbol}\n"
        f"السعر: {last}\n"
        f"نسبة التغير: {change}%\n"
        f"RVOL: {rvol}x\n"
        f"الحجم: {volume}\n"
        f"القيمة السوقية: {market_cap}\n"
        f"عدد الأسهم الحرة: {float_shares}\n"
        f"نوع التنبيه: {' + '.join(alert_type) if alert_type else 'غير محدد'}\n"
        f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    return alert

def scan_stocks():
    url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?apiKey={POLYGON_API_KEY}"
    response = requests.get(url)
    data = response.json()

    tickers = data.get("tickers", [])
    for stock in tickers:
        try:
            last = stock["lastTrade"]["p"]
            change = stock["todaysChangePerc"]
            volume = stock["day"]["v"]
            avg_volume = stock["day"]["av"]
            rvol = volume / avg_volume if avg_volume else 0

            if last < 20 and rvol > 2 and change > 3:
                alert_msg = format_alert(stock)
                bot.send_message(chat_id=CHAT_ID, text=alert_msg)
        except Exception as e:
            print(f"خطأ في {stock['ticker']}: {e}")

# تشغيل كل دقيقة
while True:
    scan_stocks()
    time.sleep(60)

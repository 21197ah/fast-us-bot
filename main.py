import requests
import pandas as pd
import time
from datetime import datetime
from telegram import Bot
import numpy as np
import ta

# مفاتيح التشغيل
POLYGON_API_KEY = "0hIZppRq0ddFHBDHzoBF7xYbceeiU9eTgq7B"
TELEGRAM_TOKEN = "8120887452:AAESsIpRAj4qLS_M09p5Ptrr870Ya99HLSs"
CHAT_ID = "1325489931"

bot = Bot(token=TELEGRAM_TOKEN)

def get_minute_data(symbol):
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/1/day?adjusted=true&include_pre_post=true&sort=asc&limit=100&apiKey={POLYGON_API_KEY}"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    df = pd.DataFrame(r.json().get("results", []))
    if df.empty or len(df) < 14:
        return None
    df["t"] = pd.to_datetime(df["t"], unit="ms")
    df.set_index("t", inplace=True)
    df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"}, inplace=True)
    df["VWAP"] = (df["Close"] * df["Volume"]).cumsum() / df["Volume"].cumsum()
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    df["EMA9"] = ta.trend.ema_indicator(df["Close"], window=9)
    df["EMA21"] = ta.trend.ema_indicator(df["Close"], window=21)
    return df

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

def scan_every_minute():
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
            print(f"خطأ في {stock.get('ticker', 'غير معروف')}: {e}")

def scan_every_5min():
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
                symbol = stock["ticker"]
                df = get_minute_data(symbol)
                if df is None:
                    continue

                latest = df.iloc[-1]
                rsi = latest["RSI"]
                vwap = latest["VWAP"]
                ema9 = latest["EMA9"]
                ema21 = latest["EMA21"]

                if np.isnan(rsi) or np.isnan(vwap) or np.isnan(ema9) or np.isnan(ema21):
                    continue
                if not (last > vwap and ema9 > ema21 and rsi < 75):
                    continue

                alert_msg = format_alert(stock)
                bot.send_message(chat_id=CHAT_ID, text=alert_msg)

        except Exception as e:
            print(f"خطأ في {stock.get('ticker', 'غير معروف')}: {e}")

# الحلقة الرئيسية
last_5min = time.time()

while True:
    scan_every_minute()
    if time.time() - last_5min > 300:
        scan_every_5min()
        last_5min = time.time()
    time.sleep(60)

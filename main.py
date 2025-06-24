import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from telegram import Bot

# مفاتيح التشغيل
TELEGRAM_TOKEN = "8120887452:AAESsIPRaj4qLS_M09p5Ptr870Ya99HLSs"
CHAT_ID = 1325489931
POLYGON_API_KEY = "F3HbS9dbxHrxY9P9yIb8F3HbS9dbxHrxY9P9yIb8"

bot = Bot(token=TELEGRAM_TOKEN)

def send_alert(symbol, price, change, total_value, rvol, float_val, cap, note):
    msg = (
        f"🚨 تنبيه زخم لحظي\n"
        f"الرمز: ${symbol}\n"
        f"نسبة الارتفاع: +{change}%\n"
        f"السعر: {price}\n"
        f"الفلوت: {float_val/1_000_000:.1f}M\n"
        f"القيمة السوقية: {cap/1_000_000_000:.1f}B\n"
        f"الحجم النسبي: {rvol}x\n"
        f"حجم التداول: ${int(total_value):,}\n"
        f"نوع التنبيه: {note}"
    )
    bot.send_message(chat_id=CHAT_ID, text=msg)

def fetch_1min_candles(symbol):
    now = datetime.utcnow()
    start = (now - timedelta(minutes=30)).isoformat()
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{start}/{now.isoformat()}?adjusted=true&sort=asc&apiKey={POLYGON_API_KEY}"
    res = requests.get(url)
    data = res.json()
    if 'results' not in data:
        return None
    df = pd.DataFrame(data["results"])
    df["t"] = pd.to_datetime(df["t"], unit="ms")
    df.set_index("t", inplace=True)
    return df

def calc_indicators(df):
    df["EMA9"] = df["c"].ewm(span=9).mean()
    df["EMA21"] = df["c"].ewm(span=21).mean()
    delta = df["c"].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(14).mean()
    avg_loss = pd.Series(loss).rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    df["VWAP"] = (df["c"] * df["v"]).cumsum() / df["v"].cumsum()
    return df

def check_conditions(stock):
    symbol = stock["ticker"]
    price = stock["lastTrade"]["p"]
    change = stock["todaysChangePerc"]
    volume = stock["day"]["v"]
    avg_volume = stock["day"]["av"]
    float_val = stock.get("sharesOutstanding", 0)
    cap = stock.get("marketCap", 0)
    total_value = price * volume
    rvol = round(volume / avg_volume, 2) if avg_volume else 0

    now = datetime.utcnow().hour
    is_premarket_or_afterhours = now < 13 or now >= 20

    if price > 20 or float_val > 10_000_000 or cap > 500_000_000:
        return None

    if is_premarket_or_afterhours:
        if change >= 10 and total_value >= 50000:
            note = "اختراق + سيولة بري ماركت"
            return (symbol, price, change, total_value, rvol, float_val, cap, note)
    else:
        if change >= 5 and total_value >= 50000 and rvol >= 1.5:
            df = fetch_1min_candles(symbol)
            if df is None or df.empty:
                return None
            df = calc_indicators(df)
            last_row = df.iloc[-1]
            if last_row["c"] > last_row["VWAP"] and last_row["EMA9"] > last_row["EMA21"] and last_row['v'] > df['v'].iloc[-6:-1].mean() * 3:
                note = "اختراق مقاومة + دخول سيولة مفاجئة"
                return (symbol, price, change, total_value, rvol, float_val, cap, note)

    return None

while True:
    try:
        url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?apiKey={POLYGON_API_KEY}"
        res = requests.get(url)
        stocks = res.json()["tickers"]

        for stock in stocks:
            result = check_conditions(stock)
            if result:
                send_alert(*result)

    except Exception as e:
        print("خطأ:", e)

    time.sleep(60)

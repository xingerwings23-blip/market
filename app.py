import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import plotly.graph_objects as go
import time

# =========================
# API KEY
# =========================
ALPHA_VANTAGE_KEY = "8HNY2KQO7SZM8NF9"

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Market Analysis Dashboard", layout="wide")

# =========================
# DISCLAIMER
# =========================
if "ok" not in st.session_state:
    st.session_state.ok = False

if not st.session_state.ok:
    st.warning("This app is for educational purposes only. Accuracy ~60–70%. Not financial advice.")
    if st.button("I understand"):
        st.session_state.ok = True
    st.stop()

# =========================
# ASSETS
# =========================
ASSETS = {
    "BTCUSDT": "crypto",
    "ETHUSDT": "crypto",
    "BNBUSDT": "crypto",
    "SOLUSDT": "crypto",
    "XRPUSDT": "crypto",
    "ADAUSDT": "crypto",
    "DOGEUSDT": "crypto",
    "MATICUSDT": "crypto",
    "AVAXUSDT": "crypto",
    "AAPL": "stock",
    "TSLA": "stock"
}

selected = st.selectbox("Select Asset", list(ASSETS.keys()))

# =========================
# DATA FETCHERS
# =========================
def fetch_binance(symbol, limit=500):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit={limit}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if not isinstance(data, list):
            return None

        df = pd.DataFrame(data, columns=[
            "t","open","high","low","close","volume",
            "ct","qv","n","tb","tq","i"
        ])
        df["Date"] = pd.to_datetime(df["t"], unit="ms")
        df.set_index("Date", inplace=True)
        df = df[["open","high","low","close","volume"]].astype(float)
        return df
    except:
        return None

def fetch_coingecko(symbol):
    map_ids = {
        "BTCUSDT":"bitcoin","ETHUSDT":"ethereum","BNBUSDT":"binancecoin",
        "SOLUSDT":"solana","XRPUSDT":"ripple","ADAUSDT":"cardano",
        "DOGEUSDT":"dogecoin","MATICUSDT":"polygon","AVAXUSDT":"avalanche"
    }
    if symbol not in map_ids:
        return None

    url = f"https://api.coingecko.com/api/v3/coins/{map_ids[symbol]}/market_chart?vs_currency=usd&days=365"
    try:
        r = requests.get(url, timeout=10).json()
        prices = r["prices"]
        df = pd.DataFrame(prices, columns=["Date","close"])
        df["Date"] = pd.to_datetime(df["Date"], unit="ms")
        df.set_index("Date", inplace=True)
        df["open"] = df["high"] = df["low"] = df["close"]
        df["volume"] = np.nan
        return df
    except:
        return None

def fetch_stock(symbol):
    # yfinance first
    try:
        df = yf.download(symbol, period="1y", interval="1d", progress=False)
        if not df.empty:
            df = df[["Open","High","Low","Close","Volume"]]
            df.columns = ["open","high","low","close","volume"]
            return df
    except:
        pass

    # Alpha Vantage fallback
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
        r = requests.get(url, timeout=10).json()
        ts = r.get("Time Series (Daily)")
        if not ts:
            return None

        df = pd.DataFrame(ts).T.rename(columns={
            "1. open":"open","2. high":"high",
            "3. low":"low","4. close":"close","5. volume":"volume"
        }).astype(float)
        df.index = pd.to_datetime(df.index)
        return df.sort_index()
    except:
        return None

# =========================
# GET DATA
# =========================
def get_data(symbol):
    if ASSETS[symbol] == "crypto":
        df = fetch_binance(symbol)
        if df is None or len(df) < 50:
            df = fetch_coingecko(symbol)
        return df
    else:
        return fetch_stock(symbol)

# =========================
# ANALYSIS
# =========================
def analyze(df):
    if df is None or len(df) < 50:
        return None

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    rsi = 100 - (100 / (1 + rs))

    ma20 = df["close"].rolling(20).mean()
    ma50 = df["close"].rolling(50).mean()

    score = 0
    reasons = []

    if rsi.iloc[-1] < 30:
        score += 25
        reasons.append("RSI oversold")
    elif rsi.iloc[-1] > 70:
        score -= 25
        reasons.append("RSI overbought")

    if ma20.iloc[-1] > ma50.iloc[-1]:
        score += 20
        reasons.append("Bullish trend")
    else:
        score -= 20
        reasons.append("Bearish trend")

    buy = np.clip(50 + score, 0, 100)
    sell = 100 - buy

    bias = "NEUTRAL"
    if buy > 55:
        bias = "BUY BIAS"
    elif buy < 45:
        bias = "SELL BIAS"

    return buy, sell, bias, reasons, ma20, ma50

# =========================
# RUN
# =========================
df = get_data(selected)
result = analyze(df)

if result is None:
    st.error("Could not fetch enough data for this asset. Try again later.")
    st.stop()

buy, sell, bias, reasons, ma20, ma50 = result

st.subheader(f"{selected}")
st.write(f"🟢 Buy: **{buy:.1f}%** | 🔴 Sell: **{sell:.1f}%** | ⚖️ {bias}")

fig = go.Figure()
fig.add_candlestick(
    x=df.index,
    open=df["open"], high=df["high"],
    low=df["low"], close=df["close"]
)
fig.add_scatter(x=df.index, y=ma20, name="MA20")
fig.add_scatter(x=df.index, y=ma50, name="MA50")
fig.update_layout(height=450, xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)
st.write("Reasons:", ", ".join(reasons))

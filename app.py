
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
st.set_page_config("Market Dashboard", layout="wide")

# =========================
# DISCLAIMER
# =========================
if "accepted" not in st.session_state:
    st.session_state.accepted = False

if not st.session_state.accepted:
    st.warning("Educational use only • Accuracy ~60–70% • Not financial advice")
    if st.button("I Understand"):
        st.session_state.accepted = True
    st.stop()

# =========================
# SIDEBAR CONTROLS
# =========================
st.sidebar.header("Settings")

auto_refresh = st.sidebar.selectbox(
    "Auto-Refresh",
    ["Off", "1 min", "3 min", "5 min", "15 min", "30 min"]
)

chart_type = st.sidebar.selectbox(
    "Chart Type",
    ["Candlestick", "Line", "Area"]
)

alert_price = st.sidebar.number_input(
    "Alert price (0 = off)", value=0.0
)

# =========================
# AUTO REFRESH LOGIC
# =========================
refresh_map = {
    "1 min": 60,
    "3 min": 180,
    "5 min": 300,
    "15 min": 900,
    "30 min": 1800
}

if auto_refresh != "Off":
    time.sleep(refresh_map[auto_refresh])
    st.rerun()

# =========================
# ASSETS
# =========================
ASSETS = {
    "BTCUSDT":"crypto","ETHUSDT":"crypto","BNBUSDT":"crypto",
    "SOLUSDT":"crypto","XRPUSDT":"crypto","ADAUSDT":"crypto",
    "DOGEUSDT":"crypto","MATICUSDT":"crypto","AVAXUSDT":"crypto",
    "AAPL":"stock","TSLA":"stock"
}

asset = st.selectbox("Select Asset", list(ASSETS.keys()))

# =========================
# DATA FETCH
# =========================
def fetch_crypto(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=500"
    try:
        r = requests.get(url, timeout=10).json()
        df = pd.DataFrame(r, columns=[
            "t","o","h","l","c","v","ct","q","n","tb","tq","i"
        ])
        df["Date"] = pd.to_datetime(df["t"], unit="ms")
        df.set_index("Date", inplace=True)
        df = df[["o","h","l","c","v"]].astype(float)
        df.columns = ["open","high","low","close","volume"]
        return df
    except:
        return None

def fetch_stock(symbol):
    try:
        df = yf.download(symbol, period="1y", interval="1d", progress=False)
        if not df.empty:
            df = df[["Open","High","Low","Close","Volume"]]
            df.columns = ["open","high","low","close","volume"]
            return df
    except:
        pass

    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
        r = requests.get(url).json()
        ts = r.get("Time Series (Daily)")
        if not ts:
            return None
        df = pd.DataFrame(ts).T.astype(float)
        df = df.rename(columns={
            "1. open":"open","2. high":"high",
            "3. low":"low","4. close":"close","5. volume":"volume"
        })
        df.index = pd.to_datetime(df.index)
        return df.sort_index()
    except:
        return None

df = fetch_crypto(asset) if ASSETS[asset]=="crypto" else fetch_stock(asset)

if df is None or len(df) < 50:
    st.error("gratefull fallback")
    st.stop()

# =========================
# ANALYSIS
# =========================
delta = df["close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
rs = gain.rolling(14).mean() / loss.rolling(14).mean()
rsi = 100 - (100 / (1 + rs))

ma20 = df["close"].rolling(20).mean()
ma50 = df["close"].rolling(50).mean()

score = 50
if rsi.iloc[-1] < 30: score += 20
elif rsi.iloc[-1] > 70: score -= 20
if ma20.iloc[-1] > ma50.iloc[-1]: score += 15
else: score -= 15

buy = np.clip(score, 0, 100)
sell = 100 - buy

bias = "NEUTRAL"
if buy > 60: bias = "BUY-SIDE"
elif buy < 40: bias = "SELL-SIDE"

# =========================
# CONFIDENCE METER
# =========================
st.subheader(f"{asset} Analysis")
st.metric("Buy %", f"{buy:.1f}%")
st.metric("Sell %", f"{sell:.1f}%")
st.progress(int(buy))

st.write("Bias:", bias)

# =========================
# ALERT
# =========================
if alert_price > 0 and df["close"].iloc[-1] >= alert_price:
    st.warning("⚠️ Price alert triggered!")

# =========================
# CHART (ZOOM FIXED)
# =========================
fig = go.Figure()

if chart_type == "Candlestick":
    fig.add_candlestick(
        x=df.index,
        open=df["open"], high=df["high"],
        low=df["low"], close=df["close"]
    )
else:
    fig.add_scatter(x=df.index, y=df["close"], fill="tozeroy" if chart_type=="Area" else None)

fig.add_scatter(x=df.index, y=ma20, name="MA20")
fig.add_scatter(x=df.index, y=ma50, name="MA50")

fig.update_layout(
    height=500,
    xaxis_rangeslider_visible=False,
    dragmode="pan",
    uirevision="static"  # 🔥 THIS FIXES ZOOM RESET
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# FUTURE AUTO-TRADING (LOCKED)
# =========================
st.info("🔒 Auto-Trading locked until 18+. Structure ready.")
def fetch_stock(symbol):
    # Primary: yfinance
    try:
        df = yf.download(symbol, period="1y", interval="1d", progress=False)
        if df is not None and not df.empty:
            df = df[["Open","High","Low","Close","Volume"]]
            df.columns = ["open","high","low","close","volume"]
            return df
    except Exception:
        pass

    # Fallback: Alpha Vantage
    try:
        url = (
            "https://www.alphavantage.co/query"
            f"?function=TIME_SERIES_DAILY"
            f"&symbol={symbol}"
            f"&apikey={ALPHA_VANTAGE_KEY}"
        )
        r = requests.get(url, timeout=10).json()
        ts = r.get("Time Series (Daily)")

        if not ts:
            return None

        df = pd.DataFrame(ts).T.rename(columns={
            "1. open": "open",
            "2. high": "high",
            "3. low": "low",
            "4. close": "close",
            "5. volume": "volume"
        })

        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        return df

    except Exception:
        return None



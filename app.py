# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import plotly.graph_objects as go
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Market Analysis Dashboard", page_icon="📊", layout="wide")

# =========================
# DISCLAIMER
# =========================
if "accepted_warning" not in st.session_state:
    st.session_state.accepted_warning = False

if not st.session_state.accepted_warning:
    st.warning("IMPORTANT DISCLAIMER")
    st.write("""
This app is for educational purposes only.
- Analysis is not 100% accurate
- This tool does NOT provide financial advice
""")
    if st.button("I Understand & Continue"):
        st.session_state.accepted_warning = True
    st.stop()

# =========================
# THEME SETTINGS
# =========================
with st.sidebar:
    theme_mode = st.selectbox("Theme Mode", ["Dark", "Light"])
    accent_color = st.color_picker("Accent Color", "#00ff99")

st.markdown(f"<h1 style='text-align:center;color:{accent_color};'>Market Analysis Dashboard</h1>", unsafe_allow_html=True)

# =========================
# ASSET SELECTION
# =========================
assets = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AAPL", "TSLA"]
selected = st.selectbox("Select Asset", assets)

# =========================
# FETCH FUNCTIONS
# =========================
def fetch_binance(symbol, interval, limit=500, retries=2):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    for attempt in range(retries+1):
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            data = res.json()
            if not data:
                continue
            df = pd.DataFrame(data, columns=[
                "open_time","open","high","low","close","volume",
                "close_time","quote_asset_volume","trades",
                "taker_buy_base_vol","taker_buy_quote_vol","ignore"
            ])
            df["Date"] = pd.to_datetime(df["open_time"], unit="ms")
            df.set_index("Date", inplace=True)
            df[["open","high","low","close","volume"]] = df[["open","high","low","close","volume"]].astype(float)
            return df[["open","high","low","close","volume"]]
        except:
            time.sleep(1)
    return None

def fetch_stock(symbol, period="1y", interval="1d", retries=2):
    for attempt in range(retries+1):
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            if df.empty:
                continue
            # Ensure required columns exist
            for col in ["Open","High","Low","Close","Volume"]:
                if col not in df.columns:
                    df[col] = np.nan
            df = df[["Open","High","Low","Close","Volume"]]
            df.columns = [c.lower() for c in df.columns]
            df.index.name = "Date"
            return df
        except:
            time.sleep(1)
    return None

# =========================
# GET DATA WITH FALLBACKS
# =========================
def get_data(symbol):
    if symbol.endswith("USDT"):
        # Crypto
        intervals = ["1d","4h","1h","15m"]
        for intrv in intervals:
            st.info(f"Fetching {symbol} data with interval {intrv}...")
            df = fetch_binance(symbol, intrv)
            if df is not None and not df.empty:
                return df
        return None
    else:
        # Stocks
        periods = [("1y","1d"), ("2y","1wk")]
        for period, interval in periods:
            st.info(f"Fetching {symbol} data {period} {interval}...")
            df = fetch_stock(symbol, period, interval)
            if df is not None and not df.empty:
                return df
        return None

# =========================
# ANALYSIS FUNCTION
# =========================
def analyze(df):
    if df is None or len(df) < 20:
        return None

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

    df["MA20"] = df["close"].rolling(20).mean()
    df["MA50"] = df["close"].rolling(50).mean()

    latest = df.iloc[-1]
    if np.isnan(latest["RSI"]) or np.isnan(latest["MA20"]) or np.isnan(latest["MA50"]):
        return None

    score = 0
    reasons = []

    if latest["RSI"] < 30:
        score += 25
        reasons.append("RSI low")
    elif latest["RSI"] > 70:
        score -= 25
        reasons.append("RSI high")
    else:
        reasons.append("RSI neutral")

    if latest["MA20"] > latest["MA50"]:
        score += 20
        reasons.append("Bullish trend")
    else:
        score -= 20
        reasons.append("Bearish trend")

    buy_pct = np.clip(50 + score, 0, 100)
    sell_pct = 100 - buy_pct

    if 45 <= buy_pct <= 55:
        bias = "NEUTRAL"
    elif buy_pct > 55:
        bias = "BUY-SIDE DOMINANT"
    else:
        bias = "SELL-SIDE DOMINANT"

    return {"buy": round(buy_pct,1), "sell": round(sell_pct,1), "bias": bias, "reasons": reasons, "df": df}

# =========================
# RUN ANALYSIS
# =========================
df = get_data(selected)

# =========================
# DEBUG DISPLAY (Optional)
# =========================
st.write("DEBUG: DataFrame preview")
st.write(df)

result = analyze(df)

if result is None:
    st.error("Could not fetch enough data for this asset. Try again later.")
    st.stop()

# =========================
# DISPLAY DASHBOARD
# =========================
st.write(f"**{selected}** — Buy {result['buy']}% | Sell {result['sell']}% | {result['bias']}")

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=result["df"].index,
    open=result["df"]["open"],
    high=result["df"]["high"],
    low=result["df"]["low"],
    close=result["df"]["close"]
))
fig.add_trace(go.Scatter(x=result["df"].index, y=result["df"]["MA20"], name="MA20"))
fig.add_trace(go.Scatter(x=result["df"].index, y=result["df"]["MA50"], name="MA50"))
fig.update_layout(template="plotly_dark" if theme_mode=="Dark" else "plotly_white",
                  height=450, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

st.write("Reasons:", ", ".join(result["reasons"]))

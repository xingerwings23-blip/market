# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import plotly.graph_objects as go

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
# BINANCE FETCH FUNCTION
# =========================
def fetch_binance_ohlcv(symbol, interval="1d", limit=500):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        if not data:
            return None
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "trades", "taker_buy_base_vol",
            "taker_buy_quote_vol", "ignore"
        ])
        df["Date"] = pd.to_datetime(df["open_time"], unit="ms")
        df.set_index("Date", inplace=True)
        df[["open","high","low","close","volume"]] = df[["open","high","low","close","volume"]].astype(float)
        return df[["open","high","low","close","volume"]]
    except:
        return None

# =========================
# STOCK FETCH FUNCTION
# =========================
def fetch_stock(symbol):
    try:
        df = yf.download(symbol, period="1y", interval="1d", progress=False)
        return df
    except:
        return None

# =========================
# GET DATA (FULLY BULLETPROOF)
# =========================
def get_data(symbol):
    if symbol.endswith("USDT"):
        df = fetch_binance_ohlcv(symbol)
    else:
        df = fetch_stock(symbol)
    
    # ⚠ Early return if df is None or empty
    if df is None or df.empty:
        return None

    # ⚠ Try normalizing columns; return None if fails
    try:
        df.columns = [c.lower() for c in df.columns]
    except AttributeError:
        return None

    return df

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

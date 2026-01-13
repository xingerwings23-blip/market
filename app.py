import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import time

# =============================
# APP CONFIG
# =============================
st.set_page_config(
    page_title="Market Analysis Dashboard",
    layout="wide",
)

st.title("📊 Market Analysis Dashboard")

st.warning(
    "⚠️ Educational tool only. Accuracy ~60–70%. "
    "Not financial advice. You decide all trades."
)

# =============================
# AUTO REFRESH
# =============================
with st.sidebar:
    st.header("⚙️ Settings")

    auto_refresh = st.checkbox("🔄 Enable Auto-Refresh")

    refresh_map = {
        "1 min": 60,
        "5 min": 300,
        "15 min": 900,
        "30 min": 1800,
    }

    refresh_choice = st.selectbox(
        "Refresh Interval",
        list(refresh_map.keys()),
        index=1,
    )

    if auto_refresh:
        st.caption("Auto-refresh active")

# =============================
# ASSET SELECTION
# =============================
assets = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "XRP-USD": "Ripple",
    "BNB-USD": "BNB",
    "SOL-USD": "Solana",
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "MSFT": "Microsoft",
}

selected_asset = st.selectbox(
    "Select Asset",
    list(assets.keys()),
    format_func=lambda x: f"{assets[x]} ({x})",
)

interval = st.selectbox(
    "Timeframe",
    ["1m", "5m", "15m", "1h", "1d"],
    index=2,
)

chart_type = st.radio(
    "Chart Type",
    ["Candlestick", "Line"],
    horizontal=True,
)

# =============================
# INTERVAL NORMALIZATION (CRITICAL FIX)
# =============================
def normalize_interval(asset, interval):
    if asset in ["AAPL", "TSLA", "MSFT"]:
        return "1d"  # stocks → daily only
    return interval

interval = normalize_interval(selected_asset, interval)

# =============================
# DATA FETCH
# =============================
@st.cache_data(ttl=60)
def get_data(symbol, interval):
    try:
        df = yf.download(
            symbol,
            period="60d",
            interval=interval,
            progress=False,
        )

        if df is None or df.empty:
            return None

        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        return df

    except Exception:
        return None

df = get_data(selected_asset, interval)

if df is None or len(df) < 30:
    st.error("❌ Could not fetch enough data for this asset.")
    st.stop()

# =============================
# INDICATORS
# =============================
def analyze(df):
    close = df["close"]

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).

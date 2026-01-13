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
# BINANCE FETCH FUNCTION WITH RETRY
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
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "trades", "taker_buy_base_vol",
                "taker_buy_quote_vol", "ignore"
            ])
            df["Date"] = pd.to_datetime(df["open_time"], unit="ms")
            df.set_index("Date", inplace=True)
            df[["open","high","low","close","volume"]] = df[["open","high","low","close","volume"]].astype(float)
            return df[["open","high","low","close","volume"]]
        except:
            time.sleep(1)  # wait 1s and retry
    return None

# =========================
# STOCK FETCH FUNCTION WITH FIXED COLUMNS
# =========================
def fetch_stock(symbol, period="1y", interval="1d", retries=2):
    for attempt in range(retries+1):
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            if df.empty:
                continue
            # Keep required columns, fill missing with NaN
            required_cols = ["Open","High","Low","Close","Volume"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = np.nan
            df = df[required_cols]
            df.columns = [c.lower() for c in df.columns]
            df.index.name = "Date"
            return df
        except:
            time.sleep(1)
    return None

# =========================
# GET DATA WITH MULTI-INTERVAL FALLBACK
# =========================
def get_data(symbol):
    if symbol.endswith("USDT"):
        # Crypto intervals
        intervals = ["1d", "4h", "1h", "15m"]
        for intrv in intervals:
            st.info(f"Fetching {symbol} data with interval {intrv}...")
            df = fetch_binance(symbol, intrv)
            if df is not None and not df.empty:
                r

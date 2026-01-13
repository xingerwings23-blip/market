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
    st.experimental_rerun()

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

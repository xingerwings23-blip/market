# =========================
# STREAMLIT CONFIG
# =========================
import streamlit as st
st.set_page_config(
    page_title="Market Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# =========================
# IMPORTS
# =========================
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =========================
# DISCLAIMER / WARNING (COMPATIBLE)
# =========================
if "accepted_warning" not in st.session_state:
    st.session_state.accepted_warning = False

if not st.session_state.accepted_warning:
    st.warning("⚠️ IMPORTANT DISCLAIMER")
    st.markdown("""
    **This app is for educational purposes only.**  

    - Market analysis is **not 100% accurate**  
    - Estimated analytical reliability: ~60–70%  
    - This tool **does NOT** provide financial advice  
    - You are fully responsible for any decisions  
    """)
    if st.button("I Understand & Continue"):
        st.session_state.accepted_warning = True
    st.stop()  # Stops execution until the user clicks the button

# =========================
# AUTO REFRESH
# =========================
# Refresh every 60 seconds (adjustable via sidebar later)
st_autorefresh(interval=60000, key="auto_refresh")

# =========================
# THEME SETTINGS
# =========================
with st.sidebar:
    st.markdown("## 🎨 Appearance Settings")
    theme_mode = st.selectbox("Theme Mode", ["Dark", "Light"])
    accent_color = st.color_picker("Accent Color", "#00ff99")
    refresh_rate = st.number_input("Auto-refresh (seconds)", min_value=10, max_value=3600, value=60, step=10)

bg_color = "#0e1117" if theme_mode == "Dark" else "#f5f5f5"
text_color = "white" if theme_mode == "Dark" else "black"

st.markdown(
    f"""
    <style>
    body {{
        background-color: {bg_color};
        color: {text_color};
    }}
    .stMetric {{
        background-color: #1c1c1c;
        border-radius: 12px;
        padding: 10px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(f"<h1 style='text-align:center;color:{accent_color};'>📊 Market Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:gray;'>Buy % • Sell % • Neutral • Analysis only</p>", unsafe_allow_html=True)

# =========================
# ASSET LIST
# =========================
assets = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "AAPL", "TSLA"]
timeframe = st.selectbox("Timeframe", ["15m", "1h", "4h", "1d"])
period_map = {"15m": "7d", "1h": "30d", "4h": "90d", "1d": "1y"}
period = period_map[timeframe]

# =========================
# ANALYSIS FUNCTION
# =========================
def analyze(symbol):
    data = yf.download(symbol, period=period, interval=timeframe, progress=False)
    if len(data) < 50:
        return None
    # RSI
    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    data["RSI"] = 100 - (100 / (1 + rs))
    # Moving Averages
    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"]

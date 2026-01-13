# -*- coding: utf-8 -*-
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

# =========================
# DISCLAIMER / WARNING
# =========================
if "accepted_warning" not in st.session_state:
    st.session_state.accepted_warning = False

if not st.session_state.accepted_warning:
    st.warning("⚠️ IMPORTANT DISCLAIMER")
    st.markdown("""
    **This app is for educational purposes only.**

    - Market analysis is not 100% accurate
    - Estimated analytical reliability: 60–70%
    - This tool does NOT provide financial advice
    - You are fully responsible for any decisions
    """)
    if st.button("I Understand & Continue"):
        st.session_state.accepted_warning = True
    st.stop()

# =========================
# THEME SETTINGS
# =========================
with st.sidebar:
    st.markdown("## Appearance Settings")
    theme_mode = st.selectbox("Theme Mode", ["Dark", "Light"])
    accent_color = st.color_picker("Accent Color", "#00ff99")

bg_color = "#0e1117" if theme_mode == "Dark" else "#f5f5f5"
text_color = "white" if theme_mode == "Dark" else "black"

st.markdown(
    f"<h1 style='text-align:center;color:{accent_color};'>Market Analysis Dashboard</h1>",
    unsafe_allow_html=True
)
st.markdown("<p style='text-align:center;color:gray;'>Buy % | Sell % | Neutral | Analysis only</p>", unsafe_allow_html=True)

# =========================
# ASSET LIST
# =========================
assets = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "AAPL", "TSLA"]
selected = st.selectbox("Select Asset", assets)

interval = "1d"
period = "1y"

# =========================
# DATA FETCH FUNCTION
# =========================
def fetch_data(symbol):
    """Fetch daily OHLC data using yfinance."""
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        return df
    except:
        return None

# =========================
# ANALYSIS FUNCTION
# =========================
def analyze(df):
    if df is None or df.empty or len(df) < 20:
        return None

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()

    latest = df.iloc[-1]

    required_cols = ["RSI", "MA20", "MA50"]
    for col in required_cols:
        if pd.isna(latest[col]):
            return None

    score = 0
    reasons = []

    if latest["RSI"] < 30:
        score += 25
        reasons.append("RSI is low (market cooled)")
    elif latest["RSI"] > 70:
        score -= 25
        reasons.append("RSI is high (market stretched)")
    else:
        reasons.append("RSI is neutral")

    if latest["MA20"] > latest["MA50"]:
        score += 20
        reasons.append("Trend: MA20 > MA50")
    else:
        score -= 20
        reasons.append("Trend: MA20 < MA50")

    buy_pct = np.clip(50 + score, 0, 100)
    sell_pct = 100 - buy_pct

    if 45 <= buy_pct <= 55:
        bias = "NEUTRAL"
    elif buy_pct > 55:
        bias = "BUY-SIDE DOMINANT"
    else:
        bias = "SELL-SIDE DOMINANT"

    explanation = " - ".join(reasons)
    return {"buy": round(buy_pct,1), "sell": round(sell_pct,1),
            "bias": bias, "explanation": explanation, "data": df}

# =========================
# RUN ANALYSIS
# =========================
df = fetch_data(selected)
result = analyze(df)

if result is None:
    st.warning("Not enough data available to analyze this asset.")
    st.stop()

# =========================
# ASSET METRICS
# =========================
st.markdown(f"## {selected} Analysis")
st.markdown(f"Buy {result['buy']}% | Sell {result['sell']}% | Bias: {result['bias']}")

# =========================
# PRICE CHART
# =========================
if df is not None and not df.empty:
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="Price"
    ))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], name="MA20"))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], name="MA50"))
    fig.update_layout(template="plotly_dark" if theme_mode=="Dark" else "plotly_white",
                      height=450,
                      xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Chart data unavailable.")

# =========================
# METRICS + EXPLANATION
# =========================
col1, col2 = st.columns(2)
col1.metric("Buy Pressure", f"{result['buy']}%")
col2.metric("Sell Pressure", f"{result['sell']}%")

st.markdown("### AI Explanation (Why this bias exists)")
st.info(result["ex]()

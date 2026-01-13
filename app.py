# =========================
# STREAMLIT CONFIG
# =========================
import streamlit as st
st.set_page_config(page_title="Market Analysis Dashboard", page_icon="📊", layout="wide")

# =========================
# IMPORTS
# =========================
import requests
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

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
# APPEARANCE
# =========================
with st.sidebar:
    theme_mode = st.selectbox("Theme Mode", ["Dark", "Light"])
    accent_color = st.color_picker("Accent Color", "#00ff99")

bg_color = "#0e1117" if theme_mode == "Dark" else "#f5f5f5"
st.markdown(f"<h1 style='text-align:center;color:{accent_color};'>Market Analysis Dashboard</h1>", unsafe_allow_html=True)

# =========================
# ASSET SELECT
# =========================
assets = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AAPL", "TSLA"]
selected = st.selectbox("Select Asset", assets + ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT"])

# =========================
# UTILITY FUNCTIONS
# =========================

def fetch_binance_ohlcv(symbol, interval="1d", limit=365):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    data = res.json()
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades", "taker_buy_base_vol",
        "taker_buy_quote_vol", "ignore"
    ])
    df["Date"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("Date", inplace=True)
    df[["open","high","low","close","volume"]] = df[["open","high","low","close","volume"]].astype(float)
    return df[["open","high","low","close","volume"]]

def fetch_stock(symbol):
    try:
        df = yf.download(symbol, period="1y", interval="1d", progress=False)
        return df
    except:
        return None

def get_data(symbol):
    if symbol.endswith("USDT"):
        return fetch_binance_ohlcv(symbol, "1d", 365)
    else:
        return fetch_stock(symbol)

def analyze(df):
    if df is None or len(df) < 20:
        return None
    df["RSI"] = 100 - (100/(1 + df["close"].diff().apply(lambda x: max(x,0)).rolling(14).mean()/df["close"].diff().apply(lambda x: -min(x,0)).rolling(14).mean()))
    df["MA20"] = df["close"].rolling(20).mean()
    df["MA50"] = df["close"].rolling(50).mean()
    latest = df.iloc[-1]
    if np.isnan(latest["RSI"]) or np.isnan(latest["MA20"]) or np.isnan(latest["MA50"]):
        return None
    score = 0; reasons=[]
    if latest["RSI"] < 30:
        score += 25; reasons.append("RSI low")
    elif latest["RSI"] > 70:
        score -= 25; reasons.append("RSI high")
    if latest["MA20"] > latest["MA50"]:
        score += 20; reasons.append("Bullish trend")
    else:
        score -= 20; reasons.append("Bearish trend")
    buy = np.clip(50 + score, 0, 100); sell = 100 - buy
    bias = "NEUTRAL" if 45<= buy <=55 else ("BUY" if buy>55 else "SELL")
    return {"buy":round(buy,1), "sell":round(sell,1), "bias":bias, "reasons": reasons, "df":df}

# =========================
# RUN ANALYSIS
# =========================
df = get_data(selected)
result = analyze(df)

if result is None:
    st.error("Could not fetch enough data for this asset.")
    st.stop()

# =========================
# DISPLAY
st.write(f"**{selected}** — Buy {result['buy']}% | Sell {result['sell']}% | {result['bias']}")

fig = go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"]))
fig.update_layout(template="plotly_dark" if theme_mode=="Dark" else "plotly_white")
st.plotly_chart(fig,use_container_width=True)
st.write("Reasons:", ", ".join(result["reasons"]))

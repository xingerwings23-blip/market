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
# DISCLAIMER / WARNING
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
    st.stop()

# =========================
# AUTO REFRESH
# =========================
st_autorefresh(interval=60000, key="auto_refresh")  # refresh every 60 seconds

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

# =========================
# APPLY CSS SAFELY
# =========================
css = f"""
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
"""
st.markdown(css, unsafe_allow_html=True)

st.markdown(f"<h1 style='text-align:center;color:{accent_color};'>📊 Market Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:gray;'>Buy % • Sell % • Neutral • Analysis only</p>", unsafe_allow_html=True)

# =========================
# ASSET LIST
# =========================
assets = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "AAPL", "TSLA"]
selected_interval = st.selectbox("Interval", ["15m", "1h", "4h", "1d"])
interval_priority = ["15m", "1h", "4h", "1d"]  # fallback order

period_map = {"15m": "7d", "1h": "30d", "4h": "90d", "1d": "1y"}

# =========================
# SAFE ANALYSIS FUNCTION
# =========================
def analyze(symbol):
    # Try each interval in order until data is found
    for interval in [selected_interval] + [i for i in interval_priority if i != selected_interval]:
        period = period_map[interval]
        try:
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            if data.empty or len(data) < 20:
                continue  # fallback to next interval

            # RSI
            delta = data["Close"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            rs = gain.rolling(14).mean() / loss.rolling(14).mean()
            data["RSI"] = 100 - (100 / (1 + rs))

            # Moving Averages
            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()

            # MACD
            ema12 = data["Close"].ewm(span=12, adjust=False).mean()
            ema26 = data["Close"].ewm(span=26, adjust=False).mean()
            data["MACD"] = ema12 - ema26
            data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()

            latest = data.iloc[-1]

            # SAFETY CHECK
            required_cols = ["RSI", "MA20", "MA50", "MACD", "Signal", "Open", "High", "Low", "Close"]
            if any(col not in data.columns or pd.isna(latest[col]) for col in required_cols):
                continue  # fallback to next interval

            score = 0
            reasons = []

            # RSI
            if latest["RSI"] < 30:
                score += 25
                reasons.append("RSI is low (market cooled)")
            elif latest["RSI"] > 70:
                score -= 25
                reasons.append("RSI is high (market stretched)")
            else:
                reasons.append("RSI is neutral")

            # Trend
            if latest["MA20"] > latest["MA50"]:
                score += 20
                reasons.append("Short-term trend above long-term trend")
            else:
                score -= 20
                reasons.append("Short-term trend below long-term trend")

            # MACD
            if latest["MACD"] > latest["Signal"]:
                score += 20
                reasons.append("MACD momentum is increasing")
            else:
                score -= 20
                reasons.append("MACD momentum is decreasing")

            # Volume
            if "Volume" in data.columns and not pd.isna(latest["Volume"]):
                vol_strength = latest["Volume"] / data["Volume"].rolling(20).mean().iloc[-1]
                if vol_strength > 1.2:
                    score += 10
                    reasons.append("Volume above average")
                else:
                    reasons.append("Volume normal")
            else:
                reasons.append("Volume data missing")

            buy_pct = np.clip(50 + score, 0, 100)
            sell_pct = 100 - buy_pct
            if 45 <= buy_pct <= 55:
                bias = "NEUTRAL"
            elif buy_pct > 55:
                bias = "BUY-SIDE DOMINANT"
            else:
                bias = "SELL-SIDE DOMINANT"

            explanation = " • ".join(reasons)
            return {"symbol": symbol, "buy": round(buy_pct, 1), "sell": round(sell_pct, 1),
                    "bias": bias, "explanation": explanation, "data": data, "interval": interval}
        except:
            continue  # try next interval
    return None  # no interval worked

# =========================
# FETCH RESULTS
# =========================
results = []
for a in assets:
    r = analyze(a)
    if r is not None:
        results.append(r)

if len(results) == 0:
    st.warning("⚠️ No data available for any asset in any interval. Try different assets later.")
    st.stop()

# =========================
# HEAT MAP
# =========================
st.markdown("## 🔥 Market Heat Map")
heat_cols = st.columns(len(results))
for col, r in zip(heat_cols, results):
    color = "#2ecc71" if r["buy"] > 60 else "#e74c3c" if r["buy"] < 40 else "#f1c40f"
    col.markdown(f"""
        <div style='padding:15px;border-radius:12px;background:{color};color:black;text-align:center;'>
        <h3>{r["symbol"]}</h3>
        <p>Buy {r['buy']}%</p>
        <p style='font-size:12px;'>Interval: {r['interval']}</p>
        </div>
        """, unsafe_allow_html=True)

# =========================
# SCANNER TABLE
# =========================
st.markdown("## 🔍 Multi-Asset Scanner")
scanner_df = pd.DataFrame([{"Asset": r["symbol"], "Interval": r["interval"], "Buy %": r["buy"], "Sell %": r["sell"], "Bias": r["bias"]} for r in results])
st.dataframe(scanner_df, use_container_width=True)

# =========================
# DETAILED VIEW
# =========================
st.markdown("## 📈 Detailed Chart & Explanation")
selected = st.selectbox("Select Asset", [r["symbol"] for r in results])
selected_data = next((r for r in results if r["symbol"] == selected), None)
if selected_data is None:
    st.error(f"No data available for {selected}.")
    st.stop()

# Candlestick chart
d = selected_data["data"]
required_cols = ["Open", "High", "Low", "Close"]
if d.empty or not all(col in d.columns for col in required_cols) or len(d) < 10:
    st.warning(f"⚠️ Not enough data to display chart for {selected_data['symbol']}.")
else:
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=d.index, open=d["Open"], high=d["High"], low=d["Low"], close=d["Close"], name="Price"
    ))
    if "MA20" in d.columns:
        fig.add_trace(go.Scatter(x=d.index, y=d["MA20"], name="MA20"))
    if "MA50" in d.columns:
        fig.add_trace(go.Scatter(x=d.index, y=d["MA50"], name="MA50"))
    fig.update_layout(template="plotly_dark" if theme_mode=="Dark" else "plotly_white", height=450, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# Metrics
c1, c2, c3 = st.columns(3)
c1.metric("📈 Buy Pressure", f"{selected_data['buy']}%")
c2.metric("📉 Sell Pressure", f"{selected_data['sell']}%")
c3.metric("⚖️ Bias", selected_data["bias"])

# AI Explanation
st.markdown("### 🧠 AI Explanation (Why this bias exists)")
st.info(selected_data["explanation"])

# Confidence Alert
if selected_data['buy'] > 75:
    st.success("📊 High buy-side confidence")
elif selected_data['sell'] > 75:
    st.error("📊 High sell-side pressure")
elif 45 <= selected_data['buy'] <= 55:
    st.warning("⚖️ Market Neutral / Low Confidence")

st.markdown("<hr><p style='text-align:center;color:gray;'>Educational analysis only • Not financial advice</p>", unsafe_allow_html=True)

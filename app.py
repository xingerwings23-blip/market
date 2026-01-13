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
# APPLY CSS SAF

import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime
import pytz  
import concurrent.futures

# --- 1. KONFIGURASI & CSS ---
st.set_page_config(page_title="Pro Swing & Scalper Radar", layout="wide", page_icon="📈")
wib_tz = pytz.timezone('Asia/Jakarta')
wib_now = datetime.now(wib_tz)

st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    .main-title { color: #38BDF8; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNGSI UTAMA ---
def clean_yf_dataframe(df):
    if df is None or df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    return df

def analyze_market_momentum(ticker):
    try:
        formatted_ticker = f"{ticker.strip().upper()}.JK"
        df = yf.download(formatted_ticker, period="3mo", interval="1d", progress=False)
        df = clean_yf_dataframe(df)
        if df is None or len(df) < 50: return None
        
        # Indikator
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # [NEW] VWAP & ATR
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last_price = float(df['Close'].iloc[-1])
        last_vwap = float(df['VWAP'].iloc[-1])
        last_atr = float(df['ATR'].iloc[-1])
        
        trend_status = "✅ Above VWAP" if last_price > last_vwap else "⚠️ Below VWAP"
        dynamic_sl = round(last_price - (2 * last_atr), 0)
        
        return {
            "Ticker": ticker,
            "Price": last_price,
            "VWAP": round(last_vwap, 2),
            "Trend Status": trend_status,
            "Dyn SL (2xATR)": dynamic_sl,
            "RSI": round(df['RSI'].iloc[-1], 2)
        }
    except: return None

# --- 3. RENDERING ---
st.markdown("<h1 class='main-title'>📈 Pro Swing & Scalper Radar</h1>", unsafe_allow_html=True)
saham_input = st.sidebar.multiselect("Pilih Saham:", ["BBCA", "BBRI", "TLKM", "MDKA", "GOTO", "ANTM"], default=["BBCA", "BBRI"])

if st.sidebar.button("Run Scan"):
    results = [analyze_market_momentum(s) for s in saham_input]
    df_result = pd.DataFrame([r for r in results if r is not None])
    
    # Fungsi Styling
    def style_table(row):
        styles = [''] * len(row)
        if "Above" in str(row['Trend Status']):
            styles[row.index.get_loc('Trend Status')] = 'color: #4ADE80; font-weight: bold;'
            styles[row.index.get_loc('VWAP')] = 'color: #4ADE80;'
        else:
            styles[row.index.get_loc('Trend Status')] = 'color: #F87171;'
            styles[row.index.get_loc('VWAP')] = 'color: #F87171;'
        return styles

    st.dataframe(df_result.style.apply(style_table, axis=1), use_container_width=True)

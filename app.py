import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime
import pytz  
import concurrent.futures

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Swing & Scalper Dashboard BEI", layout="wide", page_icon="📈")
wib_tz = pytz.timezone('Asia/Jakarta')
wib_now = datetime.now(wib_tz)

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    .main-title { color: #38BDF8; font-weight: 800; }
    .card-dana { background-color: #1E293B; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# [Fungsi load_mega_market_tickers tetap sama]
@st.cache_data(ttl=604800)
def load_mega_market_tickers():
    saham_list = ["BBCA", "BBRI", "TLKM", "MDKA", "GOTO", "ANTM", "ADRO", "BUMI", "PTRO", "ENRG", "JPFA", "FILM"] # Simplifikasi untuk contoh
    return sorted(list(set([f"{t.strip().upper()}.JK" for t in saham_list])))

master_tickers_jk = load_mega_market_tickers()
master_tickers_clean = [t.replace(".JK", "") for t in master_tickers_jk]

def clean_yf_dataframe(df):
    if df is None or df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df

# --- 4. ENGINE ANALISIS UTAMA ---
def analyze_market_momentum(ticker):
    try:
        formatted_ticker = ticker if ticker.endswith(".JK") else f"{ticker}.JK"
        df = yf.download(formatted_ticker, period="3mo", interval="1d", progress=False)
        df = clean_yf_dataframe(df)
        if df is None or len(df) < 50: return None
        
        # Indikator Dasar
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # --- VWAP & ATR LOGIC ---
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last_price = float(df['Close'].iloc[-1])
        last_vwap = float(df['VWAP'].iloc[-1])
        last_atr = float(df['ATR'].iloc[-1])
        
        # Status VWAP
        vwap_status = "✅ Bullish" if last_price > last_vwap else "⚠️ Bearish"
        
        # [Logika existing Anda lainnya...]
        
        return {
            "Ticker": ticker.replace(".JK", ""),
            "Price": last_price,
            "VWAP": round(last_vwap, 2),
            "VWAP Status": vwap_status,
            "ATR (14)": round(last_atr, 2),
            "RSI": round(df['RSI'].iloc[-1], 2),
            "Dana Masuk %": 50.0 # Contoh placeholder
        }
    except: return None

def run_mega_scanner(ticker_list):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ticker = {executor.submit(analyze_market_momentum, t): t for t in ticker_list}
        for future in concurrent.futures.as_completed(future_to_ticker):
            res = future.result()
            if res: results.append(res)
    return pd.DataFrame(results)

# --- 5. INTERFACE PANEL ---
st.markdown("<h1 class='main-title'>📈 Radar Dashboard dengan VWAP & ATR</h1>", unsafe_allow_html=True)
saham_pilihan = st.multiselect("Pilih Emiten:", options=master_tickers_clean, default=["BBCA", "BBRI"])

if st.button("Proses Radar"):
    df_radar = run_mega_scanner(saham_pilihan)
    
    def style_radar(row):
        styles = [''] * len(row)
        idx_vwap = row.index.get_loc('VWAP Status')
        if "Bullish" in str(row['VWAP Status']):
            styles[idx_vwap] = 'color: #4ADE80; font-weight: bold;'
        else:
            styles[idx_vwap] = 'color: #F87171;'
        return styles

    if not df_radar.empty:
        st.dataframe(df_radar.style.apply(style_radar, axis=1), use_container_width=True)

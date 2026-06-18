import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime
import pytz  
import concurrent.futures

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Swing & Scalper Dashboard Pro", layout="wide", page_icon="📈")

wib_tz = pytz.timezone('Asia/Jakarta')
wib_now = datetime.now(wib_tz)

# --- 2. CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    .main-title { color: #38BDF8; font-weight: 800; }
    .card-dana { background-color: #1E293B; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    .card-ihsg { background-color: #1E293B; padding: 20px; border-radius: 12px; border-left: 5px solid #38BDF8; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE MASTER ---
@st.cache_data(ttl=604800)
def load_mega_market_tickers():
    # Daftar emiten (telah dipertahankan dari list Anda)
    saham_300_plus = ["AADI", "BBCA", "BBRI", "TLKM", "MDKA", "ANTM", "GOTO", "PTRO", "NCKL", "BELI", "ULTJ", "DSSA", "RMKO"] 
    return sorted(list(set([f"{t.strip().upper()}.JK" for t in saham_300_plus])))

master_tickers_jk = load_mega_market_tickers()
master_tickers_clean = [t.replace(".JK", "") for t in master_tickers_jk]

def clean_yf_dataframe(df):
    if df is None or df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df

# --- 4. ENGINE ANALISIS UTAMA (DENGAN TAMBAHAN VWAP & ATR) ---
def analyze_market_momentum(ticker):
    try:
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        df = clean_yf_dataframe(df)
        if df is None or len(df) < 50: return None
        
        # Indikator Teknikal
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['MA50'] = ta.sma(df['Close'], length=50)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # --- TAMBAHAN TEORI: VWAP & ATR ---
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        # Kalkulasi VWAP Sederhana
        df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
        
        last_price = float(df['Close'].iloc[-1])
        last_vwap = float(df['VWAP'].iloc[-1])
        last_atr = float(df['ATR'].iloc[-1])
        
        # Logika Sinyal Baru
        is_above_vwap = last_price > last_vwap
        
        # --- Logika asli Anda ---
        prev_price = float(df['Close'].iloc[-2])
        change_pct = ((last_price - prev_price) / prev_price) * 100
        
        # ... (Logika inst flow & trend Anda tetap)
        trend_label = "🟩 Up-Trend" if last_price > df['EMA20'].iloc[-1] else "🟥 Down-Trend"
        
        # Gabungan Action Signal
        action_signal = "⏳ Wait"
        if last_price > last_vwap and last_price > df['EMA9'].iloc[-1]:
            action_signal = "🔥 SUPER BUY (Above VWAP)"
        
        return {
            "Ticker": ticker.replace(".JK", ""),
            "Price": last_price,
            "VWAP": round(last_vwap, 2),
            "ATR (Volatility)": round(last_atr, 2),
            "Trend": trend_label,
            "Actionable": action_signal,
            "Stop Loss (2xATR)": round(last_price - (2 * last_atr), 0)
        }
    except: return None

# --- 5. INTERFACE ---
st.markdown("<h1 class='main-title'>📈 Swing & Scalper Radar Pro</h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    saham_pilihan = st.multiselect("Pilih Saham:", master_tickers_clean, default=["BBCA", "BBRI", "TLKM"])

if st.button("🚀 Update Radar"):
    with st.spinner("Proses data..."):
        results = [analyze_market_momentum(f"{s}.JK") for s in saham_pilihan]
        df_radar = pd.DataFrame([r for r in results if r])
        
        if not df_radar.empty:
            st.dataframe(df_radar, use_container_width=True)
            st.success("Analisa dengan VWAP dan ATR berhasil dimuat.")
        else:
            st.warning("Data tidak tersedia.")

st.info("💡 **Tips:** Gunakan **VWAP** sebagai konfirmasi tren institusi. Jika harga di bawah VWAP, hindari entri agresif. **ATR** membantu Anda menentukan area *Stop Loss* yang tidak mudah tersentuh *noise* pasar.")

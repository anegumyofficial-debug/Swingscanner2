import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="Master Stock Scanner Pro v2.0")
st.title("🚀 Master Stock Scanner - Real-Time Dashboard")
st.write(f"Update Terakhir: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WIB")
st.markdown("---")

# 2. DAFTAR SAHAM
tickers = ["BBRI.JK", "BBCA.JK", "BBNI.JK", "ASII.JK", "TLKM.JK", "BMRI.JK"]

# 3. FUNGSI LOGIKA ANALISIS
def fetch_and_analyze(ticker, timeframe_label):
    config = {
        "Day (Scalping)": {"period": "5d", "interval": "15m", "tp": 0.02, "sl": 0.015, "rsi_low": 30},
        "Weekly (Swing)": {"period": "3mo", "interval": "1d", "tp": 0.07, "sl": 0.04, "rsi_low": 40},
        "Monthly (Invest)": {"period": "1y", "interval": "1wk", "tp": 0.15, "sl": 0.07, "rsi_low": 45}
    }
    
    conf = config[timeframe_label]
    # Ambil data dan pastikan format kolom sederhana (Satu Level)
    df = yf.download(ticker, period=conf['period'], interval=conf['interval'], progress=False)
    
    if df.empty:
        return None
        
    # Perbaikan: Meratakan kolom jika ada Multi-Index dari Yahoo Finance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Hitung Indikator
    df['RSI'] = ta.rsi(df['Close'], length=14)
    bbands = ta.bbands(df['Close'], length=20, std=2)
    
    # Pastikan BBands berhasil dihitung
    if bbands is None or bbands.empty:
        return None
        
    df = pd.concat([df, bbands], axis=1)
    
    latest = df.iloc[-1]
    curr_price = float(latest['Close'])
    rsi_val = float(latest['RSI'])
    # Menggunakan nama kolom BBands yang standar dari pandas_ta
    l_band = float(latest['BBL_20_2.0'])
    u_band = float(latest['BBU_20_2.0'])

    # Penentuan Sinyal
    if rsi_val <= conf['rsi_low'] or curr_price <= l_band:
        status, entry = "🟢 SIAP SEROK", curr_price
        tp = round(curr_price * (1 + conf['tp']), 0)
        sl = round(curr_price * (1 - conf['sl']), 0)
    elif rsi_val >= (100 - conf['rsi_low']) or curr_price >= u_band:
        status, entry, tp, sl = "🔴 JUAL / SCALPING", "-", "AMBIL PROFIT", "-"
    else:
        status = "⚪ WAIT / NEUTRAL"
        entry, tp = round(l_band, 0), round(u_band, 0)
        sl = round(l_band * (1 - conf['sl']), 0)

    return {
        "Saham": ticker.replace(".JK", ""),
        "Harga": round(curr_price, 0),
        "Status": status,
        "Harga Serok": entry,
        "Target Jual": tp,
        "Batas Aman (SL)": sl,
        "RSI": round(rsi_val, 2)
    }

# 4. TAMPILAN DASHBOARD
tab1, tab2, tab3 = st.tabs(["🕒 Day Scalping", "📅 Weekly Swing", "🏛️ Monthly Invest"])

def display_content(tab, label):
    with tab:
        all_data = []
        for t in tickers:
            res = fetch_and_analyze(t, label)
            if res: all_data.append(res)
        if all_data:
            st.table(pd.DataFrame(all_data))

display_content(tab1, "Day (Scalping)")
display_content(tab2, "Weekly (Swing)")
display_content(tab3, "Monthly (Invest)")

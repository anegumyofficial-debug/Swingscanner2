import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="Master Stock Scanner Pro v2.0")
st.title("🚀 Master Stock Scanner - Dashboard")
st.write(f"Update Terakhir: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WIB")
st.markdown("---")

# 2. SENARAI SAHAM
tickers = ["BBRI.JK", "BBCA.JK", "BBNI.JK", "ASII.JK", "TLKM.JK", "BMRI.JK"]

# 3. FUNGSI ANALISIS (VERSI SELALU MUNCUL)
def fetch_and_analyze(ticker, timeframe_label):
    config = {
        "Day (Scalping)": {"period": "1mo", "interval": "1h", "tp": 0.02, "sl": 0.015, "rsi_low": 30},
        "Weekly (Swing)": {"period": "6mo", "interval": "1d", "tp": 0.07, "sl": 0.04, "rsi_low": 40},
        "Monthly (Invest)": {"period": "2y", "interval": "1wk", "tp": 0.15, "sl": 0.07, "rsi_low": 45}
    }
    
    conf = config[timeframe_label]
    
    # Ambil data dengan tempoh lebih lama supaya tidak kosong
    df = yf.download(ticker, period=conf['period'], interval=conf['interval'], progress=False, auto_adjust=True)
    
    if df is None or df.empty:
        return None
        
    # Baiki Multi-Index kolom
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Kira Indikator
    df['RSI'] = ta.rsi(df['Close'], length=14)
    bbands = ta.bbands(df['Close'], length=20, std=2)
    
    if bbands is None or bbands.empty:
        return None
        
    df = pd.concat([df, bbands], axis=1)
    
    # PENTING: Ambil data terakhir yang mempunyai nilai (bukan NaN)
    df_valid = df.dropna(subset=['Close', 'RSI'])
    if df_valid.empty:
        return None
        
    latest = df_valid.iloc[-1]
    
    # Cari nama kolom Bollinger secara automatik
    col_bbl = [c for c in df_valid.columns if 'BBL' in c]
    col_bbu = [c for c in df_valid.columns if 'BBU' in c]
    
    curr_price = float(latest['Close'])
    rsi_val = float(latest['RSI'])
    l_band = float(latest[col_bbl])
    u_band = float(latest[col_bbu])

    # Logika Isyarat & Warna
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

# 4. GAYA JADUAL BERWARNA
def style_row(val):
    if "SIAP SEROK" in str(val):
        return 'background-color: #d4edda; color: #155724; font-weight: bold'
    if "JUAL" in str(val):
        return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
    return ''

# 5. PAPARAN TAB
tab1, tab2, tab3 = st.tabs(["🕒 Day Scalping", "📅 Weekly Swing", "🏛️ Monthly Invest"])

def render_table(tab, label):
    with tab:
        data_list = []
        for t in tickers:
            try:
                res = fetch_and_analyze(t, label)
                if res: data_list.append(res)
            except:
                continue
        
        if data_list:
            df_final = pd.DataFrame(data_list)
            # Paparkan dengan warna hijau/merah
            st.dataframe(df_final.style.applymap(style_row, subset=['Status']), use_container_width=True)
        else:
            st.warning(f"Sistem sedang menunggu data dari bursa untuk {label}...")

render_table(tab1, "Day (Scalping)")
render_table(tab2, "Weekly (Swing)")
render_table(tab3, "Monthly (Invest)")

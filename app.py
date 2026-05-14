import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="Master Stock Scanner Pro v3.0")

# Custom CSS untuk mempercantik tampilan tabel dan bar
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 10px 20px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Master Stock Scanner - Pro Dashboard")
st.write(f"Update Terakhir: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WIB")
st.markdown("---")

# 2. DAFTAR SAHAM
tickers = ["BBRI.JK", "BBCA.JK", "BBNI.JK", "ASII.JK", "TLKM.JK", "BMRI.JK"]

# 3. FUNGSI ANALISIS LOGIKA
def fetch_and_analyze(ticker, timeframe_label):
    config = {
        "Day (Scalping)": {"period": "1mo", "interval": "1h", "tp": 0.02, "sl": 0.015, "rsi_low": 30},
        "Weekly (Swing)": {"period": "6mo", "interval": "1d", "tp": 0.07, "sl": 0.04, "rsi_low": 40},
        "Monthly (Invest)": {"period": "2y", "interval": "1wk", "tp": 0.15, "sl": 0.07, "rsi_low": 45}
    }
    
    conf = config[timeframe_label]
    df = yf.download(ticker, period=conf['period'], interval=conf['interval'], progress=False, auto_adjust=True)
    
    if df is None or df.empty:
        return None
        
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['RSI'] = ta.rsi(df['Close'], length=14)
    bbands = ta.bbands(df['Close'], length=20, std=2)
    
    if bbands is None or bbands.empty:
        return None
        
    df = pd.concat([df, bbands], axis=1).dropna(subset=['Close', 'RSI'])
    if df.empty: return None
        
    latest = df.iloc[-1]
    col_bbl = [c for c in df.columns if 'BBL' in c]
    col_bbu = [c for c in df.columns if 'BBU' in c]
    
    curr_price = float(latest['Close'])
    rsi_val = float(latest['RSI'])
    l_band = float(latest[col_bbl])
    u_band = float(latest[col_bbu])

    if rsi_val <= conf['rsi_low'] or curr_price <= l_band:
        status, color_label = "🟢 SIAP SEROK", "buy"
        entry, tp, sl = curr_price, round(curr_price * (1 + conf['tp']), 0), round(curr_price * (1 - conf['sl']), 0)
    elif rsi_val >= (100 - conf['rsi_low']) or curr_price >= u_band:
        status, color_label = "🔴 JUAL / PROFIT", "sell"
        entry, tp, sl = "-", "AMBIL PROFIT", "-"
    else:
        status, color_label = "⚪ WAIT / NEUTRAL", "neutral"
        entry, tp, sl = round(l_band, 0), round(u_band, 0), round(l_band * (1 - conf['sl']), 0)

    return {
        "Saham": ticker.replace(".JK", ""),
        "Harga": round(curr_price, 0),
        "Status": status,
        "Entry": entry,
        "TP": tp,
        "SL": sl,
        "RSI": round(rsi_val, 2),
        "label": color_label
    }

# 4. TAMPILAN DASHBOARD DENGAN TAB DAN BAR BARU
def style_status(val):
    if "SIAP SEROK" in str(val): return 'background-color: #d4edda; color: #155724; font-weight: bold'
    if "JUAL" in str(val): return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
    return ''

tab1, tab2, tab3 = st.tabs(["🕒 Day Scalping", "📅 Weekly Swing", "🏛️ Monthly Invest"])

def render_dashboard(tab, label):
    with tab:
        all_results = []
        for t in tickers:
            try:
                res = fetch_and_analyze(t, label)
                if res: all_results.append(res)
            except: continue
        
        if all_results:
            df = pd.DataFrame(all_results)
            
            # --- BAR BARU (SUMMARY METRICS) ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Saham", len(tickers))
            c2.metric("Siap Serok (Buy)", len(df[df['label'] == 'buy']), delta_color="normal")
            c3.metric("Jual (Sell)", len(df[df['label'] == 'sell']), delta_color="inverse")
            c4.metric("Neutral", len(df[df['label'] == 'neutral']))
            
            st.markdown("### Detail Rekomendasi")
            # Tampilkan Tabel Berwarna
            display_df = df.drop(columns=['label'])
            st.dataframe(display_df.style.applymap(style_status, subset=['Status']), use_container_width=True)
        else:
            st.info(f"Data {label} belum tersedia. Silakan tunggu bursa buka.")

render_dashboard(tab1, "Day (Scalping)")
render_dashboard(tab2, "Weekly (Swing)")
render_dashboard(tab3, "Monthly (Invest)")

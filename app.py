import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="Master Stock Scanner Pro v2.0")

st.title("🚀 Master Stock Scanner - Real-Time Dashboard")
st.write(f"Update Terakhir: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WIB")
st.markdown("---")

# 2. DAFTAR SAHAM (Bisa Anda tambah sesuai keinginan)
tickers = ["BBRI.JK", "BBCA.JK", "BBNI.JK", "ASII.JK", "TLKM.JK", "BMRI.JK"]

# 3. FUNGSI LOGIKA ANALISIS (MESIN SINYAL)
def fetch_and_analyze(ticker, timeframe_label):
    # Penyesuaian Interval berdasarkan Kategori
    config = {
        "Day (Scalping)": {"period": "5d", "interval": "15m", "tp": 0.02, "sl": 0.015, "rsi_low": 30},
        "Weekly (Swing)": {"period": "3mo", "interval": "1d", "tp": 0.07, "sl": 0.04, "rsi_low": 40},
        "Monthly (Invest)": {"period": "1y", "interval": "1wk", "tp": 0.15, "sl": 0.07, "rsi_low": 45}
    }
    
    set = config[timeframe_label]
    df = yf.download(ticker, period=set['period'], interval=set['interval'], progress=False)
    
    if df.empty:
        return None

    # Hitung Indikator Teknikal
    df['RSI'] = ta.rsi(df['Close'], length=14)
    bbands = ta.bbands(df['Close'], length=20, std=2)
    df = pd.concat([df, bbands], axis=1)
    
    latest = df.iloc[-1]
    curr_price = round(latest['Close'], 0)
    rsi_val = latest['RSI']
    l_band = latest['BBL_20_2.0']
    u_band = latest['BBU_20_2.0']

    # Penentuan Sinyal & Trading Plan
    if rsi_val <= set['rsi_low'] or curr_price <= l_band:
        status = "🟢 SIAP SEROK"
        entry = curr_price
        tp = round(curr_price * (1 + set['tp']), 0)
        sl = round(curr_price * (1 - set['sl']), 0)
    elif rsi_val >= (100 - set['rsi_low']) or curr_price >= u_band:
        status = "🔴 JUAL / SCALPING"
        entry = "-"
        tp = "AMBIL PROFIT"
        sl = "-"
    else:
        status = "⚪ WAIT / NEUTRAL"
        entry = round(l_band, 0)
        tp = round(u_band, 0)
        sl = round(l_band * (1 - set['sl']), 0)

    return {
        "Saham": ticker.replace(".JK", ""),
        "Harga Saat Ini": curr_price,
        "Status": status,
        "Harga Serok (Entry)": entry,
        "Target Jual (TP)": tp,
        "Batas Aman (SL)": sl,
        "Power (RSI)": round(rsi_val, 2)
    }

# 4. TAMPILAN DASHBOARD (TAB SYSTEM)
tab1, tab2, tab3 = st.tabs(["🕒 Day Scalping (15M)", "📅 Weekly Swing (Daily)", "🏛️ Monthly Invest (Weekly)"])

def display_content(tab, label):
    with tab:
        st.subheader(f"Rekomendasi Strategi {label}")
        all_data = []
        for t in tickers:
            res = fetch_and_analyze(t, label)
            if res:
                all_data.append(res)
        
        # Tampilkan Tabel
        report_df = pd.DataFrame(all_data)
        
        # Styling Tabel agar warna terlihat jelas
        def color_status(val):
            if "SEROK" in val: color = '#d4edda' # Hijau muda
            elif "JUAL" in val: color = '#f8d7da' # Merah muda
            else: color = 'white'
            return f'background-color: {color}'

        st.table(report_df)

# Eksekusi Tab
display_content(tab1, "Day (Scalping)")
display_content(tab2, "Weekly (Swing)")
display_content(tab3, "Monthly (Invest)")

# 5. EDUKASI TRADING PLAN
st.markdown("---")
st.info("""
**Cara Membaca Dashboard:**
1. **Day Scalping**: Gunakan untuk jual-beli cepat (hitung jam atau hari yang sama).
2. **Weekly Swing**: Gunakan jika Anda ingin menyimpan saham selama 3-7 hari.
3. **Monthly Invest**: Fokus pada akumulasi harga murah untuk jangka panjang (1 bulan+).
4. **Harga Serok**: Angka ideal untuk mulai memasang antrean beli (Buy Limit).
""")
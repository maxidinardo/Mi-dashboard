import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

st.set_page_config(page_title="QTUM Institutional Terminal", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetricValue"] { font-size: 20px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Terminal Avanzado de Inversión: QTUM")

# --- SIDEBAR: GESTIÓN DE CARTERA ---
st.sidebar.header("💼 Tu Cartera (DCA)")
acciones = st.sidebar.number_input("Títulos Poseídos", min_value=0.0, value=10.0, step=1.0)
costo_prom = st.sidebar.number_input("Costo Promedio (USD)", min_value=0.0, value=148.78, step=0.1)

# --- DESCARGA DE DATOS ---
@st.cache_data(ttl=1800)
def cargar_datos_completos():
    ticker = yf.Ticker("QTUM")
    hist_w = ticker.history(period="3y", interval="1wk")
    hist_d = ticker.history(period="1y", interval="1d")
    info = ticker.info
    return hist_w, hist_d, info

try:
    df_w, df_d, info = cargar_datos_completos()
    precio_actual = df_d["Close"].iloc[-1]

    # --- CÁLCULOS TÉCNICOS ---
    # SMAs (Diarias y Semanales)
    df_d['SMA_50'] = df_d['Close'].rolling(window=50).mean()
    df_d['SMA_100'] = df_d['Close'].rolling(window=100).mean()
    df_d['SMA_200'] = df_d['Close'].rolling(window=200).mean()

    sma50 = df_d['SMA_50'].iloc[-1]
    sma100 = df_d['SMA_100'].iloc[-1]
    sma200 = df_d['SMA_200'].iloc[-1]

    # RSI (14 Semanal)
    delta_w = df_w['Close'].diff()
    gain = (delta_w.where(delta_w > 0, 0)).rolling(14).mean()
    loss = (-delta_w.where(delta_w < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df_w['RSI'] = 100 - (100 / (1 + rs))
    rsi_val = df_w['RSI'].iloc[-1]
    rsi_prev = df_w['RSI'].iloc[-2]

    # MACD (Semanal)
    ema12 = df_w['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df_w['Close'].ewm(span=26, adjust=False).mean()
    df_w['MACD'] = ema12 - ema26
    df_w['Signal'] = df_w['MACD'].ewm(span=9, adjust=False).mean()
    df_w['Hist'] = df_w['MACD'] - df_w['Signal']
    macd_val = df_w['MACD'].iloc[-1]
    sig_val = df_w['Signal'].iloc[-1]

    # Soportes y Resistencias (Pivot 52 sem)
    resistencia_52w = df_d['High'].max()
    soporte_52w = df_d['Low'].min()
    volumen_prom_20d = df_d['Volume'].tail(20).mean()
    volumen_hoy = df_d['Volume'].iloc[-1]

    # Detección de Divergencia RSI / Precio (Muestra rápida en ultimas 10 semanas)
    precio_min_rec = df_w['Close'].tail(8).iloc[-1] < df_w['Close'].tail(8).iloc[0]
    rsi_max_rec = df_w['RSI'].tail(8).iloc[-1] > df_w['RSI'].tail(8).iloc[0]
    divergencia_alcista = precio_min_rec and rsi_max_rec

    precio_max_rec = df_w['Close'].tail(8).iloc[-1] > df_w['Close'].tail(8).iloc[0]
    rsi_min_rec = df_w['RSI'].tail(8).iloc[-1] < df_w['RSI'].tail(8).iloc[0]
    divergencia_bajista = precio_max_rec and rsi_min_rec

    # --- SECCIÓN 1: FUNDAMENTALES Y DATOS DEL ETF ---
    st.subheader("🏢 Fundamentales y Estructura del ETF")
    f1, f2, f3, f4 = st.columns(4)
    aum = info.get('totalAssets', 'N/A')
    pe_ratio = info.get('trailingPE', 'N/A')
    div_yield = info.get('yield', 0.0)
    
    f1.metric("Activos Totales (AUM)", f"${aum:,.0f}" if isinstance(aum, (int, float)) else "N/A")
    f2.metric("P/E Promedio Cartera", f"{pe_ratio:.2f}x" if isinstance(pe_ratio, (int, float)) else "N/A")
    f3.metric("Rend. Dividendos", f"{div_yield*100:.2f}%" if isinstance(div_yield, (int, float)) else "0.00%")
    f4.metric("Volumen Diario vs Prom.", f"{volumen_hoy/1_000:,.0f}k", delta=f"{((volumen_hoy - volumen_prom_20d)/volumen_prom_20d)*100:.1f}%")

    st.markdown("---")

    # --- SECCIÓN 2: TÉCNICO Y MEDIAS MÓVILES ---
    st.subheader("📊 Indicadores Técnicos Clave (Diario / Semanal)")
    t1, t2, t3, t4, t5 = st.columns(5)
    t1.metric("Precio Actual", f"${precio_actual:.2f}")
    t2.metric("SMA 50 Días", f"${sma50:.2f}", delta=f"{((precio_actual-sma50)/sma50)*100:.1f}%")
    t3.metric("SMA 200 Días", f"${sma200:.2f}", delta=f"{((precio_actual-sma200)/sma200)*100:.1f}%")
    t4.metric("RSI (14W)", f"{rsi_val:.1f}")
    t5.metric("MACD (Hist)", f"{df_w['Hist'].iloc[-1]:.2f}")

    # --- SECCIÓN 3: SEMÁFORO TÁCTICO CON DIVERGENCIAS ---
    st.subheader("🚥 Semáforo Táctico y Alerta de Divergencias")
    
    if divergencia_alcista:
        st.info("🔍 **DIVERGENCIA ALCISTA DETECTADA:** El precio marca mínimos locales pero el RSI muestra fuerza al alza. Posible suelo / rebote inminente.")
    elif divergencia_bajista:
        st.warning("⚠️ **DIVERGENCIA BAJISTA DETECTADA:** El precio hace nuevos máximos pero el RSI pierde fuerza. Cautela con compras agresivas.")

    if precio_actual >= sma50 and rsi_val < 70:
        st.success("🟢 **VERDE — Tendencia Alcista Sólida:** Precio por encima de SMA 50. RSI en zona saludable. **Estrategia:** Continuar compras DCA programadas.")
    elif precio_actual < sma50 or rsi_val >= 70:
        st.warning("🟡 **AMARILLO — Precaución / Oportunidad de Retroceso:** Precio testeando mediano plazo o RSI sobrecomprado. **Estrategia:** Evaluar compras si toca la SMA 200.")
    else:
        st.error("🔴 **ROJO — Alerta:** Ruptura de soportes estructurales (SMA 200). **Estrategia:** Pausar nuevas entradas y reevaluar.")

    st.markdown("---")

    # --- SECCIÓN 4: GRÁFICO COMPLETO CON MACD & RSI ---
    st.subheader("📈 Gráfico Técnico Interactivo (Velas, SMAs, MACD y RSI)")

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

    # Precio y SMAs
    fig.add_trace(go.Candlestick(x=df_d.index, open=df_d['Open'], high=df_d['High'], low=df_d['Low'], close=df_d['Close'], name="Precio"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_d.index, y=df_d['SMA_50'], line=dict(color='#FF9900', width=1.5), name="SMA 50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_d.index, y=df_d['SMA_200'], line=dict(color='#0066FF', width=1.5), name="SMA 200"), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=df_w.index, y=df_w['RSI'], line=dict(color='#AB63FA', width=1.5), name="RSI (14)"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # MACD
    fig.add_trace(go.Scatter(x=df_w.index, y=df_w['MACD'], line=dict(color='#00FFCC', width=1), name="MACD"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df_w.index, y=df_w['Signal'], line=dict(color='#FF0055', width=1), name="Signal"), row=3, col=1)

    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Actualizando métricas... (Detalle: {e})")

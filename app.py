import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(page_title="Multi-Asset Terminal", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetricValue"] { font-size: 20px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("💼 Terminal Financiero & Análisis Multiactivo")

# --- CONFIGURACIÓN DE MI CARTERA (TABLA EDITABLE EN SIDEBAR) ---
st.sidebar.header("📝 Configuración de Cartera")

# Datos por defecto (Puedes modificar o agregar filas directamente en la app)
cartera_inicial = pd.DataFrame([
    {"Ticker": "QTUM", "Cantidad": 10.0, "Costo_Promedio": 148.78},
    {"Ticker": "NVDA", "Cantidad": 5.0, "Costo_Promedio": 120.50},
    {"Ticker": "AAPL", "Cantidad": 8.0, "Costo_Promedio": 180.00},
    {"Ticker": "MSFT", "Cantidad": 3.0, "Costo_Promedio": 400.00}
])

st.sidebar.caption("Edita tu cartera en la siguiente tabla:")
cartera_df = st.sidebar.data_editor(
    cartera_inicial, 
    num_rows="dynamic",
    column_config={
        "Ticker": st.column_config.TextColumn("Ticker", help="Ej: QTUM, NVDA, AAPL"),
        "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.0, format="%.2f"),
        "Costo_Promedio": st.column_config.NumberColumn("Costo Prom. ($)", min_value=0.0, format="$%.2f")
    },
    use_container_width=True
)

# SELECCIÓN DE ACTIVO PARA ANÁLISIS DETALLADO
st.sidebar.markdown("---")
lista_tickers = cartera_df["Ticker"].dropna().unique().tolist()
ticker_seleccionado = st.sidebar.selectbox("🎯 Selecciona Activo a Analizar:", lista_tickers)

# --- DESCARGA DE DATOS MULTIACTIVO ---
@st.cache_data(ttl=1800)
def cargar_datos_activo(symbol):
    ticker = yf.Ticker(symbol)
    hist_w = ticker.history(period="3y", interval="1wk")
    hist_d = ticker.history(period="1y", interval="1d")
    info = ticker.info
    return hist_w, hist_d, info

try:
    # Datos de la posición seleccionada
    posicion_actual = cartera_df[cartera_df["Ticker"] == ticker_seleccionado].iloc[0]
    cant = posicion_actual["Cantidad"]
    costo_prom = posicion_actual["Costo_Promedio"]

    df_w, df_d, info = cargar_datos_activo(ticker_seleccionado)
    precio_actual = df_d["Close"].iloc[-1]

    # --- SECCIÓN 1: RENDIMIENTO INDIVIDUAL Y POSICIÓN ---
    inversion_total = cant * costo_prom
    valor_actual = cant * precio_actual
    ganancia_usd = valor_actual - inversion_total
    ganancia_pct = (ganancia_usd / inversion_total * 100) if inversion_total > 0 else 0

    st.subheader(f"📊 Tu Posición en {ticker_seleccionado}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio en Vivo", f"${precio_actual:.2f}")
    c2.metric("Valor Total Posición", f"${valor_actual:,.2f}")
    c3.metric("Ganancia / Pérdida", f"${ganancia_usd:,.2f}", delta=f"{ganancia_pct:.2f}%")
    c4.metric("Costo Prom. / Cantidad", f"${costo_prom:.2f}", delta=f"{cant:.1f} Acc.")

    st.markdown("---")

    # --- INDICADORES TÉCNICOS ---
    # SMAs (Diarias)
    df_d['SMA_50'] = df_d['Close'].rolling(50).mean()
    df_d['SMA_200'] = df_d['Close'].rolling(200).mean()
    sma50 = df_d['SMA_50'].iloc[-1]
    sma200 = df_d['SMA_200'].iloc[-1]

    # RSI (14 Semanal)
    delta_w = df_w['Close'].diff()
    gain = (delta_w.where(delta_w > 0, 0)).rolling(14).mean()
    loss = (-delta_w.where(delta_w < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df_w['RSI'] = 100 - (100 / (1 + rs))
    rsi_val = df_w['RSI'].iloc[-1]

    # MACD (Semanal)
    ema12 = df_w['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df_w['Close'].ewm(span=26, adjust=False).mean()
    df_w['MACD'] = ema12 - ema26
    df_w['Signal'] = df_w['MACD'].ewm(span=9, adjust=False).mean()

    # DETECCIÓN DE DIVERGENCIAS
    precio_min_rec = df_w['Close'].tail(8).iloc[-1] < df_w['Close'].tail(8).iloc[0]
    rsi_max_rec = df_w['RSI'].tail(8).iloc[-1] > df_w['RSI'].tail(8).iloc[0]
    divergencia_alcista = precio_min_rec and rsi_max_rec

    precio_max_rec = df_w['Close'].tail(8).iloc[-1] > df_w['Close'].tail(8).iloc[0]
    rsi_min_rec = df_w['RSI'].tail(8).iloc[-1] < df_w['RSI'].tail(8).iloc[0]
    divergencia_bajista = precio_max_rec and rsi_min_rec

    # --- SECCIÓN 2: SEMÁFORO Y DIVERGENCIAS ---
    st.subheader(f"🚥 Semáforo Táctico: {ticker_seleccionado}")

    if divergencia_alcista:
        st.info("🔍 **DIVERGENCIA ALCISTA DETECTADA:** El precio marca mínimos pero el RSI sube. Zona probable de rebote/suelo.")
    elif divergencia_bajista:
        st.warning("⚠️ **DIVERGENCIA BAJISTA DETECTADA:** El precio marca máximos pero el RSI baja. Pérdida de impulso comprador.")

    if precio_actual >= sma50 and rsi_val < 70:
        st.success(f"🟢 **VERDE — Tendencia Alcista Sólida en {ticker_seleccionado}:** Cotiza sobre SMA 50. Continuar plan de compras (DCA).")
    elif precio_actual < sma50 or rsi_val >= 70:
        st.warning(f"🟡 **AMARILLO — Precaución / Zona de Soporte:** Testeando soportes o sobrecomprado. Evaluar compras cerca de SMA 200.")
    else:
        st.error(f"🔴 **ROJO — Alerta:** Ruptura de SMA 200. Pausar acumulación.")

    st.markdown("---")

    # --- SECCIÓN 3: GRÁFICO TÉCNICO INTERACTIVO ---
    st.subheader("📈 Gráfico de Velas, SMAs, RSI y MACD")
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

    fig.add_trace(go.Candlestick(x=df_d.index, open=df_d['Open'], high=df_d['High'], low=df_d['Low'], close=df_d['Close'], name="Precio"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_d.index, y=df_d['SMA_50'], line=dict(color='#FF9900', width=1.5), name="SMA 50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_d.index, y=df_d['SMA_200'], line=dict(color='#0066FF', width=1.5), name="SMA 200"), row=1, col=1)

    fig.add_trace(go.Scatter(x=df_w.index, y=df_w['RSI'], line=dict(color='#AB63FA', width=1.5), name="RSI"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.add_trace(go.Scatter(x=df_w.index, y=df_w['MACD'], line=dict(color='#00FFCC', width=1), name="MACD"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df_w.index, y=df_w['Signal'], line=dict(color='#FF0055', width=1), name="Signal"), row=3, col=1)

    fig.update_layout(template="plotly_dark", height=580, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Selecciona un ticker válido o verifica los datos ingresados en la tabla. (Detalle: {e})")

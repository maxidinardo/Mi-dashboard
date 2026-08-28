import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# Configuración móvil / pantalla completa
st.set_page_config(page_title="QTUM Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Estilos visuales para interfaz limpia en celular
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Panel QTUM")

# Obtener datos de mercado
@st.cache_data(ttl=3600)
def cargar_datos():
    ticker = yf.Ticker("QTUM")
    hist = ticker.history(period="1y", interval="1wk")
    return hist

try:
    df = cargar_datos()
    precio_actual = df["Close"].iloc[-1]
    max_52 = df["High"].max()
    min_52 = df["Low"].min()

    # Métricas destacadas
    col1, col2 = st.columns(2)
    col1.metric("Precio Actual", f"${precio_actual:.2f} USD")
    col2.metric("Máximo 52 Sem.", f"${max_52:.2f} USD")

    st.markdown("---")

    # Semáforo de Inversión
    st.subheader("🚥 Semáforo Semanal")
    if precio_actual >= 140.0:
        st.success("🟢 **VERDE — Tendencia Alcista Sana**\nMantener posición / Continuar compras (DCA).")
    elif 128.0 <= precio_actual < 140.0:
        st.warning("🟡 **AMARILLO — Zona de Soporte**\nRetroceso técnico. Oportunidad de recarga con descuento.")
    else:
        st.error("🔴 **ROJO — Alerta Estructural**\nCierre bajo $128 USD. Pausar compras y reevaluar.")

    st.markdown("---")

    # Gráfico adaptado a pantalla de celular
    st.subheader("📈 Gráfico Semanal")
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Precio"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='#FF9900', width=1.5), name="EMA 20W"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#0066FF', width=1.5), name="EMA 50W"))

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=400,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error("Cargando datos del mercado... Por favor recarga en unos segundos.")

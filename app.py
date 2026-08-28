import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

st.set_page_config(page_title="Terminal Pro Multiactivo", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetricValue"] { font-size: 19px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("💼 Terminal de Inversión Avanzado & Semáforo Modular")

# --- SIDEBAR: CARTERA Y CONFIGURACIÓN ---
st.sidebar.header("📝 Gestión de Cartera")

cartera_inicial = pd.DataFrame([
    {"Ticker": "QTUM", "Cantidad": 10.0, "Costo_Promedio": 148.78, "Stop_Loss": 130.00},
    {"Ticker": "NVDA", "Cantidad": 5.0, "Costo_Promedio": 120.50, "Stop_Loss": 105.00},
    {"Ticker": "AAPL", "Cantidad": 8.0, "Costo_Promedio": 180.00, "Stop_Loss": 165.00}
])

cartera_df = st.sidebar.data_editor(
    cartera_inicial, 
    num_rows="dynamic",
    column_config={
        "Ticker": st.column_config.TextColumn("Ticker"),
        "Cantidad": st.column_config.NumberColumn("Cant.", min_value=0.0, format="%.2f"),
        "Costo_Promedio": st.column_config.NumberColumn("Costo Prom. ($)", min_value=0.0, format="$%.2f"),
        "Stop_Loss": st.column_config.NumberColumn("Stop Loss ($)", min_value=0.0, format="$%.2f")
    },
    use_container_width=True
)

st.sidebar.markdown("---")
lista_tickers = cartera_df["Ticker"].dropna().unique().tolist()
ticker_sel = st.sidebar.selectbox("🎯 Selecciona Activo:", lista_tickers)

# --- DESCARGA DE DATOS Y BÚSQUEDA DE SPY ---
@st.cache_data(ttl=1800)
def cargar_datos_completos(symbol):
    tk = yf.Ticker(symbol)
    hist_w = tk.history(period="3y", interval="1wk")
    hist_d = tk.history(period="1y", interval="1d")
    info = tk.info
    financials = tk.financials
    
    # Datos de SPY para comparación
    spy = yf.Ticker("SPY").history(period="1y", interval="1d")['Close']
    return hist_w, hist_d, info, financials, spy

try:
    posicion = cartera_df[cartera_df["Ticker"] == ticker_sel].iloc[0]
    cant = posicion["Cantidad"]
    costo_prom = posicion["Costo_Promedio"]
    stop_loss_val = posicion["Stop_Loss"]

    df_w, df_d, info, financials, spy_close = cargar_datos_completos(ticker_sel)
    precio_actual = df_d["Close"].iloc[-1]
    es_etf = info.get('quoteType', '').upper() == 'ETF'

    # --- INDICADORES TÉCNICOS ---
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

    # MACD
    ema12 = df_w['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df_w['Close'].ewm(span=26, adjust=False).mean()
    df_w['MACD'] = ema12 - ema26
    df_w['Signal'] = df_w['MACD'].ewm(span=9, adjust=False).mean()

    # DIVERGENCIAS
    p_min_rec = df_w['Close'].tail(8).iloc[-1] < df_w['Close'].tail(8).iloc[0]
    r_max_rec = df_w['RSI'].tail(8).iloc[-1] > df_w['RSI'].tail(8).iloc[0]
    div_alcista = p_min_rec and r_max_rec

    p_max_rec = df_w['Close'].tail(8).iloc[-1] > df_w['Close'].tail(8).iloc[0]
    r_min_rec = df_w['RSI'].tail(8).iloc[-1] < df_w['RSI'].tail(8).iloc[0]
    div_bajista = p_max_rec and r_min_rec

    # --- RESUMEN DE POSICIÓN ---
    inv_total = cant * costo_prom
    val_act = cant * precio_actual
    pnl_usd = val_act - inv_total
    pnl_pct = (pnl_usd / inv_total * 100) if inv_total > 0 else 0

    st.subheader(f"📊 Rendimiento Posición: {ticker_sel}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio Actual", f"${precio_actual:.2f}")
    c2.metric("Valor Total", f"${val_act:,.2f}")
    c3.metric("Resultado", f"${pnl_usd:,.2f}", delta=f"{pnl_pct:.2f}%")
    c4.metric("Stop Loss Configurado", f"${stop_loss_val:.2f}", delta=f"{((precio_actual - stop_loss_val)/precio_actual)*100:.1f}% al Stop")

    st.markdown("---")

    # --- SECCIÓN 1: SEMÁFORO TÁCTICO MODULAR ---
    st.subheader(f"🚥 Semáforo Táctico Modular: {ticker_sel}")
    s1, s2, s3, s4 = st.columns(4)

    # 1. Tendencia de Precio
    with s1:
        st.markdown("**1. Tendencia de Precio**")
        if precio_actual >= sma50:
            st.success("🟢 **ALCISTA**\nPrecio por encima de SMA 50.")
        elif precio_actual >= sma200:
            st.warning("🟡 **NEUTRAL / CORRECCIÓN**\nEntre SMA 50 y SMA 200.")
        else:
            st.error("🔴 **BAJISTA**\nPrecio por debajo de SMA 200.")

    # 2. Estado de Divergencia
    with s2:
        st.markdown("**2. Divergencias (RSI)**")
        if div_alcista:
            st.info("🟢 **DIVERGENCIA ALCISTA**\nPoderoso patrón de rebote.")
        elif div_bajista:
            st.warning("⚠️ **DIVERGENCIA BAJISTA**\nPerdiendo fuerza compradora.")
        else:
            st.success("⚪ **SIN DIVERGENCIA**\nEstructura técnica armónica.")

    # 3. Estado de Stop Loss
    with s3:
        st.markdown("**3. Distancia a Stop Loss**")
        dist_stop = ((precio_actual - stop_loss_val) / precio_actual) * 100
        if precio_actual <= stop_loss_val:
            st.error("🔴 **STOP LOSS VIOLADO**\nEl precio cayó por debajo del límite.")
        elif dist_stop < 5:
            st.warning(f"🟡 **ZONA CRÍTICA**\nA solo {dist_stop:.1f}% del Stop Loss.")
        else:
            st.success(f"🟢 **SEGURO**\nA {dist_stop:.1f}% del nivel de corte.")

    # 4. Diagnóstico Integral
    with s4:
        st.markdown("**4. Estrategia Sugerida**")
        if precio_actual >= sma50 and not div_bajista:
            st.success("🟢 **MANTENER / DCA**\nTendencia sana para acumulación.")
        elif div_alcista or (precio_actual >= sma200 and precio_actual < sma50):
            st.warning("🟡 **COMPRA TÁCTICA**\nBuscar entradas cerca de soportes.")
        else:
            st.error("🔴 **PAUSAR ENTRADAS**\nEsperar estabilización de mercado.")

    st.markdown("---")

    # --- SECCIÓN 2: MÓDULOS ESPECÍFICOS (ETF vs EMPRESA) ---
    if es_etf:
        st.subheader("⚖️ Módulo ETF: Comparativa de Fuerza Relativa vs S&P 500 (SPY)")
        # Rendimiento a 1 año
        rend_ticker = ((df_d['Close'].iloc[-1] - df_d['Close'].iloc[0]) / df_d['Close'].iloc[0]) * 100
        rend_spy = ((spy_close.iloc[-1] - spy_close.iloc[0]) / spy_close.iloc[0]) * 100
        alpha = rend_ticker - rend_spy

        e1, e2, e3 = st.columns(3)
        e1.metric(f"Rendimiento 1A ({ticker_sel})", f"{rend_ticker:.2f}%")
        e2.metric("Rendimiento 1A (SPY)", f"{rend_spy:.2f}%")
        e3.metric("Alpha (Vs SPY)", f"{alpha:+.2f}%", delta="Alfa Positivo" if alpha > 0 else "Alfa Negativo")

        if alpha > 0:
            st.success(f"🟢 **Superando al Mercado:** {ticker_sel} demuestra mayor fuerza relativa que el S&P 500 (+{alpha:.2f}%).")
        else:
            st.warning(f"🟡 **Por debajo del Mercado:** {ticker_sel} rinde menos que el S&P 500 ({alpha:.2f}%).")

    else:
        st.subheader("🏢 Módulo Empresa: Análisis Fundamental Multianual (Últimos 3 Balances)")
        if not financials.empty and financials.shape[1] >= 3:
            cols = financials.columns[:3]
            try:
                # Extracción de Métricas
                rev = financials.loc['Total Revenue', cols] / 1e9
                net_inc = financials.loc['Net Income', cols] / 1e9
                
                f_df = pd.DataFrame({
                    "Año": [c.strftime('%Y') for c in cols],
                    "Ingresos (B USD)": rev.values,
                    "Beneficio Neto (B USD)": net_inc.values
                }).sort_values("Año")

                # Tendencia de Ingresos
                rev_growth = ((f_df["Ingresos (B USD)"].iloc[-1] - f_df["Ingresos (B USD)"].iloc[0]) / f_df["Ingresos (B USD)"].iloc[0]) * 100

                m1, m2, m3 = st.columns(3)
                m1.dataframe(f_df, hide_index=True, use_container_width=True)
                m2.metric("Crecimiento Ingresos (3A)", f"{rev_growth:+.1f}%")
                
                with m3:
                    if rev_growth > 15:
                        st.success("🟢 **FUNDAMENTALES SÓLIDOS**\nCrecimiento orgánico de ingresos constante.")
                    elif rev_growth > 0:
                        st.warning("🟡 **CRECIMIENTO MODERADO**\nIngresos estables pero sin aceleración.")
                    else:
                        st.error("🔴 **DETERIORO FUNDAMENTAL**\nCaída en ingresos los últimos 3 años.")
            except Exception:
                st.info("Datos fundamentales detallados no disponibles públicamente para este activo.")
        else:
            st.info("Información de balances anuales insuficientes en la base de datos para mostrar la tendencia de 3 años.")

    st.markdown("---")

    # --- SECCIÓN 3: GRÁFICO INTERACTIVO COMPLETO ---
    st.subheader("📈 Gráfico de Velas, Medias Móviles, RSI y MACD")
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
    st.error(f"Asegúrate de ingresar un ticker válido. (Detalle: {e})")

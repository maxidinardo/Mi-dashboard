import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

st.set_page_config(page_title="Terminal Financiero Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetricValue"] { font-size: 19px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CARTERA Y CONFIGURACIÓN ---
st.sidebar.header("📝 Gestión de Cartera")

cartera_inicial = pd.DataFrame([
    {"Ticker": "AAPL", "Cantidad": 8.0, "Costo_Promedio": 180.00, "Stop_Loss": 165.00},
    {"Ticker": "QTUM", "Cantidad": 10.0, "Costo_Promedio": 148.78, "Stop_Loss": 130.00},
    {"Ticker": "NVDA", "Cantidad": 5.0, "Costo_Promedio": 120.50, "Stop_Loss": 105.00}
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

# --- DESCARGA DE DATOS (HISTORIAL EXTENDIDO A 5 AÑOS) ---
@st.cache_data(ttl=1800)
def cargar_datos_completos(symbol):
    tk = yf.Ticker(symbol)
    hist_w = tk.history(period="5y", interval="1wk")
    hist_d = tk.history(period="5y", interval="1d")
    info = tk.info
    financials = tk.financials
    cashflow = tk.cashflow
    balance = tk.balancesheet
    spy = yf.Ticker("SPY").history(period="5y", interval="1d")['Close']
    return hist_w, hist_d, info, financials, cashflow, balance, spy

try:
    posicion = cartera_df[cartera_df["Ticker"] == ticker_sel].iloc[0]
    cant = posicion["Cantidad"]
    costo_prom = posicion["Costo_Promedio"]
    stop_loss_val = posicion["Stop_Loss"]

    df_w, df_d, info, financials, cashflow, balance, spy_close = cargar_datos_completos(ticker_sel)
    precio_actual = df_d["Close"].iloc[-1]
    es_etf = info.get('quoteType', '').upper() == 'ETF'

    # --- CÁLCULO DE STOP LOSS TÉCNICO SUGERIDO ---
    # 1. Soporte Técnico Estructural (Mínimo de las últimas 4 semanas / 20 días rueda)
    soporte_tecnico = df_d['Low'].tail(20).min()
    dist_soporte_pct = ((precio_actual - soporte_tecnico) / precio_actual) * 100

    # 2. Stop por Volatilidad (ATR 14 períodos x 2)
    high_low = df_d['High'] - df_d['Low']
    high_close = np.abs(df_d['High'] - df_d['Close'].shift())
    low_close = np.abs(df_d['Low'] - df_d['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr_14 = true_range.rolling(14).mean().iloc[-1]
    stop_atr = precio_actual - (2 * atr_14)
    dist_atr_pct = ((precio_actual - stop_atr) / precio_actual) * 100

    # --- INFORMACIÓN DE STOP LOSS EN CARTERA LATERAL ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("**💡 Sugerencias Técnicas de Stop Loss:**")
    st.sidebar.caption(f"• **Soporte Estructural (Mín. 20D):** `${soporte_tecnico:.2f}` *(-{dist_soporte_pct:.2f}%)*")
    st.sidebar.caption(f"• **Por Volatilidad (ATR 2x):** `${stop_atr:.2f}` *(-{dist_atr_pct:.2f}%)*")

    # --- TÍTULO DINÁMICO ---
    st.title(f"⚡ Panel {ticker_sel}")

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

    # Divergencias
    p_min_rec = df_w['Close'].tail(8).iloc[-1] < df_w['Close'].tail(8).iloc[0]
    r_max_rec = df_w['RSI'].tail(8).iloc[-1] > df_w['RSI'].tail(8).iloc[0]
    div_alcista = p_min_rec and r_max_rec

    p_max_rec = df_w['Close'].tail(8).iloc[-1] > df_w['Close'].tail(8).iloc[0]
    r_min_rec = df_w['RSI'].tail(8).iloc[-1] < df_w['RSI'].tail(8).iloc[0]
    div_bajista = p_max_rec and r_min_rec

    # --- RESUMEN DE POSICIÓN (EXPRESADO EN %) ---
    inv_total = cant * costo_prom
    val_act = cant * precio_actual
    pnl_usd = val_act - inv_total
    pnl_pct = (pnl_usd / inv_total * 100) if inv_total > 0 else 0
    dist_stop_config_pct = ((precio_actual - stop_loss_val) / precio_actual) * 100

    st.subheader(f"📊 Rendimiento Posición: {ticker_sel}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio Actual", f"${precio_actual:.2f}")
    c2.metric("Rendimiento Posición", f"{pnl_pct:+.2f}%", delta=f"${pnl_usd:,.2f}")
    c3.metric("Distancia a Stop Configurado", f"-{dist_stop_config_pct:.2f}%", delta=f"${stop_loss_val:.2f} Nivel Stop", delta_color="normal")
    c4.metric("Distancia a Soporte Técnico", f"-{dist_soporte_pct:.2f}%", delta=f"${soporte_tecnico:.2f} Mín 20D", delta_color="normal")

    st.markdown("---")

    # --- SEMÁFORO TÁCTICO MODULAR ---
    st.subheader(f"🚥 Semáforo Táctico Modular: {ticker_sel}")
    s1, s2, s3, s4 = st.columns(4)

    with s1:
        st.markdown("**1. Tendencia de Precio**")
        dist_sma50_pct = ((precio_actual - sma50) / sma50) * 100
        if precio_actual >= sma50:
            st.success(f"🟢 **ALCISTA**\n+{dist_sma50_pct:.2f}% sobre SMA 50.")
        elif precio_actual >= sma200:
            st.warning(f"🟡 **CORRECCIÓN**\nSobre SMA 200, bajo SMA 50.")
        else:
            dist_sma200_pct = ((precio_actual - sma200) / sma200) * 100
            st.error(f"🔴 **BAJISTA**\n{dist_sma200_pct:.2f}% bajo SMA 200.")

    with s2:
        st.markdown("**2. Divergencias (RSI)**")
        if div_alcista:
            st.info("🟢 **DIVERGENCIA ALCISTA**\nPatrón de rebote detectado.")
        elif div_bajista:
            st.warning("⚠️ **DIVERGENCIA BAJISTA**\nPérdida de impulso comprador.")
        else:
            st.success("⚪ **SIN DIVERGENCIA**\nEstructura técnica armónica.")

    with s3:
        st.markdown("**3. Distancia a Stop Loss**")
        if precio_actual <= stop_loss_val:
            st.error(f"🔴 **VIOLADO**\nBajo el límite por {abs(dist_stop_config_pct):.2f}%.")
        elif dist_stop_config_pct < 5.0:
            st.warning(f"🟡 **ZONA CRÍTICA**\nA -{dist_stop_config_pct:.2f}% del Stop.")
        else:
            st.success(f"🟢 **SEGURO**\nMargen de -{dist_stop_config_pct:.2f}%.")

    with s4:
        st.markdown("**4. Estrategia Sugerida**")
        if precio_actual >= sma50 and not div_bajista:
            st.success("🟢 **MANTENER / DCA**\nTendencia sana para acumular.")
        elif div_alcista or (precio_actual >= sma200 and precio_actual < sma50):
            st.warning("🟡 **COMPRA TÁCTICA**\nBuscar entradas en soportes.")
        else:
            st.error("🔴 **PAUSAR ENTRADAS**\nEsperar estabilización.")

    st.markdown("---")

    # --- MÓDULO FUNDAMENTAL AVANZADO O ETF ---
    if es_etf:
        st.subheader("⚖️ Módulo ETF: Comparativa vs S&P 500 (SPY)")
        rend_ticker = ((df_d['Close'].iloc[-1] - df_d['Close'].iloc[0]) / df_d['Close'].iloc[0]) * 100
        rend_spy = ((spy_close.iloc[-1] - spy_close.iloc[0]) / spy_close.iloc[0]) * 100
        alpha = rend_ticker - rend_spy

        e1, e2, e3 = st.columns(3)
        e1.metric(f"Rendimiento 5A ({ticker_sel})", f"{rend_ticker:+.2f}%")
        e2.metric("Rendimiento 5A (SPY)", f"{rend_spy:+.2f}%")
        e3.metric("Alpha Relativo", f"{alpha:+.2f}%", delta="Alfa Positivo" if alpha > 0 else "Alfa Negativo")
    else:
        st.subheader("🏢 Módulo Fundamental Exhaustivo (EEFF & Ratios)")
        eps = info.get('trailingEps', 'N/A')
        fcf = info.get('freeCashflow', None)
        fcf_str = f"${fcf / 1e9:.2f}B" if fcf else "N/A"
        revenue = info.get('totalRevenue', None)
        rev_str = f"${revenue / 1e9:.2f}B" if revenue else "N/A"
        total_debt = info.get('totalDebt', None)
        debt_str = f"${total_debt / 1e9:.2f}B" if total_debt else "N/A"
        current_ratio = info.get('currentRatio', 'N/A')
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("EPS (TTM)", f"${eps}" if isinstance(eps, (int, float)) else "N/A")
        m2.metric("Ingresos Totales", rev_str)
        m3.metric("Free Cash Flow (FCF)", fcf_str)
        m4.metric("Deuda Total", debt_str)
        m5.metric("Ratio Liquidez", f"{current_ratio}x" if isinstance(current_ratio, (int, float)) else "N/A")

        if not cashflow.empty and not balance.empty:
            st.markdown("**Evolución Multianual de Flujos y Recompras:**")
            cols = cashflow.columns[:3]
            try:
                years = [c.strftime('%Y') for c in cols]
                recompras = []
                for col in cols:
                    val = cashflow.loc['Repurchase Of Capital Stock', col] if 'Repurchase Of Capital Stock' in cashflow.index else 0
                    recompras.append(abs(val) / 1e9 if pd.notna(val) else 0)
                
                df_fund = pd.DataFrame({
                    "Año": years,
                    "Recompras Acciones (B USD)": recompras
                }).sort_values("Año")

                st.dataframe(df_fund, hide_index=True, use_container_width=True)
            except Exception:
                st.caption("Detalle específico de recompras en balances no disponible para este activo.")

    st.markdown("---")

    # --- GRÁFICO DE VELAS A 5 AÑOS CON DESPLAZAMIENTO LATERAL ---
    st.subheader("📈 Gráfico de Velas (Histórico 5 Años) con Barra de Desplazamiento Lateral")
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

    # Velas y Medias
    fig.add_trace(go.Candlestick(x=df_d.index, open=df_d['Open'], high=df_d['High'], low=df_d['Low'], close=df_d['Close'], name="Precio"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_d.index, y=df_d['SMA_50'], line=dict(color='#FF9900', width=1.5), name="SMA 50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_d.index, y=df_d['SMA_200'], line=dict(color='#0066FF', width=1.5), name="SMA 200"), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=df_w.index, y=df_w['RSI'], line=dict(color='#AB63FA', width=1.5), name="RSI (Semanal)"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # MACD
    fig.add_trace(go.Scatter(x=df_w.index, y=df_w['MACD'], line=dict(color='#00FFCC', width=1), name="MACD"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df_w.index, y=df_w['Signal'], line=dict(color='#FF0055', width=1), name="Signal"), row=3, col=1)

    # Configuración de layout con barra horizontal a 5 años
    fig.update_layout(
        template="plotly_dark",
        height=700,
        xaxis_rangeslider_visible=True,
        xaxis_rangeslider_thickness=0.05,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar el activo seleccionado. (Detalle: {e})")


    # Habilitar barra de desplazamiento horizontal (Range Slider)
    fig.update_layout(
        template="plotly_dark",
        height=650,
        xaxis_rangeslider_visible=True,  # Barra de desplazamiento activada
        xaxis_rangeslider_thickness=0.05,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar el activo seleccionado. (Detalle: {e})")

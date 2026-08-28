import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Configuración inicial de la página
st.set_page_config(page_title="Terminal Financiero Pro", layout="wide", initial_sidebar_state="expanded")

# Estilos CSS personalizados
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetricValue"] { font-size: 19px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CARTERA IMPORTADA DE DIVTRACKER ---
st.sidebar.header("📝 Gestión de Cartera")

cartera_inicial = pd.DataFrame([
    {'Ticker': 'AAPL', 'Cantidad': 3.30, 'Costo_Promedio': 188.79, 'Stop_Loss': 169.91},
    {'Ticker': 'AMZN', 'Cantidad': 1.04, 'Costo_Promedio': 153.48, 'Stop_Loss': 138.13},
    {'Ticker': 'AXP', 'Cantidad': 1.13, 'Costo_Promedio': 206.97, 'Stop_Loss': 186.27},
    {'Ticker': 'BABA', 'Cantidad': 0.11, 'Costo_Promedio': 76.32, 'Stop_Loss': 68.69},
    {'Ticker': 'BRK-B', 'Cantidad': 1.54, 'Costo_Promedio': 436.20, 'Stop_Loss': 392.58},
    {'Ticker': 'DIA', 'Cantidad': 0.65, 'Costo_Promedio': 384.29, 'Stop_Loss': 345.86},
    {'Ticker': 'FXI', 'Cantidad': 17.20, 'Costo_Promedio': 30.24, 'Stop_Loss': 27.22},
    {'Ticker': 'GOOGL', 'Cantidad': 5.83, 'Costo_Promedio': 146.51, 'Stop_Loss': 131.86},
    {'Ticker': 'JNJ', 'Cantidad': 0.93, 'Costo_Promedio': 133.68, 'Stop_Loss': 120.31},
    {'Ticker': 'KO', 'Cantidad': 7.60, 'Costo_Promedio': 64.86, 'Stop_Loss': 58.37},
    {'Ticker': 'MCD', 'Cantidad': 1.09, 'Costo_Promedio': 269.46, 'Stop_Loss': 242.51},
    {'Ticker': 'MELI', 'Cantidad': 0.31, 'Costo_Promedio': 2268.38, 'Stop_Loss': 2041.54},
    {'Ticker': 'MSFT', 'Cantidad': 0.10, 'Costo_Promedio': 381.50, 'Stop_Loss': 343.35},
    {'Ticker': 'NKE', 'Cantidad': 10.92, 'Costo_Promedio': 70.07, 'Stop_Loss': 63.06},
    {'Ticker': 'PYPL', 'Cantidad': 1.25, 'Costo_Promedio': 61.61, 'Stop_Loss': 55.45},
    {'Ticker': 'QQQ', 'Cantidad': 0.55, 'Costo_Promedio': 422.06, 'Stop_Loss': 379.85},
    {'Ticker': 'SCHD', 'Cantidad': 12.87, 'Costo_Promedio': 27.00, 'Stop_Loss': 24.30},
    {'Ticker': 'SHY', 'Cantidad': 15.72, 'Costo_Promedio': 82.70, 'Stop_Loss': 74.43},
    {'Ticker': 'SPY', 'Cantidad': 3.30, 'Costo_Promedio': 536.74, 'Stop_Loss': 483.07},
    {'Ticker': 'V', 'Cantidad': 0.56, 'Costo_Promedio': 268.25, 'Stop_Loss': 241.42},
    {'Ticker': 'VIST', 'Cantidad': 8.33, 'Costo_Promedio': 30.52, 'Stop_Loss': 27.47}
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

# --- DESCARGA DE DATOS ---
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

    # --- FIBONACCI ---
    df_recent = df_d.tail(252)
    max_fib = df_recent['High'].max()
    min_fib = df_recent['Low'].min()
    diff_fib = max_fib - min_fib

    fib_0 = max_fib
    fib_236 = max_fib - 0.236 * diff_fib
    fib_382 = max_fib - 0.382 * diff_fib
    fib_500 = max_fib - 0.500 * diff_fib
    fib_618 = max_fib - 0.618 * diff_fib
    fib_100 = min_fib
    ext_1618 = max_fib + 0.618 * diff_fib

    # --- STOP LOSS TÉCNICO SUGERIDO ---
    soporte_tecnico = df_d['Low'].tail(20).min()
    dist_soporte_pct = ((precio_actual - soporte_tecnico) / precio_actual) * 100

    high_low = df_d['High'] - df_d['Low']
    high_close = np.abs(df_d['High'] - df_d['Close'].shift())
    low_close = np.abs(df_d['Low'] - df_d['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr_14 = true_range.rolling(14).mean().iloc[-1]
    stop_atr = precio_actual - (2 * atr_14)
    dist_atr_pct = ((precio_actual - stop_atr) / precio_actual) * 100

    st.sidebar.markdown("---")
    st.sidebar.markdown("**💡 Sugerencias Técnicas de Stop Loss:**")
    st.sidebar.caption(f"• **Soporte Estructural (Mín 20D):** `${soporte_tecnico:.2f}` *({dist_soporte_pct:+.2f}%)*")
    st.sidebar.caption(f"• **Por Volatilidad (ATR 2x):** `${stop_atr:.2f}` *({dist_atr_pct:+.2f}%)*")

    st.title(f"⚡ Panel {ticker_sel}")

    # --- INDICADORES TÉCNICOS ---
    df_d['SMA_50'] = df_d['Close'].rolling(50).mean()
    df_d['SMA_200'] = df_d['Close'].rolling(200).mean()
    sma50 = df_d['SMA_50'].iloc[-1]
    sma200 = df_d['SMA_200'].iloc[-1]

    # RSI
    delta_w = df_w['Close'].diff()
    gain = (delta_w.where(delta_w > 0, 0)).rolling(14).mean()
    loss = (-delta_w.where(delta_w < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df_w['RSI'] = 100 - (100 / (1 + rs))

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

    # --- RESUMEN DE POSICIÓN ---
    inv_total = cant * costo_prom
    val_act = cant * precio_actual
    pnl_usd = val_act - inv_total
    pnl_pct = (pnl_usd / inv_total * 100) if inv_total > 0 else 0
    dist_stop_config_pct = ((precio_actual - stop_loss_val) / precio_actual) * 100

    st.subheader(f"📊 Rendimiento Posición: {ticker_sel}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio Actual", f"${precio_actual:.2f}")
    c2.metric("Rendimiento Posición", f"{pnl_pct:+.2f}%", delta=f"${pnl_usd:,.2f}")
    c3.metric("Distancia a Stop Configurado", f"{dist_stop_config_pct:+.2f}%", delta=f"${stop_loss_val:.2f} Nivel Stop", delta_color="normal")
    c4.metric("Distancia a Soporte Técnico", f"{dist_soporte_pct:+.2f}%", delta=f"${soporte_tecnico:.2f} Mín 20D", delta_color="normal")

    st.markdown("---")

    # --- INTERPRETACIÓN ESTRUCTURAL Y FIBONACCI ---
    st.subheader(f"📐 Interpretación de Estructuras y Niveles Clave ({ticker_sel})")
    
    niveles_fib = [fib_100, fib_618, fib_500, fib_382, fib_236, fib_0, ext_1618]
    resistencia_proxima = min([n for n in niveles_fib if n > precio_actual], default=ext_1618)
    soporte_proximo = max([n for n in niveles_fib if n < precio_actual], default=fib_100)
    
    dist_res_pct = ((resistencia_proxima - precio_actual) / precio_actual) * 100
    dist_sop_pct = ((precio_actual - soporte_proximo) / precio_actual) * 100

    f1, f2, f3 = st.columns(3)
    f1.metric("🎯 Próxima Resistencia Objetiva", f"${resistencia_proxima:.2f}", delta=f"+{dist_res_pct:.2f}% distancia")
    f2.metric("🛡️ Próximo Soporte Fibonacci", f"${soporte_proximo:.2f}", delta=f"-{dist_sop_pct:.2f}% distancia", delta_color="normal")
    f3.metric("📏 Zona Dorada Fib (61.8%)", f"${fib_618:.2f}", delta="Punto crítico de recarga" if precio_actual >= fib_618 else "Bajo zona dorada")

    pct_extension = ((ext_1618 - precio_actual) / precio_actual) * 100
    estado_chartista = (
        "El activo muestra fortaleza alcista manteniéndose sobre la Zona Dorada (61.8%)." 
        if precio_actual >= fib_618 
        else "El activo ha penetrado niveles clave de retroceso, lo que sugiere cautela antes de abrir nuevas posiciones."
    )

    st.info(
        f"🔍 **Diagnóstico Táctico Estructural:**\n\n"
        f"• **Situación de Fibonacci:** El precio cotiza entre el soporte de **${soporte_proximo:.2f}** y la resistencia de **${resistencia_proxima:.2f}**.\n\n"
        f"• **Techo Clave:** Un quiebre confirmado del máximo reciente en **${max_fib:.2f}** proyecta un objetivo por **Extensión de Fibonacci** hacia **${ext_1618:.2f}** (+{pct_extension:.1f}%).\n\n"
        f"• **Estructura Chartista:** {estado_chartista}"
    )

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
            st.warning(f"🟡 **ZONA CRÍTICA**\nA {dist_stop_config_pct:+.2f}% del Stop.")
        else:
            st.success(f"🟢 **SEGURO**\nMargen de {dist_stop_config_pct:+.2f}%.")

    with s4:
        st.markdown("**4. Estrategia Sugerida**")
        if precio_actual >= sma50 and not div_bajista:
            st.success("🟢 **MANTENER / DCA**\nTendencia sana para acumular.")
        elif div_alcista or (precio_actual >= sma200 and precio_actual < sma50):
            st.warning("🟡 **COMPRA TÁCTICA**\nBuscar entradas en soportes.")
        else:
            st.error("🔴 **PAUSAR ENTRADAS**\nEsperar estabilización.")

    st.markdown("---")

    # --- MÓDULO FUNDAMENTAL AVANZADO (EVOLUTIVO 3 AÑOS) ---
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
        st.subheader(f"🏢 Módulo Fundamental Exhaustivo: Evolutivo 3 Años ({ticker_sel})")
        
        # Extracción de columnas de los últimos 3 años disponibles
        cols_fin = financials.columns[:3] if not financials.empty else []
        years = [c.strftime('%Y') for c in cols_fin] if len(cols_fin) > 0 else ["N/A", "N/A", "N/A"]

        # Funciones auxiliares para extracción segura de métricas multianuales
        def get_series_vals(df_source, row_label, factor=1e9):
            vals = []
            for col in cols_fin:
                if not df_source.empty and row_label in df_source.index and pd.notna(df_source.loc[row_label, col]):
                    vals.append(f"${df_source.loc[row_label, col] / factor:.2f}B" if factor else f"${df_source.loc[row_label, col]:.2f}")
                else:
                    vals.append("N/A")
            return vals

        # 1. Crecimiento
        rev_vals = get_series_vals(financials, 'Total Revenue')
        eps_vals = get_series_vals(financials, 'Basic EPS', factor=None)
        fcf_vals = get_series_vals(cashflow, 'Free Cash Flow')
        txt_crec = " | ".join([f"{y}: Rev {r}, EPS {e}" for y, r, e in zip(years, rev_vals, eps_vals)])

        # 2. Rentabilidad
        gross_margin = []
        for col in cols_fin:
            if not financials.empty and 'Gross Profit' in financials.index and 'Total Revenue' in financials.index:
                gp = financials.loc['Gross Profit', col]
                rev = financials.loc['Total Revenue', col]
                gross_margin.append(f"{(gp/rev)*100:.1f}%" if pd.notna(gp) and pd.notna(rev) and rev != 0 else "N/A")
            else:
                gross_margin.append("N/A")
        txt_rent = " | ".join([f"{y}: Mg Bruto {m}" for y, m in zip(years, gross_margin)])

        # 3. Caja
        txt_caja = " | ".join([f"{y}: FCF {f}" for y, f in zip(years, fcf_vals)])

        # 4. Deuda
        debt_vals = get_series_vals(balance, 'Total Debt')
        txt_deuda = " | ".join([f"{y}: Deuda {d}" for y, d in zip(years, debt_vals)])

        # 5. Acciones
        shares_vals = get_series_vals(balance, 'Share Issued', factor=1e6)
        txt_acciones = " | ".join([f"{y}: {s}M" for y, s in zip(years, shares_vals)]) if len(shares_vals) > 0 and shares_vals[0] != "N/A" else "Datos no disponibles en balance"

        # 6. Ventaja competitiva (Márgenes Operativos)
        op_margin = []
        for col in cols_fin:
            if not financials.empty and 'Operating Income' in financials.index and 'Total Revenue' in financials.index:
                op = financials.loc['Operating Income', col]
                rev = financials.loc['Total Revenue', col]
                op_margin.append(f"{(op/rev)*100:.1f}%" if pd.notna(op) and pd.notna(rev) and rev != 0 else "N/A")
            else:
                op_margin.append("N/A")
        txt_moat = " | ".join([f"{y}: Mg Op {m}" for y, m in zip(years, op_margin)])

        # 7. Valuación TTM actual
        pe_ratio = info.get('trailingPE', 'N/A')
        fcf_yield = f"{(info.get('freeCashflow', 0) / info.get('marketCap', 1))*100:.2f}%" if info.get('marketCap') else "N/A"
        ev_ebitda = info.get('enterpriseToEbitda', 'N/A')
        txt_val = f"P/E TTM: {pe_ratio}x | FCF Yield: {fcf_yield} | EV/EBITDA: {ev_ebitda}x"

        # TABLA DE EVALUACIÓN MULTIANUAL DINÁMICA
        st.markdown("### 📋 Análisis Multianual de Estados Financieros (3 Años)")
        tabla_fund_data = {
            "Bloque": [
                "1. Crecimiento", 
                "2. Rentabilidad", 
                "3. Caja", 
                "4. Deuda", 
                "5. Acciones", 
                "6. Ventaja competitiva", 
                "7. Valuación"
            ],
            "Qué mirar": [
                "Ventas, EPS, FCF",
                "Márgenes, ROIC, ROE",
                "Free Cash Flow",
                "Deuda neta / EBITDA",
                "Acciones en circulación",
                "Market share, márgenes",
                "P/E, FCF Yield, EV/EBITDA"
            ],
            "Objetivo": [
                "📈 Crecimiento sostenido",
                "📈 Estables o crecientes",
                "📈 Conversión a beneficio real",
                "📉 Controlada",
                "📉 Estables o bajando",
                "🟢 Que se mantenga",
                "💰 Precio razonable"
            ],
            f"Evolución 3 Años ({' - '.join(reversed(years))})": [
                txt_crec,
                txt_rent,
                txt_caja,
                txt_deuda,
                txt_acciones,
                txt_moat,
                txt_val
            ]
        }
        st.table(pd.DataFrame(tabla_fund_data))

        # RESUMEN FUNDAMENTAL ESPECÍFICO DE LOS 3 AÑOS
        st.markdown(f"### 📝 Análisis Sintético de los Últimos 3 Años ({ticker_sel})")
        
        rev_trend = f"ingresos pasaron de {rev_vals[-1]} a {rev_vals[0]}" if len(rev_vals) > 1 and rev_vals[0] != "N/A" else "ingresos mantienen su trayectoria de balance"
        fcf_trend = f"un Free Cash Flow en {fcf_vals[0]}" if fcf_vals[0] != "N/A" else "generación de caja en observación"
        debt_trend = f"deuda total en {debt_vals[0]}" if debt_vals[0] != "N/A" else "estructura de deuda estable"
        
        resumen_especifico = (
            f"El desempeño multianual de {ticker_sel} refleja la capacidad del activo para sostener su ventaja "
            f"competitiva y generar valor al accionista. En los últimos tres años, los {rev_trend}, "
            f"respaldados por {fcf_trend} que confirma la calidad operacional del negocio. "
            f"La estabilidad en los márgenes operativos demuestra eficiencia en la asignación de recursos. "
            f"Por su parte, la contención con una {debt_trend} refuerza la solidez del balance y optimiza "
            f"el retorno sobre el capital invertido respecto a sus métricas actuales de valuación (P/E de {pe_ratio}x)."
        )
        st.info(resumen_especifico)

    st.markdown("---")

    # --- GRÁFICO DE VELAS (5 AÑOS) CON FIBONACCI ---
    st.subheader("📈 Gráfico de Velas (5 Años) con Estructura de Fibonacci")
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

    fig.add_trace(go.Candlestick(x=df_d.index, open=df_d['Open'], high=df_d['High'], low=df_d['Low'], close=df_d['Close'], name="Precio"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_d.index, y=df_d['SMA_50'], line=dict(color='#FF9900', width=1.5), name="SMA 50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_d.index, y=df_d['SMA_200'], line=dict(color='#0066FF', width=1.5), name="SMA 200"), row=1, col=1)

    fig.add_hline(y=max_fib, line_dash="dash", line_color="red", annotation_text=f"Fib 0% (${max_fib:.1f})", row=1, col=1)
    fig.add_hline(y=fib_382, line_dash="dash", line_color="orange", annotation_text=f"Fib 38.2% (${fib_382:.1f})", row=1, col=1)
    fig.add_hline(y=fib_618, line_dash="dash", line_color="gold", annotation_text=f"Fib 61.8% (${fib_618:.1f})", row=1, col=1)
    fig.add_hline(y=min_fib, line_dash="dash", line_color="green", annotation_text=f"Fib 100% (${min_fib:.1f})", row=1, col=1)

    fig.add_trace(go.Scatter(x=df_w.index, y=df_w['RSI'], line=dict(color='#AB63FA', width=1.5), name="RSI (Semanal)"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.add_trace(go.Scatter(x=df_w.index, y=df_w['MACD'], line=dict(color='#00FFCC', width=1), name="MACD"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df_w.index, y=df_w['Signal'], line=dict(color='#FF0055', width=1), name="Signal"), row=3, col=1)

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

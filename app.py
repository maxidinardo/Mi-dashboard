import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime

# Configuración inicial de la página
st.set_page_config(page_title="Terminal Financiero Pro", layout="wide", initial_sidebar_state="expanded")

# Estilos CSS personalizados
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetricValue"] { font-size: 19px; font-weight: bold; }
    
    /* Estilos para la Matriz Fundamental */
    .fund-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-family: sans-serif; }
    .fund-table th { background-color: #1e293b; color: #f8fafc; padding: 10px; text-align: right; font-size: 13px; border-bottom: 2px solid #334155; }
    .fund-table th:first-child { text-align: left; }
    .fund-table td { padding: 8px 10px; font-size: 13px; border-bottom: 1px solid #1e293b; text-align: right; }
    .fund-table td:first-child { text-align: left; font-weight: 500; }
    .fund-group-header { background-color: #0f172a; color: #38bdf8; font-weight: bold; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; }
    .val-pill { padding: 3px 8px; border-radius: 4px; font-weight: 600; display: inline-block; min-width: 60px; text-align: center; }
    .val-pos { background-color: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
    .val-neg { background-color: rgba(244, 63, 94, 0.2); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.4); }
    .val-neutral { background-color: rgba(148, 163, 184, 0.1); color: #cbd5e1; }
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

# --- FUNCIÓN NOTICIAS YAHOO FINANCE ---
@st.cache_data(ttl=900)
def obtener_ultimas_noticias(symbol, limite=3):
    try:
        tk = yf.Ticker(symbol)
        noticias = tk.news
        noticias_procesadas = []
        
        for item in noticias[:limite]:
            content = item.get('content', item)
            titulo = content.get('title', 'Sin título')
            resumen = content.get('summary', content.get('description', ''))
            proveedor = content.get('provider', {}).get('displayName', 'Yahoo Finance')
            link = content.get('canonicalUrl', {}).get('url', content.get('link', '#'))
            
            pub_date = content.get('pubDate', '')
            if not pub_date and 'providerPublishTime' in item:
                pub_date = datetime.fromtimestamp(item['providerPublishTime']).strftime('%Y-%m-%d %H:%M')
            elif pub_date:
                pub_date = pub_date.replace('T', ' ').replace('Z', '')[:16]

            noticias_procesadas.append({
                'titulo': titulo,
                'resumen': resumen,
                'proveedor': proveedor,
                'link': link,
                'fecha': pub_date
            })
        return noticias_procesadas
    except Exception:
        return []

# --- GENERADOR DE SPARKLINE SVG PARA STREAMLIT ---
def generar_sparkline_svg(values):
    valid_vals = [v for v in values if isinstance(v, (int, float)) and not pd.isna(v)]
    if len(valid_vals) < 2:
        return "-"
    min_v, max_v = min(valid_vals), max(valid_vals)
    rng = max_v - min_v if max_v - min_v != 0 else 1
    
    pts = []
    circles = []
    for idx, val in enumerate(values):
        if isinstance(val, (int, float)) and not pd.isna(val):
            x = (idx / (len(values) - 1)) * 60 + 5
            y = 22 - ((val - min_v) / rng) * 16
            pts.append(f"{x:.1f},{y:.1f}")
            circles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="#38bdf8" />')
    
    polyline = f'<polyline fill="none" stroke="#38bdf8" stroke-width="2" points="{" ".join(pts)}" />'
    return f'<svg width="70" height="26" viewBox="0 0 70 26">{polyline}{"".join(circles)}</svg>'

# --- EJECUCIÓN PRINCIPAL DE LA APLICACIÓN ---
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

    # --- MÓDULO FUNDAMENTAL AVANZADO ---
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
        st.subheader(f"🏢 Matriz Fundamental Avanzada ({ticker_sel})")
        
        cols_fin = list(financials.columns[:3]) if not financials.empty else []
        years = [c.strftime('%Y') for c in reversed(cols_fin)] if len(cols_fin) > 0 else ["Año-2", "Año-1", "Anterior"]
        headers_years = years + ["TTM (Actual)"]

        def get_raw_series(df_source, row_label, scale=1e9):
            if df_source.empty or row_label not in df_source.index:
                return [np.nan] * len(cols_fin)
            res = []
            for col in reversed(cols_fin):
                val = df_source.loc[row_label, col]
                res.append(float(val) / scale if pd.notna(val) else np.nan)
            return res

        rev_list = get_raw_series(financials, 'Total Revenue', 1e9) + [info.get('totalRevenue', np.nan) / 1e9 if info.get('totalRevenue') else np.nan]
        eps_list = get_raw_series(financials, 'Basic EPS', 1) + [info.get('trailingEps', np.nan)]
        fcf_list = get_raw_series(cashflow, 'Free Cash Flow', 1e9) + [info.get('freeCashflow', np.nan) / 1e9 if info.get('freeCashflow') else np.nan]
        ebitda_list = get_raw_series(financials, 'EBITDA', 1e9) + [info.get('ebitda', np.nan) / 1e9 if info.get('ebitda') else np.nan]
        debt_list = get_raw_series(balance, 'Total Debt', 1e9) + [info.get('totalDebt', np.nan) / 1e9 if info.get('totalDebt') else np.nan]

        gross_list, op_list = [], []
        for col in reversed(cols_fin):
            if not financials.empty and 'Gross Profit' in financials.index and 'Total Revenue' in financials.index:
                gp = financials.loc['Gross Profit', col]
                rev = financials.loc['Total Revenue', col]
                gross_list.append((gp / rev) * 100 if pd.notna(gp) and pd.notna(rev) and rev != 0 else np.nan)
            else:
                gross_list.append(np.nan)
            
            if not financials.empty and 'Operating Income' in financials.index and 'Total Revenue' in financials.index:
                op = financials.loc['Operating Income', col]
                rev = financials.loc['Total Revenue', col]
                op_list.append((op / rev) * 100 if pd.notna(op) and pd.notna(rev) and rev != 0 else np.nan)
            else:
                op_list.append(np.nan)

        gross_list.append(info.get('grossMargins', np.nan) * 100 if info.get('grossMargins') else np.nan)
        op_list.append(info.get('operatingMargins', np.nan) * 100 if info.get('operatingMargins') else np.nan)

        groups = [
            {
                "title": "Indicadores de Crecimiento",
                "metrics": [
                    {"name": "Ventas / Ingresos", "unit": "$B", "vals": rev_list},
                    {"name": "EPS (Ganancia por Acción)", "unit": "$", "vals": eps_list}
                ]
            },
            {
                "title": "Rentabilidad y Ventaja Competitiva",
                "metrics": [
                    {"name": "Margen Bruto", "unit": "%", "vals": gross_list},
                    {"name": "Margen Operativo", "unit": "%", "vals": op_list}
                ]
            },
            {
                "title": "Generación de Caja",
                "metrics": [
                    {"name": "Free Cash Flow (FCF)", "unit": "$B", "vals": fcf_list}
                ]
            },
            {
                "title": "Estructura de Deuda",
                "metrics": [
                    {"name": "EBITDA", "unit": "$B", "vals": ebitda_list},
                    {"name": "Deuda Total", "unit": "$B", "vals": debt_list, "is_inverse": True}
                ]
            }
        ]

        html_code = f"""
        <table class="fund-table">
            <thead>
                <tr>
                    <th>Indicador</th>
                    <th>{headers_years[0]}</th>
                    <th>{headers_years[1]}</th>
                    <th>{headers_years[2]}</th>
                    <th>{headers_years[3]}</th>
                    <th style="text-align: center;">Tendencia</th>
                </tr>
            </thead>
            <tbody>
        """

        for grp in groups:
            html_code += f'<tr><td colSpan="6" class="fund-group-header">{grp["title"]}</td></tr>'
            for m in grp["metrics"]:
                vals = m["vals"]
                is_inv = m.get("is_inverse", False)
                
                html_code += f'<tr><td>{m["name"]} <span style="color:#64748b; font-size:11px;">({m["unit"]})</span></td>'
                
                for idx, v in enumerate(vals):
                    if pd.isna(v):
                        val_str = "N/A"
                        cell_class = "val-neutral"
                    else:
                        val_str = f"{v:.2f}"
                        if idx == 0:
                            cell_class = "val-neutral"
                        else:
                            prev_v = vals[idx-1]
                            if pd.isna(prev_v):
                                cell_class = "val-neutral"
                            else:
                                if is_inv:
                                    cell_class = "val-pos" if v < prev_v else "val-neg"
                                else:
                                    cell_class = "val-pos" if v > prev_v else "val-neg"
                    
                    html_code += f'<td><span class="val-pill {cell_class}">{val_str}</span></td>'
                
                sparkline = generar_sparkline_svg(vals)
                html_code += f'<td style="text-align: center; vertical-align: middle;">{sparkline}</td></tr>'

        html_code += """
            </tbody>
        </table>
        """
        st.markdown(html_code, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Se produjo un error al procesar los datos: {e}")

import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

# Configuración inicial de la página
st.set_page_config(
    page_title="Terminal Financiero Pro",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados
st.markdown(
    """
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
    """,
    unsafe_allow_html=True,
)

# --- PERSISTENCIA DE CARTERA EN JSON ---
CARTERA_FILE = Path(__file__).resolve().parent / "cartera_guardada.json"
COLUMNAS_CARTERA = ["Ticker", "Cantidad", "Costo_Promedio", "Stop_Loss"]

cartera_inicial = pd.DataFrame(
    [
        {"Ticker": "AAPL", "Cantidad": 3.30, "Costo_Promedio": 188.79, "Stop_Loss": 169.91},
        {"Ticker": "AMZN", "Cantidad": 1.04, "Costo_Promedio": 153.48, "Stop_Loss": 138.13},
        {"Ticker": "AXP", "Cantidad": 1.13, "Costo_Promedio": 206.97, "Stop_Loss": 186.27},
        {"Ticker": "BABA", "Cantidad": 0.11, "Costo_Promedio": 76.32, "Stop_Loss": 68.69},
        {"Ticker": "BRK-B", "Cantidad": 1.54, "Costo_Promedio": 436.20, "Stop_Loss": 392.58},
        {"Ticker": "DIA", "Cantidad": 0.65, "Costo_Promedio": 384.29, "Stop_Loss": 345.86},
        {"Ticker": "FXI", "Cantidad": 17.20, "Costo_Promedio": 30.24, "Stop_Loss": 27.22},
        {"Ticker": "GOOGL", "Cantidad": 5.83, "Costo_Promedio": 146.51, "Stop_Loss": 131.86},
        {"Ticker": "JNJ", "Cantidad": 0.93, "Costo_Promedio": 133.68, "Stop_Loss": 120.31},
        {"Ticker": "KO", "Cantidad": 7.60, "Costo_Promedio": 64.86, "Stop_Loss": 58.37},
        {"Ticker": "MCD", "Cantidad": 1.09, "Costo_Promedio": 269.46, "Stop_Loss": 242.51},
        {"Ticker": "MELI", "Cantidad": 0.31, "Costo_Promedio": 2268.38, "Stop_Loss": 2041.54},
        {"Ticker": "MSFT", "Cantidad": 0.10, "Costo_Promedio": 381.50, "Stop_Loss": 343.35},
        {"Ticker": "NKE", "Cantidad": 10.92, "Costo_Promedio": 70.07, "Stop_Loss": 63.06},
        {"Ticker": "PYPL", "Cantidad": 1.25, "Costo_Promedio": 61.61, "Stop_Loss": 55.45},
        {"Ticker": "QQQ", "Cantidad": 0.55, "Costo_Promedio": 422.06, "Stop_Loss": 379.85},
        {"Ticker": "SCHD", "Cantidad": 12.87, "Costo_Promedio": 27.00, "Stop_Loss": 24.30},
        {"Ticker": "SHY", "Cantidad": 15.72, "Costo_Promedio": 82.70, "Stop_Loss": 74.43},
        {"Ticker": "SPY", "Cantidad": 3.30, "Costo_Promedio": 536.74, "Stop_Loss": 483.07},
        {"Ticker": "V", "Cantidad": 0.56, "Costo_Promedio": 268.25, "Stop_Loss": 241.42},
        {"Ticker": "VIST", "Cantidad": 8.33, "Costo_Promedio": 30.52, "Stop_Loss": 27.47},
    ]
)


def normalizar_cartera(df: pd.DataFrame) -> pd.DataFrame:
    limpio = df.copy()
    for col in COLUMNAS_CARTERA:
        if col not in limpio.columns:
            limpio[col] = "" if col == "Ticker" else 0.0
    limpio = limpio[COLUMNAS_CARTERA]
    limpio["Ticker"] = limpio["Ticker"].fillna("").astype(str).str.strip().str.upper()
    limpio = limpio[limpio["Ticker"] != ""]
    for col in ["Cantidad", "Costo_Promedio", "Stop_Loss"]:
        limpio[col] = pd.to_numeric(limpio[col], errors="coerce").fillna(0.0)
    return limpio.reset_index(drop=True)


def cargar_cartera() -> pd.DataFrame:
    if CARTERA_FILE.exists():
        try:
            with open(CARTERA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            df_loaded = pd.DataFrame(data)
            if not df_loaded.empty:
                return normalizar_cartera(df_loaded)
        except Exception:
            pass
    return normalizar_cartera(cartera_inicial)


def guardar_cartera(df: pd.DataFrame) -> None:
    limpio = normalizar_cartera(df)
    with open(CARTERA_FILE, "w", encoding="utf-8") as f:
        json.dump(limpio.to_dict(orient="records"), f, indent=2, ensure_ascii=False)


# --- SIDEBAR: GESTIÓN DE CARTERA CON PERSISTENCIA ---
st.sidebar.header("📝 Gestión de Cartera")

if "cartera_base" not in st.session_state:
    st.session_state.cartera_base = cargar_cartera()

cartera_df = st.sidebar.data_editor(
    st.session_state.cartera_base,
    key="editor_cartera",
    num_rows="dynamic",
    column_config={
        "Ticker": st.column_config.TextColumn("Ticker"),
        "Cantidad": st.column_config.NumberColumn("Cant.", min_value=0.0, format="%.2f"),
        "Costo_Promedio": st.column_config.NumberColumn("Costo Prom. ($)", min_value=0.0, format="$%.2f"),
        "Stop_Loss": st.column_config.NumberColumn("Stop Loss ($)", min_value=0.0, format="$%.2f"),
    },
    use_container_width=True,
)

col_btn1, col_btn2 = st.sidebar.columns(2)
if col_btn1.button("💾 Guardar", use_container_width=True):
    guardar_cartera(cartera_df)
    st.session_state.cartera_base = normalizar_cartera(cartera_df)
    st.sidebar.success("Cartera guardada.")

if col_btn2.button("↩️ Inicial", use_container_width=True):
    guardar_cartera(cartera_inicial)
    st.session_state.cartera_base = normalizar_cartera(cartera_inicial)
    st.rerun()

st.sidebar.markdown("---")
cartera_df["Ticker"] = cartera_df["Ticker"].astype(str).str.strip().str.upper()
lista_tickers = [t for t in cartera_df["Ticker"].dropna().unique().tolist() if t and t != "NAN"]

if not lista_tickers:
    st.warning("Agrega al menos un ticker válido en la barra lateral para comenzar.")
    st.stop()

if "ticker_activo" not in st.session_state or st.session_state["ticker_activo"] not in lista_tickers:
    st.session_state["ticker_activo"] = lista_tickers[0]


def establecer_ticker(nuevo_ticker: str):
    nuevo_ticker = str(nuevo_ticker).strip().upper()
    if nuevo_ticker in lista_tickers:
        st.session_state["ticker_activo"] = nuevo_ticker


def sincronizar_ticker_sidebar():
    establecer_ticker(st.session_state["selector_sidebar"])


def sincronizar_ticker_rapido():
    establecer_ticker(st.session_state["selector_rapido"])


st.sidebar.selectbox(
    "🎯 Selecciona Activo:",
    lista_tickers,
    index=lista_tickers.index(st.session_state["ticker_activo"]),
    key="selector_sidebar",
    on_change=sincronizar_ticker_sidebar,
)


# --- DESCARGA DE DATOS ---
@st.cache_data(ttl=1800)
def cargar_spy_benchmark():
    return yf.Ticker("SPY").history(period="5y", interval="1d")["Close"]


@st.cache_data(ttl=1800)
def cargar_datos_completos(symbol):
    tk = yf.Ticker(symbol)
    hist_w = tk.history(period="5y", interval="1wk")
    hist_d = tk.history(period="5y", interval="1d")
    info = tk.info or {}
    financials = tk.financials if tk.financials is not None else pd.DataFrame()
    cashflow = tk.cashflow if tk.cashflow is not None else pd.DataFrame()
    balance = tk.balancesheet if tk.balancesheet is not None else pd.DataFrame()
    return hist_w, hist_d, info, financials, cashflow, balance


@st.cache_data(ttl=900)
def obtener_resumen_cartera(cartera_json: str) -> pd.DataFrame:
    df_c = pd.DataFrame(json.loads(cartera_json))
    if df_c.empty:
        return pd.DataFrame()

    tickers = df_c["Ticker"].unique().tolist()
    precios = {}

    try:
        data = yf.download(tickers, period="5d", interval="1d", group_by="ticker", progress=False, threads=True)
        for t in tickers:
            try:
                if len(tickers) == 1:
                    serie = data["Close"].dropna()
                else:
                    serie = data[t]["Close"].dropna()
                if not serie.empty:
                    precios[t] = float(serie.iloc[-1])
            except Exception:
                pass
    except Exception:
        pass

    for t in tickers:
        if t not in precios:
            try:
                hist_fallback = yf.Ticker(t).history(period="5d", interval="1d")["Close"].dropna()
                if not hist_fallback.empty:
                    precios[t] = float(hist_fallback.iloc[-1])
            except Exception:
                pass

    filas = []
    for _, row in df_c.iterrows():
        t = row["Ticker"]
        cant = float(row.get("Cantidad", 0.0) or 0.0)
        costo = float(row.get("Costo_Promedio", 0.0) or 0.0)
        precio = precios.get(t, np.nan)

        if pd.isna(precio) or cant <= 0:
            continue

        inversion = cant * costo
        valor_actual = cant * precio
        pnl_usd = valor_actual - inversion
        pnl_pct = ((precio - costo) / costo * 100.0) if costo > 0 else 0.0

        filas.append(
            {
                "Ticker": t,
                "Cantidad": cant,
                "Costo_Promedio": costo,
                "Precio_Actual": precio,
                "Inversion": inversion,
                "Valor_Actual": valor_actual,
                "PnL_USD": pnl_usd,
                "PnL_Pct": pnl_pct,
            }
        )

    return pd.DataFrame(filas).reset_index(drop=True)


# --- FUNCIÓN NOTICIAS YAHOO FINANCE ---
@st.cache_data(ttl=900)
def obtener_ultimas_noticias(symbol, limite=3):
    try:
        tk = yf.Ticker(symbol)
        noticias = tk.news or []
        noticias_procesadas = []

        for item in noticias[:limite]:
            if not isinstance(item, dict):
                continue
            content = item.get("content") or item
            titulo = content.get("title") or "Sin título"
            resumen = content.get("summary") or content.get("description") or ""
            provider_obj = content.get("provider") or {}
            proveedor = provider_obj.get("displayName") if isinstance(provider_obj, dict) else "Yahoo Finance"
            url_obj = content.get("canonicalUrl") or {}
            link = (url_obj.get("url") if isinstance(url_obj, dict) else None) or content.get("link") or "#"

            pub_date = content.get("pubDate") or ""
            if not pub_date and item.get("providerPublishTime"):
                pub_date = datetime.fromtimestamp(item["providerPublishTime"]).strftime("%Y-%m-%d %H:%M")
            elif pub_date:
                pub_date = str(pub_date).replace("T", " ").replace("Z", "")[:16]

            noticias_procesadas.append(
                {
                    "titulo": titulo,
                    "resumen": resumen,
                    "proveedor": proveedor,
                    "link": link,
                    "fecha": pub_date,
                }
            )
        return noticias_procesadas
    except Exception:
        return []


# --- GENERADOR DE SPARKLINE SVG PARA STREAMLIT ---
def generar_sparkline_svg(values):
    valid_vals = [v for v in values if isinstance(v, (int, float)) and not pd.isna(v)]
    if len(valid_vals) < 2:
        return "-"
    min_v, max_v = min(valid_vals), max(valid_vals)
    rng = max_v - min_v if max_v - min_v != 0 else 1.0
    n = len(values)

    pts = []
    circles = []
    for idx, val in enumerate(values):
        if isinstance(val, (int, float)) and not pd.isna(val):
            x = (idx / (n - 1)) * 60 + 5
            y = 22 - ((val - min_v) / rng) * 16
            pts.append(f"{x:.1f},{y:.1f}")
            circles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="#38bdf8" />')

    if len(pts) < 2:
        return "-"
    polyline = f'<polyline fill="none" stroke="#38bdf8" stroke-width="2" points="{" ".join(pts)}" />'
    return f'<svg width="70" height="26" viewBox="0 0 70 26">{polyline}{"".join(circles)}</svg>'


def safe_float(val, default=0.0):
    try:
        f = float(val)
        return default if pd.isna(f) else f
    except (TypeError, ValueError):
        return default


# --- TÍTULO Y MAPA DE CALOR INICIAL DE LA CARTERA ---
st.title("⚡ Terminal Financiero Pro")

cartera_limpia_json = normalizar_cartera(cartera_df).to_json(orient="records")
df_resumen_cartera = obtener_resumen_cartera(cartera_limpia_json)

if not df_resumen_cartera.empty:
    st.subheader("🔥 Mapa de Calor de Cartera vs. Precio de Compra")
    st.caption("Usa los botones rápidos o el selector de abajo para cambiar el activo sin hacer zoom en el mosaico.")

    total_valor = df_resumen_cartera["Valor_Actual"].sum()
    total_inv = df_resumen_cartera["Inversion"].sum()
    total_pnl_usd = total_valor - total_inv
    total_pnl_pct = (total_pnl_usd / total_inv * 100.0) if total_inv > 0 else 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("Valor Total Cartera", f"${total_valor:,.2f}")
    m2.metric("Inversión Total", f"${total_inv:,.2f}")
    m3.metric("Ganancia / Pérdida Total", f"{total_pnl_pct:+.2f}%", delta=f"${total_pnl_usd:+,.2f}")

    labels = [
        f"{r['Ticker']}<br>{r['PnL_Pct']:+.1f}%<br>${r['Valor_Actual']:,.0f}"
        for _, r in df_resumen_cartera.iterrows()
    ]
    customdata = np.stack(
        [
            df_resumen_cartera["Ticker"].values,
            df_resumen_cartera["Costo_Promedio"].values,
            df_resumen_cartera["Precio_Actual"].values,
            df_resumen_cartera["Valor_Actual"].values,
            df_resumen_cartera["PnL_USD"].values,
            df_resumen_cartera["PnL_Pct"].values,
        ],
        axis=-1,
    )

    colorscale_rojo_verde = [
        [0.0, "#b91c1c"],
        [0.35, "#ef4444"],
        [0.5, "#334155"],
        [0.65, "#10b981"],
        [1.0, "#047857"],
    ]

    fig_heatmap = go.Figure(
        go.Treemap(
            ids=df_resumen_cartera["Ticker"].tolist(),
            labels=labels,
            parents=[""] * len(df_resumen_cartera),
            values=df_resumen_cartera["Valor_Actual"],
            customdata=customdata,
            tiling=dict(packing="squarify"),
            marker=dict(
                colors=df_resumen_cartera["PnL_Pct"],
                colorscale=colorscale_rojo_verde,
                cmid=0,
                cmin=-25,
                cmax=25,
                line=dict(width=2, color="#0e1117"),
                colorbar=dict(
                    title="Rend. %",
                    ticksuffix="%",
                    thickness=14,
                    len=0.9,
                ),
            ),
            textinfo="label",
            textfont=dict(size=13, color="#ffffff"),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Rendimiento vs. Compra: <b>%{customdata[5]:+.2f}%</b> (%{customdata[4]:+$,.2f})<br>"
                "Precio Actual: $%{customdata[2]:.2f} | Costo Prom.: $%{customdata[1]:.2f}<br>"
                "Valor Posición: $%{customdata[3]:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig_heatmap.update_layout(
        template="plotly_dark",
        height=390,
        margin=dict(l=5, r=5, t=5, b=5),
    )

    evento_heatmap = st.plotly_chart(
        fig_heatmap,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key="heatmap_cartera",
    )

    # Detección robusta por point_number / id / customdata
    if evento_heatmap and evento_heatmap.selection and evento_heatmap.selection.points:
        punto = evento_heatmap.selection.points[0]
        ticker_detectado = None

        pt_num = punto.get("point_number")
        if pt_num is not None and 0 <= int(pt_num) < len(df_resumen_cartera):
            ticker_detectado = str(df_resumen_cartera.iloc[int(pt_num)]["Ticker"]).strip().upper()
        elif punto.get("id"):
            ticker_detectado = str(punto.get("id")).strip().upper()
        else:
            cd = punto.get("customdata")
            if isinstance(cd, (list, tuple, np.ndarray)) and len(cd) > 0:
                ticker_detectado = str(cd[0]).strip().upper()

        if ticker_detectado and ticker_detectado in lista_tickers and ticker_detectado != st.session_state["ticker_activo"]:
            st.session_state["ticker_activo"] = ticker_detectado
            st.rerun()

st.markdown("---")

# --- SELECTOR RÁPIDO Y BOTONES DE ACCESO DIRECTO ---
col_sel_izq, col_sel_der = st.columns([2, 3])
with col_sel_izq:
    st.selectbox(
        "⚡ Selector rápido de activo:",
        lista_tickers,
        index=lista_tickers.index(st.session_state["ticker_activo"]),
        key="selector_rapido",
        on_change=sincronizar_ticker_rapido,
    )
with col_sel_der:
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(f"Activo seleccionado actualmente: **{st.session_state['ticker_activo']}**")

# Fila de botones rápidos para cambiar sin zoom en el treemap
n_cols_btn = min(len(lista_tickers), 11)
if n_cols_btn > 0:
    cols_chips = st.columns(n_cols_btn)
    for idx_t, t_sym in enumerate(lista_tickers[:n_cols_btn]):
        es_actual = t_sym == st.session_state["ticker_activo"]
        etiqueta_btn = f"▶ {t_sym}" if es_actual else t_sym
        if cols_chips[idx_t].button(etiqueta_btn, key=f"chip_{t_sym}", use_container_width=True):
            if not es_actual:
                st.session_state["ticker_activo"] = t_sym
                st.rerun()

ticker_sel = st.session_state["ticker_activo"]

# --- EJECUCIÓN PRINCIPAL DEL ACTIVO SELECCIONADO ---
try:
    posicion = cartera_df[cartera_df["Ticker"] == ticker_sel].iloc[0]
    cant = safe_float(posicion["Cantidad"], 0.0)
    costo_prom = safe_float(posicion["Costo_Promedio"], 0.0)
    stop_loss_val = safe_float(posicion["Stop_Loss"], 0.0)

    df_w, df_d, info, financials, cashflow, balance = cargar_datos_completos(ticker_sel)
    spy_close = cargar_spy_benchmark()

    if df_d.empty or df_w.empty:
        st.error(f"No se encontraron datos históricos suficientes para {ticker_sel}.")
        st.stop()

    precio_actual = float(df_d["Close"].iloc[-1])
    es_etf = str(info.get("quoteType", "")).upper() == "ETF"

    # --- FIBONACCI ---
    df_recent = df_d.tail(252)
    max_fib = float(df_recent["High"].max())
    min_fib = float(df_recent["Low"].min())
    diff_fib = max_fib - min_fib

    fib_0 = max_fib
    fib_236 = max_fib - 0.236 * diff_fib
    fib_382 = max_fib - 0.382 * diff_fib
    fib_500 = max_fib - 0.500 * diff_fib
    fib_618 = max_fib - 0.618 * diff_fib
    fib_100 = min_fib
    ext_1618 = max_fib + 0.618 * diff_fib

    # --- STOP LOSS TÉCNICO SUGERIDO ---
    soporte_tecnico = float(df_d["Low"].tail(20).min())
    dist_soporte_pct = ((precio_actual - soporte_tecnico) / precio_actual) * 100 if precio_actual else 0.0

    high_low = df_d["High"] - df_d["Low"]
    high_close = np.abs(df_d["High"] - df_d["Close"].shift())
    low_close = np.abs(df_d["Low"] - df_d["Close"].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr_series = true_range.rolling(14).mean()
    atr_14 = float(atr_series.iloc[-1]) if not pd.isna(atr_series.iloc[-1]) else 0.0
    stop_atr = precio_actual - (2 * atr_14)
    dist_atr_pct = ((precio_actual - stop_atr) / precio_actual) * 100 if precio_actual else 0.0

    st.sidebar.markdown("---")
    st.sidebar.markdown("**💡 Sugerencias Técnicas de Stop Loss:**")
    st.sidebar.caption(f"• **Soporte Estructural (Mín 20D):** `${soporte_tecnico:.2f}` *({dist_soporte_pct:+.2f}%)*")
    st.sidebar.caption(f"• **Por Volatilidad (ATR 2x):** `${stop_atr:.2f}` *({dist_atr_pct:+.2f}%)*")

    st.header(f"🎯 Detalle del Activo: {ticker_sel}")

    # --- INDICADORES TÉCNICOS ---
    df_d["SMA_50"] = df_d["Close"].rolling(50).mean()
    df_d["SMA_200"] = df_d["Close"].rolling(200).mean()
    sma50 = float(df_d["SMA_50"].iloc[-1]) if not pd.isna(df_d["SMA_50"].iloc[-1]) else precio_actual
    sma200 = float(df_d["SMA_200"].iloc[-1]) if not pd.isna(df_d["SMA_200"].iloc[-1]) else precio_actual

    # RSI Semanal
    delta_w = df_w["Close"].diff()
    gain = delta_w.where(delta_w > 0, 0.0).rolling(14).mean()
    loss = (-delta_w.where(delta_w < 0, 0.0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df_w["RSI"] = 100 - (100 / (1 + rs))

    # MACD Semanal
    ema12 = df_w["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df_w["Close"].ewm(span=26, adjust=False).mean()
    df_w["MACD"] = ema12 - ema26
    df_w["Signal"] = df_w["MACD"].ewm(span=9, adjust=False).mean()

    # Divergencias en ventana de 8 semanas
    w_close_8 = df_w["Close"].tail(8)
    w_rsi_8 = df_w["RSI"].tail(8)
    div_alcista = False
    div_bajista = False
    if len(w_close_8) >= 2 and not pd.isna(w_rsi_8.iloc[0]) and not pd.isna(w_rsi_8.iloc[-1]):
        div_alcista = (w_close_8.iloc[-1] < w_close_8.iloc[0]) and (w_rsi_8.iloc[-1] > w_rsi_8.iloc[0])
        div_bajista = (w_close_8.iloc[-1] > w_close_8.iloc[0]) and (w_rsi_8.iloc[-1] < w_rsi_8.iloc[0])

    # --- RESUMEN DE POSICIÓN ---
    inv_total = cant * costo_prom
    val_act = cant * precio_actual
    pnl_usd = val_act - inv_total
    pnl_pct = (pnl_usd / inv_total * 100) if inv_total > 0 else 0.0
    dist_stop_config_pct = ((precio_actual - stop_loss_val) / precio_actual) * 100 if precio_actual else 0.0

    st.subheader(f"📊 Rendimiento Posición: {ticker_sel}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio Actual", f"${precio_actual:.2f}")
    c2.metric("Rendimiento Posición", f"{pnl_pct:+.2f}%", delta=f"${pnl_usd:,.2f}")
    c3.metric("Distancia a Stop Configurado", f"{dist_stop_config_pct:+.2f}%", delta=f"${stop_loss_val:.2f} Nivel Stop")
    c4.metric("Distancia a Soporte Técnico", f"{dist_soporte_pct:+.2f}%", delta=f"${soporte_tecnico:.2f} Mín 20D")

    st.markdown("---")

    # --- INTERPRETACIÓN ESTRUCTURAL Y FIBONACCI ---
    st.subheader(f"📐 Interpretación de Estructuras y Niveles Clave ({ticker_sel})")

    niveles_fib = [fib_100, fib_618, fib_500, fib_382, fib_236, fib_0, ext_1618]
    resistencia_proxima = min([n for n in niveles_fib if n > precio_actual], default=ext_1618)
    soporte_proximo = max([n for n in niveles_fib if n < precio_actual], default=fib_100)

    dist_res_pct = ((resistencia_proxima - precio_actual) / precio_actual) * 100 if precio_actual else 0.0
    dist_sop_pct = ((precio_actual - soporte_proximo) / precio_actual) * 100 if precio_actual else 0.0

    f1, f2, f3 = st.columns(3)
    f1.metric("🎯 Próxima Resistencia Objetiva", f"${resistencia_proxima:.2f}", delta=f"+{dist_res_pct:.2f}% distancia")
    f2.metric("🛡️ Próximo Soporte Fibonacci", f"${soporte_proximo:.2f}", delta=f"-{dist_sop_pct:.2f}% distancia")
    f3.metric(
        "📏 Zona Dorada Fib (61.8%)",
        f"${fib_618:.2f}",
        delta="Punto crítico de recarga" if precio_actual >= fib_618 else "Bajo zona dorada",
    )

    pct_extension = ((ext_1618 - precio_actual) / precio_actual) * 100 if precio_actual else 0.0
    estado_chartista = (
        "El activo muestra fortaleza alcista manteniéndose sobre la Zona Dorada (61.8%)."
        if precio_actual >= fib_618
        else "El activo ha penetrado niveles clave de retroceso, lo que sugiere cautela antes de abrir nuevas posiciones."
    )

    st.info(
        f"🔍 **Diagnóstico Táctico Estructural:**\n\n"
        f"• **Situación de Fibonacci:** El precio cotiza entre el soporte de **${soporte_proximo:.2f}** y la resistencia de **${resistencia_proxima:.2f}**.\n\n"
        f"• **Techo Clave:** Un quiebre confirmado del máximo reciente en **${max_fib:.2f}** proyecta un objetivo por **Extensión de Fibonacci** hacia **${ext_1618:.2f}** ({pct_extension:+.1f}%).\n\n"
        f"• **Estructura Chartista:** {estado_chartista}"
    )

    st.markdown("---")

    # --- SEMÁFORO TÁCTICO MODULAR ---
    st.subheader(f"🚥 Semáforo Táctico Modular: {ticker_sel}")
    s1, s2, s3, s4 = st.columns(4)

    with s1:
        st.markdown("**1. Tendencia de Precio**")
        dist_sma50_pct = ((precio_actual - sma50) / sma50) * 100 if sma50 else 0.0
        if precio_actual >= sma50:
            st.success(f"🟢 **ALCISTA**\n+{dist_sma50_pct:.2f}% sobre SMA 50.")
        elif precio_actual >= sma200:
            st.warning("🟡 **CORRECCIÓN**\nSobre SMA 200, bajo SMA 50.")
        else:
            dist_sma200_pct = ((precio_actual - sma200) / sma200) * 100 if sma200 else 0.0
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
        if stop_loss_val <= 0:
            st.info("⚪ **SIN STOP CONFIGURADO**\nDefine un nivel en la barra lateral.")
        elif precio_actual <= stop_loss_val:
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
        rend_ticker = ((df_d["Close"].iloc[-1] - df_d["Close"].iloc[0]) / df_d["Close"].iloc[0]) * 100
        rend_spy = (
            ((spy_close.iloc[-1] - spy_close.iloc[0]) / spy_close.iloc[0]) * 100
            if not spy_close.empty
            else 0.0
        )
        alpha = rend_ticker - rend_spy

        e1, e2, e3 = st.columns(3)
        e1.metric(f"Rendimiento 5A ({ticker_sel})", f"{rend_ticker:+.2f}%")
        e2.metric("Rendimiento 5A (SPY)", f"{rend_spy:+.2f}%")
        e3.metric("Alpha Relativo", f"{alpha:+.2f}%", delta="Alfa Positivo" if alpha > 0 else "Alfa Negativo")
    else:
        st.subheader(f"🏢 Matriz Fundamental Avanzada ({ticker_sel})")

        cols_fin = list(financials.columns[:3]) if not financials.empty else []
        years = [c.strftime("%Y") for c in reversed(cols_fin)] if len(cols_fin) > 0 else ["Año-2", "Año-1", "Anterior"]
        while len(years) < 3:
            years.insert(0, f"Año-{3 - len(years)}")
        headers_years = years[-3:] + ["TTM (Actual)"]

        def get_raw_series(df_source, row_label, scale=1e9):
            if df_source.empty or row_label not in df_source.index or len(cols_fin) == 0:
                return [np.nan] * 3
            res = []
            for col in reversed(cols_fin):
                val = df_source.loc[row_label, col]
                res.append(float(val) / scale if pd.notna(val) else np.nan)
            while len(res) < 3:
                res.insert(0, np.nan)
            return res[-3:]

        rev_list = get_raw_series(financials, "Total Revenue", 1e9) + [
            info["totalRevenue"] / 1e9 if info.get("totalRevenue") else np.nan
        ]
        eps_list = get_raw_series(financials, "Basic EPS", 1) + [
            info["trailingEps"] if info.get("trailingEps") is not None else np.nan
        ]
        fcf_list = get_raw_series(cashflow, "Free Cash Flow", 1e9) + [
            info["freeCashflow"] / 1e9 if info.get("freeCashflow") else np.nan
        ]
        ebitda_list = get_raw_series(financials, "EBITDA", 1e9) + [
            info["ebitda"] / 1e9 if info.get("ebitda") else np.nan
        ]
        debt_list = get_raw_series(balance, "Total Debt", 1e9) + [
            info["totalDebt"] / 1e9 if info.get("totalDebt") else np.nan
        ]

        gross_list, op_list = [], []
        for col in reversed(cols_fin):
            if not financials.empty and "Gross Profit" in financials.index and "Total Revenue" in financials.index:
                gp = financials.loc["Gross Profit", col]
                rev = financials.loc["Total Revenue", col]
                gross_list.append((gp / rev) * 100 if pd.notna(gp) and pd.notna(rev) and rev != 0 else np.nan)
            else:
                gross_list.append(np.nan)

            if not financials.empty and "Operating Income" in financials.index and "Total Revenue" in financials.index:
                op = financials.loc["Operating Income", col]
                rev = financials.loc["Total Revenue", col]
                op_list.append((op / rev) * 100 if pd.notna(op) and pd.notna(rev) and rev != 0 else np.nan)
            else:
                op_list.append(np.nan)

        while len(gross_list) < 3:
            gross_list.insert(0, np.nan)
        while len(op_list) < 3:
            op_list.insert(0, np.nan)

        gross_list = gross_list[-3:] + [info["grossMargins"] * 100 if info.get("grossMargins") is not None else np.nan]
        op_list = op_list[-3:] + [info["operatingMargins"] * 100 if info.get("operatingMargins") is not None else np.nan]

        groups = [
            {
                "title": "Indicadores de Crecimiento",
                "metrics": [
                    {"name": "Ventas / Ingresos", "unit": "$B", "vals": rev_list},
                    {"name": "EPS (Ganancia por Acción)", "unit": "$", "vals": eps_list},
                ],
            },
            {
                "title": "Rentabilidad y Ventaja Competitiva",
                "metrics": [
                    {"name": "Margen Bruto", "unit": "%", "vals": gross_list},
                    {"name": "Margen Operativo", "unit": "%", "vals": op_list},
                ],
            },
            {
                "title": "Generación de Caja",
                "metrics": [
                    {"name": "Free Cash Flow (FCF)", "unit": "$B", "vals": fcf_list},
                ],
            },
            {
                "title": "Estructura de Deuda",
                "metrics": [
                    {"name": "EBITDA", "unit": "$B", "vals": ebitda_list},
                    {"name": "Deuda Total", "unit": "$B", "vals": debt_list, "is_inverse": True},
                ],
            },
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
            html_code += f'<tr><td colspan="6" class="fund-group-header">{grp["title"]}</td></tr>'
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
                            prev = vals[idx - 1]
                            if pd.isna(prev) or v == prev:
                                cell_class = "val-neutral"
                            else:
                                is_better = (v < prev) if is_inv else (v > prev)
                                cell_class = "val-pos" if is_better else "val-neg"

                    html_code += f'<td><span class="val-pill {cell_class}">{val_str}</span></td>'

                spark = generar_sparkline_svg(vals)
                html_code += f'<td style="text-align: center; vertical-align: middle;">{spark}</td></tr>'

        html_code += "</tbody></table>"
        st.markdown(html_code, unsafe_allow_html=True)

        # --- ANÁLISIS DINÁMICO BASADO EN TENDENCIAS REALES ---
        st.markdown(f"### 📋 Lectura de Tendencias Fundamentals ({ticker_sel})")

        def evaluar_tendencia(serie):
            validos = [v for v in serie if not pd.isna(v)]
            if len(validos) < 2:
                return "sin_datos", 0.0
            inicio, fin = validos[0], validos[-1]
            if inicio == 0:
                return "estable", 0.0
            var_pct = ((fin - inicio) / abs(inicio)) * 100
            if var_pct > 5:
                return "creciente", var_pct
            elif var_pct < -5:
                return "decreciente", var_pct
            return "estable", var_pct

        tend_rev, var_rev = evaluar_tendencia(rev_list)
        tend_eps, var_eps = evaluar_tendencia(eps_list)
        _, _ = evaluar_tendencia(gross_list)
        tend_op, var_op = evaluar_tendencia(op_list)
        tend_fcf, var_fcf = evaluar_tendencia(fcf_list)
        tend_debt, var_debt = evaluar_tendencia(debt_list)

        if tend_rev == "creciente" and tend_eps == "creciente":
            diag_crecimiento = (
                f"**Expansión sólida:** Las ventas crecieron un **{var_rev:+.1f}%** acumulado en la serie, "
                f"alineadas con una mejora del **{var_eps:+.1f}%** en el EPS."
            )
        elif tend_rev == "creciente" and tend_eps == "decreciente":
            diag_crecimiento = (
                f"**Crecimiento bajo presión:** A pesar de escalar ingresos (+{var_rev:.1f}%), "
                f"el EPS retrocedió un **{var_eps:+.1f}%**, señal de mayor costo operativo o dilución."
            )
        elif tend_rev == "decreciente":
            diag_crecimiento = (
                f"**Contracción en top-line:** Los ingresos cayeron un **{var_rev:.1f}%** en el período, "
                f"lo que exige atención a la demanda."
            )
        else:
            diag_crecimiento = "**Estabilidad operativa:** Los ingresos y el EPS se mantuvieron sin cambios drásticos."

        if tend_op == "creciente":
            diag_margen = (
                f"**Eficiencia al alza:** El margen operativo aumentó un **{var_op:+.1f}%**, "
                f"mostrando apalancamiento operativo."
            )
        elif tend_op == "decreciente":
            diag_margen = (
                f"**Compresión de márgenes:** El margen operativo cedió un **{var_op:+.1f}%**, "
                f"reflejando mayor presión de costos."
            )
        else:
            diag_margen = "**Márgenes consistentes:** La rentabilidad operativa permaneció estable durante la serie."

        if tend_fcf == "creciente" and tend_debt != "creciente":
            diag_caja = (
                f"**Generación limpia de caja:** El FCF se expandió un **{var_fcf:+.1f}%** "
                f"mientras la deuda se mantuvo bajo control ({var_debt:+.1f}%)."
            )
        elif tend_debt == "creciente":
            diag_caja = (
                f"**Incremento del apalancamiento:** La deuda subió un **{var_debt:+.1f}%**. "
                f"Conviene monitorear la cobertura de intereses contra la caja generada."
            )
        else:
            diag_caja = (
                f"**Flujo de caja sostenible:** La generación de Free Cash Flow registra una variación "
                f"de **{var_fcf:+.1f}%** en el período."
            )

        st.markdown(
            f"• **Crecimiento e Ingresos:** {diag_crecimiento}\n\n"
            f"• **Rentabilidad y Márgenes:** {diag_margen}\n\n"
            f"• **Caja y Estructura Financiera:** {diag_caja}"
        )

    st.markdown("---")

    # --- GRÁFICO DE VELAS (5 AÑOS) CON FIBONACCI ---
    st.subheader("📈 Gráfico de Velas (5 Años) con Estructura de Fibonacci")
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

    fig.add_trace(
        go.Candlestick(
            x=df_d.index, open=df_d["Open"], high=df_d["High"], low=df_d["Low"], close=df_d["Close"], name="Precio"
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=df_d.index, y=df_d["SMA_50"], line=dict(color="#FF9900", width=1.5), name="SMA 50"), row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df_d.index, y=df_d["SMA_200"], line=dict(color="#0066FF", width=1.5), name="SMA 200"),
        row=1,
        col=1,
    )

    fig.add_hline(y=max_fib, line_dash="dash", line_color="red", annotation_text=f"Fib 0% (${max_fib:.1f})", row=1, col=1)
    fig.add_hline(
        y=fib_382, line_dash="dash", line_color="orange", annotation_text=f"Fib 38.2% (${fib_382:.1f})", row=1, col=1
    )
    fig.add_hline(
        y=fib_618, line_dash="dash", line_color="gold", annotation_text=f"Fib 61.8% (${fib_618:.1f})", row=1, col=1
    )
    fig.add_hline(
        y=min_fib, line_dash="dash", line_color="green", annotation_text=f"Fib 100% (${min_fib:.1f})", row=1, col=1
    )

    fig.add_trace(
        go.Scatter(x=df_w.index, y=df_w["RSI"], line=dict(color="#AB63FA", width=1.5), name="RSI (Semanal)"),
        row=2,
        col=1,
    )
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.add_trace(
        go.Scatter(x=df_w.index, y=df_w["MACD"], line=dict(color="#00FFCC", width=1), name="MACD"), row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=df_w.index, y=df_w["Signal"], line=dict(color="#FF0055", width=1), name="Signal"), row=3, col=1
    )

    fig.update_layout(
        template="plotly_dark",
        height=700,
        xaxis_rangeslider_visible=True,
        xaxis_rangeslider_thickness=0.05,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- MÓDULO DE ÚLTIMAS NOTICIAS Y INFORME RESUMIDO ---
    st.markdown("---")
    st.subheader(f"📰 Últimas Noticias Bursátiles ({ticker_sel})")

    noticias = obtener_ultimas_noticias(ticker_sel, limite=3)

    if len(noticias) > 0:
        cols_noticias = st.columns(len(noticias))
        for idx, noticia in enumerate(noticias):
            with cols_noticias[idx]:
                st.markdown(
                    f"""
                    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; height: 100%;">
                        <span style="color: #38bdf8; font-size: 11px; font-weight: bold;">{noticia['proveedor']}</span>
                        <span style="color: #94a3b8; font-size: 11px; float: right;">{noticia['fecha']}</span>
                        <h4 style="font-size: 14px; margin: 10px 0; color: #f8fafc;">{noticia['titulo']}</h4>
                        <a href="{noticia['link']}" target="_blank" style="color: #34d399; text-decoration: none; font-size: 12px; font-weight: bold;">Leer noticia completa ↗</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)
        items_resumen = []
        for n in noticias:
            texto_cuerpo = n["resumen"] if n["resumen"] else n["titulo"]
            items_resumen.append(f"• **{n['titulo']}** ({n['proveedor']}): {texto_cuerpo}")

        cuerpo_informe = "\n\n".join(items_resumen)

        st.info(f"💡 **Informe Resumido del Mercado ({ticker_sel}):**\n\n{cuerpo_informe}")
    else:
        st.info("No se encontraron noticias recientes disponibles para este activo.")

except Exception as e:
    st.error(f"Error al cargar el activo seleccionado: {e}")

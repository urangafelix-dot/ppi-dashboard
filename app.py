"""
PPI Portfolio Live
Dashboard profesional de monitoreo de cartera.
Todo expresado en dólares al tipo de cambio MEP.
"""

from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

from ppi_wrapper import create_client_from_env

# -----------------------------------------------------------------------------
# Page config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PPI Portfolio",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_dotenv()

# -----------------------------------------------------------------------------
# Custom CSS
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #0e0e0e;
        color: #e8e8e8;
    }
    h1, h2, h3 {
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: -0.02em;
        color: #f5f5f5 !important;
    }
    h1 { font-size: 1.8rem !important; margin-bottom: 0.2rem !important; }
    [data-testid="stMetric"] {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 10px;
        padding: 16px 20px;
    }
    [data-testid="stMetricLabel"] {
        color: #999 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    [data-testid="stMetricValue"] {
        color: #f5f5f5 !important;
        font-size: 1.4rem !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #222;
    }
    .stDataFrame { border: 1px solid #2a2a2a; border-radius: 8px; }
    hr { border-color: #2a2a2a !important; margin: 1.4rem 0 !important; }
    .stCaption { color: #777 !important; }

    /* Alert cards */
    .alert-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
    .alert-title {
        font-size: 0.95rem;
        font-weight: 500;
        color: #f0f0f0;
        margin-bottom: 4px;
    }
    .alert-desc {
        font-size: 0.85rem;
        color: #999;
        line-height: 1.4;
    }
    .alert-high { border-left: 3px solid #e74c3c; }
    .alert-medium { border-left: 3px solid #f39c12; }
    .alert-low { border-left: 3px solid #2ecc71; }
    .alert-info { border-left: 3px solid #3498db; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Configuración")
    refresh_seconds = st.slider("Auto-refresh (seg)", 30, 300, 60, 30)
    st.markdown("---")
    st.caption("Solo lectura · USD MEP")

st_autorefresh(interval=refresh_seconds * 1000, key="data_refresh")


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def fmt_usd(value: float) -> str:
    try:
        return f"US$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(value)


def fmt_ars(value: float) -> str:
    try:
        return f"$ {value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(value)


def fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


# -----------------------------------------------------------------------------
# Classification helpers
# -----------------------------------------------------------------------------
US_TICKERS = {
    "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "NVDA", "AMD",
    "QQQ", "SPY", "DIA", "IWM", "XLF", "XLK", "XLE", "XLV", "XLI", "XLY",
    "XLP", "XLU", "XLB", "XLRE", "QCOM", "AVGO", "NFLX", "CRM", "ADBE",
    "INTC", "CSCO", "PEP", "KO", "JNJ", "UNH", "V", "MA", "JPM", "BAC",
    "WMT", "HD", "DIS", "NKE", "PFE", "MRK", "ABBV", "TMO", "COST", "MCD",
    "SNOW", "SHOP", "SQ", "PYPL", "UBER", "LYFT", "COIN", "RIVN", "LCID",
    "PLTR", "SOFI", "HOOD", "RBLX", "U", "NET", "DDOG", "ZS", "CRWD",
    "MELI", "GLOB", "DESP"
}

TECH_TICKERS = {
    "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "NVDA", "AMD",
    "QQQ", "XLK", "QCOM", "AVGO", "NFLX", "CRM", "ADBE", "INTC", "CSCO",
    "SNOW", "SHOP", "SQ", "PYPL", "UBER", "COIN", "PLTR", "SOFI", "HOOD",
    "RBLX", "U", "NET", "DDOG", "ZS", "CRWD", "SNDK", "RGTI"
}

ARG_TICKERS = {
    "YPFD", "GGAL", "BMA", "SUPV", "BBAR", "TECO2", "PAMP", "TXAR", "ALUA",
    "CRES", "EDN", "LOMA", "MIRG", "COME", "TRAN", "CEPU", "TGSU2", "HARG",
    "IRSA", "CTIO", "BYMA", "VALO", "BHIP", "MORI", "METR", "AGRO", "SAMI"
}


def classify_instrument(ticker: str, group: str) -> Tuple[str, str]:
    """Returns (tipo, geografia)"""
    t = (ticker or "").upper().strip()
    g = (group or "").upper()

    # Tipo
    if "CEDEAR" in g or t in US_TICKERS:
        tipo = "CEDEARs"
    elif "FCI" in g or "FONDO" in g:
        tipo = "FCI"
    elif "BONO" in g or "LETRA" in g or "ON" in g:
        tipo = "Bonos"
    elif "ACCION" in g or t in ARG_TICKERS:
        tipo = "Acciones"
    else:
        tipo = "Otros"

    # Geografía
    if t in US_TICKERS or "CEDEAR" in g:
        geo = "Estados Unidos"
    elif t in ARG_TICKERS or "ACCION" in g or "BONO" in g:
        geo = "Argentina"
    elif t in {"MELI", "GLOB", "DESP"}:
        geo = "LatAm"
    else:
        geo = "Otros"

    return tipo, geo


def generate_alerts(
    total_usd: float,
    cash_usd: float,
    instruments: List[Dict],
    mep: float,
) -> List[Dict]:
    """Genera alertas y recomendaciones basadas en reglas simples."""
    alerts = []
    if total_usd <= 0:
        return alerts

    # Ordenar por peso
    sorted_inst = sorted(instruments, key=lambda x: x["Monto USD"], reverse=True)
    top = sorted_inst[0] if sorted_inst else None

    # 1. Concentración en un solo activo
    if top and top["Peso %"] >= 12:
        severity = "high" if top["Peso %"] >= 18 else "medium"
        alerts.append({
            "severity": severity,
            "title": f"Alta concentración en {top['Ticker']}",
            "desc": f"{top['Ticker']} representa el {top['Peso %']:.1f}% de la cartera. Considerá reducir exposición si supera tu tolerancia al riesgo."
        })

    # 2. Liquidez
    liq_pct = (cash_usd / (total_usd + cash_usd)) * 100 if (total_usd + cash_usd) > 0 else 0
    if liq_pct < 3:
        alerts.append({
            "severity": "high",
            "title": "Liquidez muy baja",
            "desc": f"Solo tenés {liq_pct:.1f}% en efectivo. Recomendable mantener al menos 5-8% para oportunidades."
        })
    elif liq_pct < 6:
        alerts.append({
            "severity": "medium",
            "title": "Liquidez ajustada",
            "desc": f"Liquidez actual: {liq_pct:.1f}%. Podría ser conveniente aumentar el colchón de efectivo."
        })
    elif liq_pct > 20:
        alerts.append({
            "severity": "info",
            "title": "Exceso de liquidez",
            "desc": f"Tenés {liq_pct:.1f}% en efectivo. Considerá ponerlo a trabajar en un FCI money market o bonos cortos."
        })

    # 3. Exposición a Tecnología
    tech_usd = sum(i["Monto USD"] for i in instruments if i["Ticker"] in TECH_TICKERS)
    tech_pct = (tech_usd / total_usd) * 100 if total_usd > 0 else 0
    if tech_pct >= 35:
        alerts.append({
            "severity": "medium",
            "title": "Alta exposición a Tecnología",
            "desc": f"El {tech_pct:.1f}% de la cartera está en tech (incluyendo Tesla y ETFs sectoriales). El sector es volátil."
        })

    # 4. Exposición a Argentina
    arg_usd = sum(i["Monto USD"] for i in instruments if i["Geografia"] == "Argentina")
    arg_pct = (arg_usd / total_usd) * 100 if total_usd > 0 else 0
    if arg_pct >= 45:
        alerts.append({
            "severity": "medium",
            "title": "Elevada exposición a Argentina",
            "desc": f"{arg_pct:.1f}% de la cartera está en activos locales. Considerá diversificar más internacionalmente."
        })

    # 5. Si no hay alertas fuertes, dar una positiva
    if not any(a["severity"] in ("high", "medium") for a in alerts):
        alerts.append({
            "severity": "low",
            "title": "Cartera relativamente equilibrada",
            "desc": "No se detectaron concentraciones extremas ni problemas de liquidez relevantes."
        })

    return alerts


# -----------------------------------------------------------------------------
# Data loading
# -----------------------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner="Actualizando cartera...")
def load_portfolio_data():
    client = create_client_from_env()
    client.login()
    balances = client.get_available_balance()
    positions_raw = client.get_balance_and_positions()
    movements = client.get_movements(days=15)
    active_orders = client.get_active_orders()
    mep_rate = client.get_mep_rate()
    return {
        "account_number": client.account_number,
        "balances": balances,
        "positions_raw": positions_raw,
        "movements": movements,
        "active_orders": active_orders,
        "mep_rate": mep_rate,
        "timestamp": datetime.now(),
    }


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
try:
    data = load_portfolio_data()
except Exception as e:
    st.error("Error de conexión con PPI")
    st.code(str(e))
    st.stop()

account = data["account_number"]
mep = data["mep_rate"] or 1.0
ts = data["timestamp"].strftime("%d/%m/%Y %H:%M")

# Process positions
positions_raw = data["positions_raw"]
all_instruments = []
total_ars = 0.0
total_usd = 0.0

if positions_raw and "groupedInstruments" in positions_raw:
    for group in positions_raw["groupedInstruments"]:
        group_name = group.get("name", "Otros")
        for inst in group.get("instruments", []):
            amount = float(inst.get("amount", 0) or 0)
            usd_amount = amount / mep if mep > 1 else amount
            total_ars += amount
            total_usd += usd_amount
            ticker = inst.get("ticker", "")
            tipo, geo = classify_instrument(ticker, group_name)
            all_instruments.append({
                "Grupo": group_name,
                "Ticker": ticker,
                "Tipo": tipo,
                "Geografia": geo,
                "Cantidad": float(inst.get("quantity", 0) or 0),
                "Precio": float(inst.get("price", 0) or 0),
                "Monto ARS": amount,
                "Monto USD": round(usd_amount, 2),
            })

# Calculate weights
if total_usd > 0:
    for inst in all_instruments:
        inst["Peso %"] = round((inst["Monto USD"] / total_usd) * 100, 2)

# Cash
cash_ars = 0.0
cash_usd = 0.0
for bal in (data["balances"] or []):
    name = (bal.get("name") or "").lower()
    amount = float(bal.get("amount", 0) or 0)
    symbol = str(bal.get("symbol", "")).upper()
    if "peso" in name or symbol in ("$", "ARS"):
        cash_ars += amount
    else:
        cash_usd += amount

cash_usd_total = cash_usd + (cash_ars / mep if mep > 1 else 0)
grand_total_usd = total_usd + cash_usd_total

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.markdown("# Portfolio")
st.caption(f"Cuenta {account}  ·  {ts}  ·  Dólar MEP {mep:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown(f"""
<div style="margin: 1.5rem 0 0.5rem 0;">
    <div style="font-size: 2.8rem; font-weight: 500; letter-spacing: -0.03em; color: #f5f5f5;">
        {fmt_ars(total_ars + cash_ars)}
    </div>
    <div style="font-size: 1.1rem; color: #888; margin-top: 0.2rem;">
        {fmt_usd(grand_total_usd)} al dólar MEP
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Top metrics
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Liquidez", fmt_usd(cash_usd_total))
with c2:
    st.metric("Posiciones", fmt_usd(total_usd))
with c3:
    st.metric("Dólar MEP", f"{mep:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
with c4:
    st.metric("Instrumentos", str(len(all_instruments)))

st.markdown("---")

# -----------------------------------------------------------------------------
# Alertas y Recomendaciones
# -----------------------------------------------------------------------------
st.markdown("### Alertas y recomendaciones")

alerts = generate_alerts(total_usd, cash_usd_total, all_instruments, mep)

if alerts:
    cols = st.columns(min(3, len(alerts)))
    for i, alert in enumerate(alerts[:3]):
        with cols[i % len(cols)]:
            severity_class = f"alert-{alert['severity']}"
            st.markdown(f"""
            <div class="alert-card {severity_class}">
                <div class="alert-title">{alert['title']}</div>
                <div class="alert-desc">{alert['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.caption("Sin alertas relevantes en este momento.")

st.markdown("---")

# -----------------------------------------------------------------------------
# Composición
# -----------------------------------------------------------------------------
st.markdown("### Composición de la cartera")

if all_instruments:
    df = pd.DataFrame(all_instruments)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**Por tipo de instrumento**")
        by_tipo = df.groupby("Tipo")["Monto USD"].sum().reset_index()
        by_tipo = by_tipo.sort_values("Monto USD", ascending=False)
        # Agregar liquidez
        by_tipo = pd.concat([
            by_tipo,
            pd.DataFrame([{"Tipo": "Liquidez", "Monto USD": cash_usd_total}])
        ], ignore_index=True)

        fig1 = px.pie(
            by_tipo, values="Monto USD", names="Tipo", hole=0.55,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig1.update_traces(textposition="inside", textinfo="percent+label",
                           marker=dict(line=dict(color="#0e0e0e", width=2)))
        fig1.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#ccc", showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10), height=280
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_right:
        st.markdown("**Por geografía**")
        by_geo = df.groupby("Geografia")["Monto USD"].sum().reset_index()
        by_geo = by_geo.sort_values("Monto USD", ascending=False)

        fig2 = px.pie(
            by_geo, values="Monto USD", names="Geografia", hole=0.55,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label",
                           marker=dict(line=dict(color="#0e0e0e", width=2)))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#ccc", showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10), height=280
        )
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# Tilts / Concentración
# -----------------------------------------------------------------------------
st.markdown("### Concentración y tilts")

if all_instruments and total_usd > 0:
    df = pd.DataFrame(all_instruments)
    top = df.sort_values("Monto USD", ascending=False).iloc[0]
    tech_usd = df[df["Ticker"].isin(TECH_TICKERS)]["Monto USD"].sum()
    tech_pct = (tech_usd / total_usd) * 100
    arg_usd = df[df["Geografia"] == "Argentina"]["Monto USD"].sum()
    arg_pct = (arg_usd / total_usd) * 100
    us_usd = df[df["Geografia"] == "Estados Unidos"]["Monto USD"].sum()
    us_pct = (us_usd / total_usd) * 100

    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.metric("Mayor posición", f"{top['Ticker']}", delta=fmt_pct(top["Peso %"]))
    with t2:
        st.metric("Exposición Tech", fmt_pct(tech_pct))
    with t3:
        st.metric("Argentina", fmt_pct(arg_pct))
    with t4:
        st.metric("Estados Unidos", fmt_pct(us_pct))

st.markdown("---")

# -----------------------------------------------------------------------------
# Posiciones
# -----------------------------------------------------------------------------
st.markdown("### Posiciones")

if all_instruments:
    df_pos = pd.DataFrame(all_instruments).sort_values("Monto USD", ascending=False)
    show_cols = ["Ticker", "Tipo", "Geografia", "Cantidad", "Precio", "Monto USD", "Monto ARS", "Peso %"]
    st.dataframe(
        df_pos[show_cols].style.format({
            "Cantidad": "{:,.2f}",
            "Precio": "{:,.2f}",
            "Monto USD": "{:,.2f}",
            "Monto ARS": "{:,.0f}",
            "Peso %": "{:.2f}%",
        }),
        use_container_width=True,
        hide_index=True,
        height=min(420, 50 + len(df_pos) * 35),
    )
else:
    st.info("Sin posiciones abiertas.")

st.markdown("---")

# -----------------------------------------------------------------------------
# Órdenes y movimientos
# -----------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.markdown("### Órdenes activas")
    active = data["active_orders"]
    if active:
        df_orders = pd.DataFrame(active)
        cols = [c for c in ["ticker", "operation", "status", "quantity", "price", "settlement"] if c in df_orders.columns]
        st.dataframe(df_orders[cols], use_container_width=True, hide_index=True)
    else:
        st.caption("No hay órdenes activas.")

with right:
    st.markdown("### Últimos movimientos")
    movs = data["movements"]
    if movs:
        df_mov = pd.DataFrame(movs)
        cols = [c for c in ["settlementDate", "description", "ticker", "amount"] if c in df_mov.columns]
        st.dataframe(df_mov[cols].head(12), use_container_width=True, hide_index=True)
    else:
        st.caption("Sin movimientos recientes.")

st.markdown("---")
st.caption("Solo lectura · API oficial PPI · MEP calculado con AL30/AL30D")

"""
PPI Portfolio Live
Dashboard profesional de monitoreo de cartera.
Todo expresado en dólares al tipo de cambio MEP.
"""

import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

from ppi_wrapper import create_client_from_env

st.set_page_config(
    page_title="PPI Portfolio",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_dotenv()

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
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 0.2rem !important;
    }
    [data-testid="stMetric"] {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 10px;
        padding: 16px 20px;
    }
    [data-testid="stMetricLabel"] {
        color: #999 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    [data-testid="stMetricValue"] {
        color: #f5f5f5 !important;
        font-size: 1.5rem !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #222;
    }
    .stDataFrame {
        border: 1px solid #2a2a2a;
        border-radius: 8px;
    }
    hr {
        border-color: #2a2a2a !important;
        margin: 1.5rem 0 !important;
    }
    .stCaption {
        color: #777 !important;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Configuración")
    st.markdown("")
    refresh_seconds = st.slider(
        "Auto-refresh (seg)",
        min_value=30,
        max_value=300,
        value=60,
        step=30,
    )
    st.markdown("---")
    st.caption("Solo lectura")
    st.caption("Valores en USD MEP")

st_autorefresh(interval=refresh_seconds * 1000, key="data_refresh")

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

try:
    data = load_portfolio_data()
except Exception as e:
    st.error("Error de conexión con PPI")
    st.code(str(e))
    st.stop()

account = data["account_number"]
mep = data["mep_rate"] or 1.0
ts = data["timestamp"].strftime("%d/%m/%Y %H:%M")

st.markdown("# Portfolio")
st.caption(f"Cuenta {account}  ·  {ts}  ·  Dólar MEP {mep:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

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
            all_instruments.append({
                "Grupo": group_name,
                "Ticker": inst.get("ticker", ""),
                "Cantidad": float(inst.get("quantity", 0) or 0),
                "Precio": float(inst.get("price", 0) or 0),
                "Monto ARS": amount,
                "Monto USD": round(usd_amount, 2),
            })

cash_ars = 0.0
cash_usd = 0.0
balances = data["balances"] or []

for bal in balances:
    name = (bal.get("name") or "").lower()
    amount = float(bal.get("amount", 0) or 0)
    symbol = str(bal.get("symbol", "")).upper()
    if "peso" in name or symbol in ("$", "ARS"):
        cash_ars += amount
    else:
        cash_usd += amount

cash_usd_total = cash_usd + (cash_ars / mep if mep > 1 else 0)

st.markdown(f"""
<div style="margin: 1.5rem 0 0.5rem 0;">
    <div style="font-size: 2.8rem; font-weight: 500; letter-spacing: -0.03em; color: #f5f5f5;">
        {fmt_ars(total_ars + cash_ars)}
    </div>
    <div style="font-size: 1.1rem; color: #888; margin-top: 0.2rem;">
        {fmt_usd(total_usd + cash_usd_total)} al dólar MEP
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

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
st.markdown("### Posiciones")

if all_instruments:
    df_pos = pd.DataFrame(all_instruments)
    df_pos = df_pos.sort_values("Monto USD", ascending=False)
    if total_usd > 0:
        df_pos["Peso %"] = (df_pos["Monto USD"] / total_usd * 100).round(2)
    show_cols = ["Ticker", "Grupo", "Cantidad", "Precio", "Monto USD", "Monto ARS", "Peso %"]
    show_cols = [c for c in show_cols if c in df_pos.columns]
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
    if total_usd > 0 and len(df_pos) > 1:
        fig = px.pie(df_pos.head(12), values="Monto USD", names="Ticker", hole=0.55)
        fig.update_traces(textposition="inside", textinfo="percent", marker=dict(line=dict(color="#0e0e0e", width=2)))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#ccc",
            showlegend=True,
            legend=dict(orientation="h", y=-0.1),
            margin=dict(t=20, b=20, l=20, r=20),
            height=340,
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Sin posiciones abiertas.")

st.markdown("---")

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

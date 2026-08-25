"""
PPI Live Portfolio Dashboard
Tablero de monitoreo en vivo de la cartera en Portfolio Personal Inversiones.
"""

import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

from ppi_wrapper import create_client_from_env, PPIWrapper

# -----------------------------------------------------------------------------
# Configuración de página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PPI Portfolio Live",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cargar .env si existe (solo local)
load_dotenv()

# -----------------------------------------------------------------------------
# Sidebar - Configuración
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuración")
    st.markdown("---")

    # Refresh interval
    refresh_seconds = st.slider(
        "Auto-refresh (segundos)",
        min_value=30,
        max_value=300,
        value=60,
        step=30,
        help="Cada cuánto se actualizan los datos automáticamente",
    )

    st.markdown("---")
    st.caption("Versión inicial · Solo lectura")
    st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")

# Auto-refresh
st_autorefresh(interval=refresh_seconds * 1000, key="data_refresh")


# -----------------------------------------------------------------------------
# Helpers de formato
# -----------------------------------------------------------------------------
def format_currency(value, symbol=""):
    try:
        return f"{symbol} {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(value)


def safe_df(data, columns=None):
    if not data:
        return pd.DataFrame(columns=columns or [])
    return pd.DataFrame(data)


# -----------------------------------------------------------------------------
# Carga de datos (con cache corto)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner="Conectando con PPI...")
def load_portfolio_data():
    client = create_client_from_env()
    client.login()

    balances = client.get_available_balance()
    positions_raw = client.get_balance_and_positions()
    movements = client.get_movements(days=15)
    active_orders = client.get_active_orders()

    return {
        "account_number": client.account_number,
        "balances": balances,
        "positions_raw": positions_raw,
        "movements": movements,
        "active_orders": active_orders,
        "timestamp": datetime.now(),
    }


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
st.title("📈 PPI Portfolio Live")
st.caption("Monitoreo en vivo de tu cartera · Portfolio Personal Inversiones")

# Intentar cargar datos
try:
    data = load_portfolio_data()
except Exception as e:
    st.error("Error al conectar con la API de PPI")
    st.code(str(e))
    st.info(
        "Verificá que las keys estén correctamente configuradas:\n"
        "- **Local**: archivo `.env` con PPI_PUBLIC_KEY y PPI_PRIVATE_KEY\n"
        "- **Streamlit Cloud**: Secrets (Settings → Secrets)"
    )
    st.stop()

account = data["account_number"]
st.success(f"Conectado · Cuenta: **{account}** · {data['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}")

# -----------------------------------------------------------------------------
# Sección 1: Saldos disponibles
# -----------------------------------------------------------------------------
st.header("💰 Saldos disponibles")

balances = data["balances"]
if balances:
    cols = st.columns(min(4, len(balances)))
    for i, bal in enumerate(balances):
        with cols[i % len(cols)]:
            name = bal.get("name", "—")
            amount = bal.get("amount", 0)
            settlement = bal.get("settlement", "")
            symbol = bal.get("symbol", "")
            st.metric(
                label=f"{name} ({settlement})",
                value=format_currency(amount, symbol),
            )
else:
    st.info("No se encontraron saldos disponibles.")

st.markdown("---")

# -----------------------------------------------------------------------------
# Sección 2: Posiciones
# -----------------------------------------------------------------------------
st.header("📦 Posiciones")

positions_raw = data["positions_raw"]
all_instruments = []

if positions_raw and "groupedInstruments" in positions_raw:
    for group in positions_raw["groupedInstruments"]:
        group_name = group.get("name", "Otros")
        for inst in group.get("instruments", []):
            all_instruments.append(
                {
                    "Grupo": group_name,
                    "Ticker": inst.get("ticker", ""),
                    "Cantidad": inst.get("quantity", 0),
                    "Precio": inst.get("price", 0),
                    "Monto": inst.get("amount", 0),
                    "Colateral": inst.get("collateralQuantity", 0),
                }
            )

if all_instruments:
    df_pos = pd.DataFrame(all_instruments)

    # Total valuación
    total_value = df_pos["Monto"].sum()
    st.metric("Valuación total de posiciones", format_currency(total_value))

    # Tabla
    st.dataframe(
        df_pos.style.format(
            {
                "Cantidad": "{:,.2f}",
                "Precio": "{:,.2f}",
                "Monto": "{:,.2f}",
                "Colateral": "{:,.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    # Gráfico simple de composición (si hay datos)
    if len(df_pos) > 0 and df_pos["Monto"].sum() > 0:
        fig = px.pie(
            df_pos,
            values="Monto",
            names="Ticker",
            title="Composición de la cartera (por monto)",
            hole=0.4,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay posiciones abiertas en este momento.")

st.markdown("---")

# -----------------------------------------------------------------------------
# Sección 3: Órdenes activas
# -----------------------------------------------------------------------------
st.header("📋 Órdenes activas")

active = data["active_orders"]
if active:
    df_orders = pd.DataFrame(active)
    # Seleccionamos columnas más útiles si existen
    preferred_cols = [
        "id",
        "ticker",
        "operation",
        "status",
        "quantity",
        "price",
        "amount",
        "settlement",
        "date",
    ]
    cols_to_show = [c for c in preferred_cols if c in df_orders.columns]
    st.dataframe(df_orders[cols_to_show], use_container_width=True, hide_index=True)
else:
    st.info("No hay órdenes activas.")

st.markdown("---")

# -----------------------------------------------------------------------------
# Sección 4: Últimos movimientos
# -----------------------------------------------------------------------------
st.header("🔄 Últimos movimientos (15 días)")

movs = data["movements"]
if movs:
    df_mov = pd.DataFrame(movs)
    preferred_mov_cols = [
        "settlementDate",
        "description",
        "ticker",
        "currency",
        "amount",
        "quantity",
        "price",
        "balance",
    ]
    cols_to_show = [c for c in preferred_mov_cols if c in df_mov.columns]
    st.dataframe(
        df_mov[cols_to_show].head(50),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No se encontraron movimientos en los últimos 15 días.")

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "Dashboard de solo lectura · Datos obtenidos vía API oficial de PPI · "
    "No realiza operaciones de compra/venta."
)

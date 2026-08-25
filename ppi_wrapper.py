"""
Wrapper limpio sobre ppi-client para el dashboard.
Maneja login, errores, formatea datos y calcula dólar MEP.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import os

from ppi_client.ppi import PPI
from ppi_client.models.account_movements import AccountMovements


class PPIWrapper:
    def __init__(self, public_key: str, private_key: str, sandbox: bool = False):
        self.public_key = public_key
        self.private_key = private_key
        self.sandbox = sandbox
        self.ppi = PPI(sandbox=sandbox)
        self._logged_in = False
        self.account_number: Optional[str] = None

    def login(self) -> bool:
        try:
            self.ppi.account.login_api(self.public_key, self.private_key)
            accounts = self.ppi.account.get_accounts()
            if not accounts:
                raise ValueError("No se encontraron cuentas asociadas a las keys")
            self.account_number = accounts[0]["accountNumber"]
            self._logged_in = True
            return True
        except Exception as e:
            self._logged_in = False
            raise RuntimeError(f"Error de login: {e}") from e

    def ensure_login(self):
        if not self._logged_in:
            self.login()

    def get_accounts(self) -> List[Dict]:
        self.ensure_login()
        return self.ppi.account.get_accounts()

    def get_available_balance(self) -> List[Dict]:
        self.ensure_login()
        return self.ppi.account.get_available_balance(self.account_number)

    def get_balance_and_positions(self) -> Dict:
        self.ensure_login()
        return self.ppi.account.get_balance_and_positions(self.account_number)

    def get_movements(self, days: int = 30) -> List[Dict]:
        self.ensure_login()
        date_to = datetime.now()
        date_from = date_to - timedelta(days=days)
        movements = self.ppi.account.get_movements(
            AccountMovements(self.account_number, date_from, date_to, None)
        )
        return movements or []

    def get_active_orders(self) -> List[Dict]:
        self.ensure_login()
        return self.ppi.orders.get_active_orders(self.account_number) or []

    def get_orders(self, days: int = 30) -> List[Dict]:
        self.ensure_login()
        date_to = datetime.now()
        date_from = date_to - timedelta(days=days)
        return self.ppi.orders.get_orders(
            self.account_number, date_from=date_from, date_to=date_to
        ) or []

    def get_mep_rate(self) -> Optional[float]:
        """
        Calcula el dólar MEP implícito usando AL30 / AL30D.
        Método estándar y más confiable del mercado argentino.
        """
        self.ensure_login()
        try:
            for settlement in ["A-48HS", "INMEDIATA", "A-24HS"]:
                try:
                    al30 = self.ppi.marketdata.current("AL30", "BONOS", settlement)
                    al30d = self.ppi.marketdata.current("AL30D", "BONOS", settlement)

                    price_ars = None
                    price_usd = None

                    if isinstance(al30, dict):
                        price_ars = al30.get("price") or al30.get("Price")
                    if isinstance(al30d, dict):
                        price_usd = al30d.get("price") or al30d.get("Price")

                    if price_ars and price_usd and float(price_usd) > 0:
                        rate = float(price_ars) / float(price_usd)
                        if 500 < rate < 3000:
                            return round(rate, 2)
                except Exception:
                    continue
            return None
        except Exception:
            return None


def create_client_from_env() -> PPIWrapper:
    """Crea el cliente desde variables de entorno o Streamlit secrets."""
    public = os.getenv("PPI_PUBLIC_KEY")
    private = os.getenv("PPI_PRIVATE_KEY")
    sandbox_str = os.getenv("PPI_SANDBOX", "false").lower()
    sandbox = sandbox_str in ("true", "1", "yes")

    if not public or not private:
        raise ValueError(
            "Faltan PPI_PUBLIC_KEY o PPI_PRIVATE_KEY. "
            "Configuralas en .env (local) o en Streamlit Secrets (deploy)."
        )

    return PPIWrapper(public, private, sandbox=sandbox)

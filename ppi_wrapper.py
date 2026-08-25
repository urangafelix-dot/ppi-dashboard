"""
Wrapper limpio sobre ppi-client para el dashboard.
Maneja login, errores y formatea los datos de forma consistente.
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

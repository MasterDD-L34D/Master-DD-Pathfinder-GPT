import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODULES_DIR = BASE_DIR / "modules"
DATA_DIR = BASE_DIR / "data"


class Settings:
    """Configurazione base caricata da variabili d'ambiente."""

    def __init__(self) -> None:
        self.api_key: str | None = os.getenv("API_KEY")
        self.allow_anonymous: bool = os.getenv("ALLOW_ANONYMOUS", "false").lower() in (
            "1",
            "true",
            "yes",
            "y",
        )
        self.allow_module_dump: bool = os.getenv(
            "ALLOW_MODULE_DUMP", "true"
        ).lower() in (
            "1",
            "true",
            "yes",
            "y",
        )  # se False, il testo dei moduli viene troncato
        self.auth_backoff_threshold: int = int(
            os.getenv("AUTH_BACKOFF_THRESHOLD", "5")
        )  # tentativi invalidi prima del backoff
        self.auth_backoff_seconds: int = int(
            os.getenv("AUTH_BACKOFF_SECONDS", "60")
        )  # finestra di backoff in secondi
        self.metrics_api_key: str | None = os.getenv("METRICS_API_KEY")
        self.metrics_ip_allowlist: list[str] = [
            ip.strip()
            for ip in os.getenv("METRICS_IP_ALLOWLIST", "").split(",")
            if ip.strip()
        ]


settings = Settings()

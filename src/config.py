import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODULES_DIR = BASE_DIR / "modules"
DATA_DIR = BASE_DIR / "data"

class Settings:
    """Configurazione base caricata da variabili d'ambiente."""

    def __init__(self) -> None:
        self.api_key: str | None = os.getenv("API_KEY")
        self.allow_module_dump: bool = os.getenv("ALLOW_MODULE_DUMP", "true").lower() in (
            "1",
            "true",
            "yes",
            "y",
        )  # se False, il testo dei moduli viene troncato


settings = Settings()

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODULES_DIR = BASE_DIR / "modules"
DATA_DIR = BASE_DIR / "data"

# In produzione puoi leggere queste cose da variabili d'ambiente
class Settings:
    api_key: str | None = None  # opzionale, se vuoi aggiungere auth
    allow_module_dump: bool = True  # se False, puoi limitare lunghezza contenuti

settings = Settings()

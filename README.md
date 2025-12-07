# Pathfinder 1E Master DD — Core Repo (API + Prompt Kit)

Questo repository contiene il "cuore" del tuo GPT **Pathfinder 1E Master DD** in forma esterna:
- tutti i moduli originali (`base_profile.txt`, `Taverna_NPC.txt`, `minmax_builder.txt`, ecc.)
- una piccola API in Python (FastAPI) che espone i moduli al GPT tramite Actions
- i file di supporto (knowledge pack, template scheda, guide PDF)
- un prompt compatto da incollare nel builder dei GPT, che usa questa API invece di includere tutto il base_profile

## Struttura

```text
pathfinder_master_dd_repo/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ src/
│  ├─ app.py                # FastAPI con endpoint per i moduli
│  ├─ config.py             # Configurazione path e sicurezza base
│  ├─ modules/              # TUTTI i tuoi moduli originali (txt/md/json)
│  └─ data/                 # PDF di supporto (gear guide, crafter guide, ecc.)
├─ gpt/
│  ├─ system_prompt_core.md # Istruzioni compatte da incollare nel GPT
│  └─ openapi.json          # Spec Actions per collegare l'API
└─ docs/
   ├─ architecture.md       # Spiegazione architettura Kernel + moduli
   └─ module_index.md       # Indice rapido dei file in src/modules
```

### Requisiti

- Python 3.10+
- `pip install -r requirements.txt`

### Avvio API locale

```bash
uvicorn src.app:app --reload --port 8000
```

L'endpoint di base sarà ad esempio: `http://localhost:8000`

### Endpoints principali

- `GET /health` — ping rapido
- `GET /modules` — lista dei file modulo disponibili
- `GET /modules/{name}` — contenuto testuale di un modulo (es. `base_profile.txt`)
- `GET /modules/{name}/meta` — info sintetiche sul modulo (dimensione, tipo)
- `GET /knowledge` — lista risorse PDF/MD disponibili
- `GET /knowledge/{name}` — metadata su una risorsa

> Nel builder GPT userai il file `gpt/openapi.json` come **Actions Spec** e il testo
> di `gpt/system_prompt_core.md` come **istruzioni**. Così il GPT non deve più contenere
> l'intero `base_profile.txt`, ma può chiedere all'API i moduli quando servono.

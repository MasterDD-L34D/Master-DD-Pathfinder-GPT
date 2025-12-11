# API Usage — Pathfinder 1E Master DD

Questa guida riassume come usare l'API FastAPI esposta dal progetto, con esempi di richieste e note sui limiti.

## Autenticazione e flag runtime

- **Header obbligatorio**: `x-api-key: <API_KEY>` a meno che non sia impostato `ALLOW_ANONYMOUS=true`.
- **Troncamento contenuti** (`ALLOW_MODULE_DUMP`):
  - `false` (default): i file non testuali generano `403 Module download not allowed`; i `.txt`/`.md` sono limitati ai primi 4000 caratteri con suffisso `[contenuto troncato]`, header `X-Content-Partial: true`, `X-Content-Partial-Reason: ALLOW_MODULE_DUMP=false`, `X-Content-Served-Bytes`/`X-Content-Remaining-Bytes` e status `206 Partial Content`.
  - `true`: i file vengono restituiti per intero, inclusi PDF/asset non testuali (abilitare solo per QA/export controllati).
- **Metriche Prometheus** (`METRICS_API_KEY` o `METRICS_IP_ALLOWLIST`):
  - `/metrics` è protetto da API key dedicata (`METRICS_API_KEY`) o dalla stessa `API_KEY`.
  - In alternativa è possibile autorizzare un allowlist IP con `METRICS_IP_ALLOWLIST="1.2.3.4,10.0.0.0"` (liste separate da virgole).
  - Se nessuna chiave è configurata, solo gli IP nella allowlist possono leggere le metriche.
  - Le metriche includono conteggio richieste per endpoint/metodo/status, errori 4xx/5xx, trigger di backoff, stato delle directory.

## Endpoint principali

### `GET /health`
Verifica lo stato dell'API e delle directory configurate. Risposta di esempio:

```json
{
  "status": "ok",
  "directories": {
    "modules": { "status": "ok", "path": "src/modules", "message": null },
    "data": { "status": "ok", "path": "src/data", "message": null }
  }
}
```

In caso di problemi, lo stesso payload include `status: "error"`, campi `message` valorizzati e un array `errors`; l'endpoint risponde con `503 Service Unavailable`.

### `GET /modules`
Elenca i moduli disponibili in `src/modules`.

**Esempio**
```http
GET /modules
x-api-key: ${API_KEY}
```

**Risposta**
```json
[
  { "name": "base_profile.txt", "size_bytes": 12345, "suffix": ".txt" },
  { "name": "minmax_builder.txt", "size_bytes": 6789, "suffix": ".txt" }
]
```

### `GET /modules/{name}/meta`
Restituisce metadati (nome, dimensioni, estensione) senza il contenuto del file.
Se il modulo dichiara un header strutturato (es. `version`, `compatibility`) questi
campi vengono esposti insieme a eventuali note di compatibilità in formato stringa
o dizionario. Per i moduli JSON (es. `tavern_hub.json`) `version`/`compatibility`
vengono letti dal blocco `meta` o dal root dell'oggetto JSON, senza necessità di
front matter.

Esempio di risposta:

```json
{
  "name": "ruling_expert.txt",
  "size_bytes": 12345,
  "suffix": ".txt",
  "version": "3.1-hybrid",
  "compatibility": {
    "core_min": "2.6.7",
    "integrates_with": [
      "MinMax Builder",
      "Documentazione",
      "Taverna NPC",
      "Explain",
      "Archivist"
    ]
  }
}
```

### `GET /modules/taverna_saves/meta`
Restituisce quota e metadati della cartella di servizio `taverna_saves`, inclusi path, `max_files`, slot residui, spazio disco libero e policy di naming/overflow. Quando `ALLOW_MODULE_DUMP=false` il payload espone anche `module_dump_allowed: false` e `partial_dump_notice` per ricordare che i dump testuali sono parziali. Il payload include un campo `remediation` con istruzioni per sbloccare Echo gate sotto soglia (<8.5) ripetendo /grade o usando /refine_npc (in sandbox puoi disattivare temporaneamente Echo con /echo off) e per chiudere i QA CHECK bloccanti eseguendo /self_check, completando Canvas+Ledger e verificando Echo ≥ soglia prima di rilanciare /save_npc o /npc_export.

### `GET /modules/taverna_saves/quota`
Espone solo i numeri di quota/occupazione (`current_files`, `remaining_files`, spazio disco, dimensione totale dei JSON salvati).

### `GET|POST /modules/{name}`
Restituisce il contenuto del modulo o, per `minmax_builder.txt`, uno **stub** di risposta del builder.

Parametri principali:
- `mode` (query/body): `core` o `extended` per il builder; `stub` per forzare la risposta di esempio.
- `stub` (query): boolean per ottenere lo stub del builder.
- `class`, `race`, `archetype` (query): usati nello stub per popolare la build fittizia.
- `body` (POST): opzionale, accetta campi `mode`, `builder_mode`, `race`, `archetype`, `hooks`, ecc.

**Esempio — modulo testuale**
```http
GET /modules/base_profile.txt?mode=extended
x-api-key: ${API_KEY}
```
Risposta: contenuto `.txt` (troncato se `ALLOW_MODULE_DUMP=false`).

**Esempio — stub builder**
```http
POST /modules/minmax_builder.txt?stub=true&class=Fighter&race=Elf&archetype="Lore Warden"
x-api-key: ${API_KEY}
Content-Type: application/json

{ "mode": "extended", "hooks": ["serve l'Ordine"], "sheet_locale": "it-IT" }
```

Risposta JSON semplificata:
```json
{
  "class": "Fighter",
  "mode": "extended",
  "build_state": { "class": "Fighter", "mode": "extended", "race": "Elf", "archetype": "Lore Warden", "step": 1, "step_total": 16, "step_labels": { "1": "Profilo Base", "2": "Razza & Classe", "8": "QA & Export", "16": "Chiusura" } },
  "benchmark": { "meta_tier": "T3", "ruling_badge": "validated", "dpr_snapshot": { "livello_1": { "media": 6, "picco": 9 } } },
  "export": { "sheet_payload": { "classi": [{ "nome": "Fighter", "livelli": 1, "archetipi": ["Lore Warden"] }], "statistiche": { "FOR": 16, "DES": 14 }, "hooks": ["serve l'Ordine"] } },
  "narrative": "Elf Lore Warden pronta/o per il campo, specializzata/o in tattiche da Fighter.",
  "ledger": { "movimenti": [{ "voce": "Equipaggiamento iniziale", "importo": -150 }] },
  "composite": { "build": { "build_state": { "class": "Fighter", "mode": "extended", "race": "Elf", "archetype": "Lore Warden", "step": 1, "step_total": 16, "step_labels": { "1": "Profilo Base" } }, "benchmark": { "meta_tier": "T3" }, "export": { "sheet_payload": { "statistiche": { "FOR": 16, "DES": 14 } } } }, "narrative": "...", "sheet": { "statistiche": { "FOR": 16, "DES": 14 } }, "ledger": { "movimenti": [] } }
}
```

### `GET /knowledge`
Elenca i file in `src/data` (PDF, markdown di supporto). Non restituisce il contenuto dei manuali Paizo protetti.

### `GET /knowledge/{name}/meta`
Metadati per un singolo asset in `src/data`.

## Errori standard
- `401 Unauthorized`: chiave mancante/non valida quando `ALLOW_ANONYMOUS` è disabilitato o `API_KEY` non è configurata.
- `403 Module download not allowed`: download di asset non testuali bloccato quando `ALLOW_MODULE_DUMP=false`.
- `404 Module not found` / `Knowledge file not found`: path valido ma file assente.
- `400 Invalid module/knowledge path`: path con traversal o formato non supportato.
- `503 Service Unavailable`: directory `modules` o `data` non raggiungibili; anche `/health` riporta `503` in questo caso.
- `500 Stub payload non valido`: solo per `/modules/minmax_builder.txt` se la generazione dello stub fallisce.

## Metriche

L'accesso a `/metrics` è protetto da `require_metrics_access`, che accetta le seguenti credenziali:

- Header `x-api-key` valorizzato con `METRICS_API_KEY`.
- In alternativa, lo stesso header può usare la chiave primaria `API_KEY`.
- Allowlist IP configurabile con `METRICS_IP_ALLOWLIST="1.2.3.4,10.0.0.0"` (valori separati da virgole, senza spazi).

Se la richiesta non include una chiave valida **né** proviene da un IP in allowlist, `/metrics` risponde con `403 Forbidden`.

**Esempi `curl`**

- Accesso con chiave dedicata:
  ```bash
  curl -H "x-api-key: ${METRICS_API_KEY}" https://example.org/metrics
  ```
- Accesso con chiave primaria:
  ```bash
  curl -H "x-api-key: ${API_KEY}" https://example.org/metrics
  ```
- Accesso basato su allowlist IP (nessuna chiave, IP autorizzato):
  ```bash
  curl https://example.org/metrics
  ```

**Output**: testo Prometheus con contatori per richieste totali per endpoint/metodo/status, errori 4xx/5xx, attivazioni del backoff di autenticazione e gauge sullo stato delle directory di configurazione.

> **Nota di sicurezza**: in ambienti pubblici usare sempre `METRICS_API_KEY` (o `API_KEY`) e limitare l'allowlist al minimo necessario; evitare allowlist larghe per prevenire scraping non autorizzato.

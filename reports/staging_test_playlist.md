# Playlist QA Staging — Dump policy, CTA QA, naming export

Questa playlist copre i casi richiesti per l'ambiente di **staging/sandbox** usando solo le API documentate (`/modules`, `/health`, `/metrics`) e le note operative dei moduli principali.

## Prerequisiti
- Imposta `API_KEY` e, se necessario, `METRICS_API_KEY`; per i test sui dump modifica `ALLOW_MODULE_DUMP` tra `false` e `true`.
- Base URL: `https://staging.example.com` (sostituibile con sandbox locale `http://localhost:8000`).
- Variabili comuni:
  ```bash
  export API_URL="https://staging.example.com"
  export API_KEY="<chiave>"
  ```

## 1) Troncamento e header coerenti (`ALLOW_MODULE_DUMP=false/true`)
- **Smoke 401/headers** (dump OFF):
  ```bash
  curl -i "$API_URL/modules/minmax_builder.txt"                 # atteso 401
  curl -i -H "x-api-key:$API_KEY" "$API_URL/modules/minmax_builder.txt" | head -n 20
  ```
  - Verifica `206` con header `X-Content-*`, marker `[contenuto troncato — ...]` e `X-Content-Partial-Reason: ALLOW_MODULE_DUMP=false`.【F:src/app.py†L1517-L1580】
- **Binari bloccati** (dump OFF): `curl -i -H "x-api-key:$API_KEY" "$API_URL/modules/minmax_builder.pdf"` → `403`.
- **Full dump** (dump ON):
  ```bash
  ALLOW_MODULE_DUMP=true uvicorn src.app:app --port 8000 &
  curl -i -H "x-api-key:$API_KEY" "$API_URL/modules/base_profile.txt" | head -n 5   # 200 con file completo
  ```
- **Metrics gate**: `curl -i "$API_URL/metrics"` → `403`; ripetere con `-H "x-api-key:$METRICS_API_KEY"` per 200 e contenuto `text/plain; version=0.0.4`.

## 2) Gating QA con CTA obbligatorie
- **Encounter Designer**: GET `/modules/Encounter_Designer.txt` con API key, verificando nel testo la CTA `/validate_encounter` e il blocco export allo step 6 (flow QA→export).【F:src/modules/Encounter_Designer.txt†L387-L438】【F:src/modules/Encounter_Designer.txt†L505-L514】
- **MinMax Builder**: GET `/modules/minmax_builder.txt`, controllando il gate `export_requires` e la CTA `/qa_check` prima degli export (`/export_build`, `/export_vtt`).【F:src/modules/minmax_builder.txt†L1886-L1893】【F:src/modules/minmax_builder.txt†L2018-L2024】
- **Narrative/Taverna hub**: GET `/modules/Taverna_NPC.txt` e `/modules/narrative_flow.txt` per confermare CTA di remediation/QA prima di export/report (quiz, `qa_story`, ledger).【F:src/modules/Taverna_NPC.txt†L1299-L1334】【F:src/modules/narrative_flow.txt†L334-L401】

## 3) Coerenza del naming export
- **MinMax Builder**: nel modulo verifica la nomenclatura condivisa `MinMax_<nome>.pdf/.xlsx/.json` su `/export_build` e `/export_vtt`.【F:src/modules/minmax_builder.txt†L940-L943】【F:src/modules/minmax_builder.txt†L1224-L1225】
- **Encounter Designer**: conferma che il flow export riporta `export_filename` e naming condivisa con MinMax (VTT/MD/PDF).【F:src/modules/Encounter_Designer.txt†L419-L438】
- **Ledger/Taverna**: controlla auto-naming `taverna_saves` e export guidati dal canvas/ledger, senza dump raw diretto.【F:src/modules/Taverna_NPC.txt†L1299-L1334】【F:src/modules/adventurer_ledger.txt†L1101-L1127】

## Output atteso e raccolta evidenze
- Salvare header/raw delle chiamate in `reports/module_tests/<modulo>_staging.log` (uno per modulo toccato) e allegare estratti nei report di QA.
- Annotare gli esiti nel tracker sprint (stato storia chiusa/riaperta) e postare nel canale di rilascio il riepilogo dei test eseguiti con riferimenti ai log.

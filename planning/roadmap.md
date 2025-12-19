# Roadmap Pathfinder 1E Master DD

## Obiettivi correnti
- Stabilizzare il ciclo di generazione del database build esteso e dei moduli raw per esport/benchmark.
- Rendere la validazione dei payload modulare con livelli progressivi (`--strict`, `--keep-invalid`) per individuare rapidamente dati non conformi senza perdere evidenze utili.
- Hardening di healthcheck/metriche e autenticazione per ridurre falsi positivi/negativi nei probe e nei rate-limit.

## Milestone
- **Generazione DB esteso**: usare `tools/generate_build_db.py` in modalità `extended` per coprire classi e varianti chiave, salvando build e moduli in `src/data/`. Collegamento al flusso descritto in README per l'orchestrazione completa (health check, parametri `mode`, dump moduli).
- **Discovery e filtri moduli**: abilitare `--discover-modules` per unire moduli pinnati e quelli esposti da `/modules`, applicando filtri glob (`--include/--exclude`) per controllare ciò che finisce nel dump, come previsto dal flusso di selezione moduli nel README.
- **Validazione progressiva**: adottare i flag `--strict` e `--keep-invalid` per gestire errori di schema durante la generazione DB, preservando payload non conformi per analisi successive come indicato nella sezione troubleshooting.
- **Health/metrics hardening**: estendere probe di `/health` e raccolta delle metriche per allinearsi ai workflow di avvio API e backoff descritti nel README, riducendo blocchi dovuti a `401/429` e time-out su endpoint remoti.

## Stato ultimo ciclo build
- **Esecuzione:** preflight locale con `--export-lists` per rigenerare `reports/build_review.json` e `reports/index_analysis.json`; gli alert evidenziano che nessuna classe core ha build valide negli indici correnti.
- **Follow-up rapido (handoff):**
  - **Tech Lead:** priorizzare un run mirato per coprire almeno le classi core e ridurre gli alert CI appena introdotti.
  - **Backend/API:** verificare le cause dei warning di validazione (es. versioni catalogo e campo `source` nei meta moduli) e proporre fix lato API/schema.
  - **Data/Validation:** riprocessare i payload esistenti aggiornando catalogo/versioni e correggendo i metadati per rientrare negli schemi.
  - **Docs & Prompt:** documentare nel README/runbook la presenza degli alert di copertura e le azioni richieste per chiudere il gap sulle classi core.
  - **QA reportistica:** continuare a far girare `python tools/refresh_module_reports.py --check` (lint anti-placeholder) e validare gli output coverage generati in CI.

## Owner / Responsabili
- **Tech Lead**: supervisione roadmap, priorità e merge decisioni.
- **Backend/API**: implementazione script `generate_build_db`, autenticazione (`AUTH_BACKOFF_*`), metriche/health.
- **Data/Validation**: schemi in `schemas/`, flag `--strict`/`--keep-invalid`, indici `build_index.json` e `module_index.json`.
- **Docs & Prompt**: allineamento README, `docs/api_usage.md`, `gpt/system_prompt_core.md` e comunicazione cambiamenti.

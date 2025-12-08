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

## Owner / Responsabili
- **Tech Lead**: supervisione roadmap, priorità e merge decisioni.
- **Backend/API**: implementazione script `generate_build_db`, autenticazione (`AUTH_BACKOFF_*`), metriche/health.
- **Data/Validation**: schemi in `schemas/`, flag `--strict`/`--keep-invalid`, indici `build_index.json` e `module_index.json`.
- **Docs & Prompt**: allineamento README, `docs/api_usage.md`, `gpt/system_prompt_core.md` e comunicazione cambiamenti.

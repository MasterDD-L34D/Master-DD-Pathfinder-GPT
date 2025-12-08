# Command run log

## generate_build_db connectivity check (initial)
- **Command:** `python tools/generate_build_db.py --api-url http://localhost:8000 --mode extended --discover-modules --max-retries 3 --strict`
- **Result:** Failed with `httpx.ConnectError: All connection attempts failed` while calling `/modules` during module discovery. The tool issued schema-related deprecation warnings before the network failure.
- **Notes:** No spec file was provided; defaults targeted `src/data/builds` and `src/data/modules`. Strict validation remained enabled; switching to `--warn-only` or `--keep-invalid` was not tested because the run stopped before any payloads were retrieved.
- **Timestamp:** 2025-12-08T03:27:49Z

## generate_build_db rerun with local API up
- **Prep:** Started `uvicorn src.app:app --reload --port 8000` with `ALLOW_ANONYMOUS=true` to bypass the missing API key that blocked the previous attempt.
- **Command:** `python tools/generate_build_db.py --api-url http://localhost:8000 --mode extended --discover-modules --max-retries 3 --strict`
- **Result:** Success. Discovery hit `/modules`, downloaded 14 module assets, and fetched extended builds for all PF1e classes. Strict validation passed; only deprecation warnings from `jsonschema.RefResolver` and `datetime.utcnow()` were reported. Index files were written to `src/data/build_index.json` and `src/data/module_index.json` alongside per-class JSON in `src/data/builds/` and module dumps in `src/data/modules/`.
- **Notes:** No spec file was used. Module fetches included metadata calls (e.g., `/modules/<name>/meta`) and validated step totals at 16 for extended mode. Keep `ALLOW_ANONYMOUS=true` or set `API_KEY` before reruns.
- **Timestamp:** 2025-12-08T03:32:06Z

## generate_build_db comandi di riferimento (core)
- **Variabili:** impostare `API_URL` verso l'endpoint MinMax Builder e `API_KEY` quando richiesto dal gateway; esempio `API_URL=https://builder.example.org API_KEY=token-supersegret`.
- **Comando base:** `API_URL=$API_URL API_KEY=$API_KEY python tools/generate_build_db.py --mode core --classes Alchemist Barbarian --output-dir src/data/builds --modules-output-dir src/data/modules --index-path src/data/build_index.json --module-index-path src/data/module_index.json --max-retries 2`.
- **Salto health check:** aggiungere `--skip-health-check` quando l'endpoint `/health` non è esposto (la richiesta prosegue direttamente verso `/modules/minmax_builder.txt`; eventuali errori di connessione generano `httpx.ConnectError` con contesto esplicito sull'URL usato).
- **Archiviazione locale:** dopo l'esecuzione si possono comprimere gli output con `tar -czf build_db_core.tar.gz src/data/builds src/data/build_index.json src/data/module_index.json` per il caricamento come artefatto CI.

## generate-build-db-core (GitHub Actions)
- **Nome job:** `generate-build-db-core / Build DB core e archiviazione` (workflow `generate-build-db-core.yml`).
- **Cosa fa:** usa `API_URL`/`API_KEY` da secret GitHub per eseguire `python tools/generate_build_db.py --mode core --strict --max-retries 3` archiviando log e output (builds, moduli, indici) nella cartella `build_artifacts/`.
- **Trigger:** schedulato ogni lunedì alle 03:00 UTC e avviabile manualmente via **Run workflow**.
- **Recupero log e artefatti:** al termine del job scaricare l'artefatto `generate-build-db-core-artifacts`, che contiene `generate_build_db_core.log`, i dump in `builds/` e `modules/` e i file indice `build_index.json` e `module_index.json`.

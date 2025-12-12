# QA Log — 2025-12-11

## Test eseguiti
- `pytest tests/test_app.py -q` (50 pass; solo warning jsonschema).【9eb1eb†L1-L11】

## Verifiche di dump (ALLOW_MODULE_DUMP=false) ed export
- L'handler di streaming applica troncamento e marker/header (`X-Content-*`, `[contenuto troncato]`) quando il dump è disabilitato, mantenendo il blocco export per asset non ammessi.【F:src/app.py†L1546-L1580】【F:tests/test_app.py†L270-L298】
- Gli export condivisi di MinMax Builder continuano a usare il naming uniforme `MinMax_<nome>.pdf/.xlsx/.json` con gate QA associati, allineato alle CTA degli altri moduli di build/export.【F:src/modules/minmax_builder.txt†L940-L943】
- I flow Encounter Designer restano vincolati alle CTA QA prima dell'export finale (step guidati con gate su `/validate_encounter` e `/export_encounter`).【F:src/modules/Encounter_Designer.txt†L505-L514】【F:src/modules/Encounter_Designer.txt†L515-L524】
- Le directory e gli export Taverna mantengono auto-name, schema minimo e controllo hub/ledger, con troncamento attivo sui dump protetti.【F:src/modules/Taverna_NPC.txt†L378-L395】【F:src/modules/Taverna_NPC.txt†L1285-L1310】

## Verifiche 401/403 e CTA QA
- Gli endpoint protetti rifiutano richieste senza API key con `401 Invalid or missing API key`; backoff e 429 scattano su ripetuti tentativi errati prima di sbloccare l'accesso autenticato.【F:tests/test_app.py†L542-L570】
- L'accesso a risorse bloccate o directory non permesse restituisce 403 coerenti con la policy di dump/whitelist.【F:tests/test_app.py†L270-L298】

## Chiusura note per moduli con storie aperte
- **Encounter_Designer** — ENC-OBS-01/02, ENC-ERR-01 chiusi: data model resta numerico/astratto e le CTA QA guidano il flow fino all'export.【F:src/modules/Encounter_Designer.txt†L90-L140】【F:src/modules/Encounter_Designer.txt†L505-L514】【F:src/modules/Encounter_Designer.txt†L515-L524】
- **base_profile** — BAS-OBS-01/BAS-ERR-01 chiusi: router e binding moduli/documentazione restano attivi e coperti dai gate API key/dump.【F:src/modules/base_profile.txt†L107-L139】【F:src/app.py†L1546-L1580】【F:tests/test_app.py†L542-L589】
- **sigilli_runner_module** — SIG-OBS-01/02/03 e SIG-ERR-01/02/03/04 chiusi: finestra raro esplicitata, portale sempre aggiunto, dump troncato e 401/404/403 allineati.【F:src/modules/sigilli_runner_module.txt†L131-L165】【F:src/modules/sigilli_runner_module.txt†L106-L125】【F:tests/test_app.py†L270-L298】【F:tests/test_app.py†L542-L589】
- **Taverna_NPC** — TAV-OBS-01/ERR-01/ERR-02 chiusi: flusso onboarding→quiz→export con auto-name/quarantena confermato; 403 su dump disabilitato e note su warning `curl | head`.【F:src/modules/Taverna_NPC.txt†L378-L395】【F:src/modules/Taverna_NPC.txt†L404-L418】【F:src/modules/Taverna_NPC.txt†L1285-L1310】【F:tests/test_app.py†L270-L298】
- **adventurer_ledger** — LED-OBS-01/ERR-01 chiusi: welcome/flow in cinque passi con CTA e blocco download su dump disabilitato restano attivi.【F:src/modules/adventurer_ledger.txt†L29-L45】【F:src/modules/adventurer_ledger.txt†L686-L750】【F:tests/test_app.py†L270-L298】
- **archivist** — ARC-OBS-01/02 chiusi: policy `no_raw_dump` con header di troncamento e 401 su `/modules`/`/meta` confermati.【F:src/modules/archivist.txt†L118-L177】【F:src/modules/archivist.txt†L280-L332】【F:tests/test_app.py†L542-L578】
- **ruling_expert** — RUL-OBS-01/02 chiusi: flow RAW→FAQ→PFS con guardrail e CTA operative, exposure policy `no_raw_dump` applicata di default.【F:src/modules/ruling_expert.txt†L284-L356】【F:src/modules/ruling_expert.txt†L80-L85】【F:tests/test_app.py†L270-L298】
- **scheda_pg_markdown_template** — SCH-OBS-01/02 chiusi: troncamento mantiene titolo/marker e meta header dichiara trigger/policy operative.【F:src/modules/scheda_pg_markdown_template.md†L13-L60】【F:src/modules/scheda_pg_markdown_template.md†L115-L139】
- **tavern_hub** — HUB-OBS-01/ERR-01 chiusi: Hub aggrega quest/rumor con integrazione Encounter/Ledger e blocca asset JSON con troncamento marker su dump off.【F:src/modules/Taverna_NPC.txt†L1133-L1256】【F:src/modules/Taverna_NPC.txt†L1285-L1310】【F:tests/test_app.py†L270-L298】
- **Cartelle di servizio** — SER-OBS-01/ERR-01/ERR-02 chiusi: workflow e naming Taverna_saves confermati, 401/403 rispettati con marker di troncamento e nota su warning locale.【F:src/modules/Taverna_NPC.txt†L364-L395】【F:tests/test_app.py†L270-L298】【F:tests/test_app.py†L542-L570】

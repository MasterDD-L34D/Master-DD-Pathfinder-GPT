# Report modulo `staging_sandbox_log`

## Ambiente
- Sandbox via `TestClient` FastAPI allineato allo staging con API key richiesta e `ALLOW_MODULE_DUMP=false` di default.【F:reports/staging_sandbox_log.md†L4-L5】

## Esiti API
- `pytest tests/test_app.py -q`: 53/53 test passati con 2 warning di deprecazione jsonschema.【F:reports/staging_sandbox_log.md†L5-L5】

## Metadati
- Ambito: verifica dump toggle, CTA QA e naming export per i moduli principali in sandbox/staging con playlist dedicata.【F:reports/staging_sandbox_log.md†L3-L8】

## Comandi/Flow
- Playlist di staging eseguita per dump, CTA QA e naming; riferimento dettagliato in `reports/staging_test_playlist.md`.【F:reports/staging_sandbox_log.md†L6-L8】

## QA
- Le verifiche combinate di pytest e playlist coprono dump troncati, gating QA ed export naming per i moduli tracciati nella tabella seguente.【F:reports/staging_sandbox_log.md†L10-L23】

| Modulo | Dump policy | CTA / Gate QA | Naming export | Note/log |
| --- | --- | --- | --- | --- |
| Encounter_Designer | Troncamento e header `X-Content-*` applicati con dump off; full dump solo quando consentito.【F:src/app.py†L1517-L1580】 | Export bloccato senza `/validate_encounter` nello step 6.【F:src/modules/Encounter_Designer.txt†L387-L438】【F:src/modules/Encounter_Designer.txt†L505-L514】 | Export VTT/MD/PDF guidati da `export_filename` condiviso.【F:src/modules/Encounter_Designer.txt†L419-L438】 | Header di troncamento e flow QA verificati via playlist; nessun errore nei test automatizzati.【F:reports/staging_test_playlist.md†L1-L46】 |
| minmax_builder | 206 con marker `[contenuto troncato — …]` e blocco binari quando `ALLOW_MODULE_DUMP=false`.【F:src/app.py†L1517-L1580】 | Gate `export_requires`/`qa_check` obbligatori prima di export/benchmark.【F:src/modules/minmax_builder.txt†L1886-L1893】【F:src/modules/minmax_builder.txt†L2018-L2024】 | Nomenclatura condivisa `MinMax_<nome>.pdf/.xlsx/.json` per export VTT/PDF/Excel.【F:src/modules/minmax_builder.txt†L940-L943】【F:src/modules/minmax_builder.txt†L1224-L1225】 | Test automatizzati passati; header/403 coperti da pytest.【F:reports/staging_test_playlist.md†L1-L46】 |
| Taverna_NPC / tavern_hub | Dump parziale con marker/header quando il download è bloccato; export hub protetto.【F:src/modules/Taverna_NPC.txt†L1299-L1334】 | CTA remediation/quiz obbligatorie prima di export/report hub.【F:src/modules/Taverna_NPC.txt†L1299-L1334】 | Auto-naming su canvas/ledger (`taverna_saves`) senza raw dump.【F:src/modules/Taverna_NPC.txt†L1299-L1334】 | Flow CTA/export verificato via playlist; nessuna regressione nei test automatici.【F:reports/staging_test_playlist.md†L1-L46】 |
| narrative_flow | Header `x-truncated`/`x-original-length` e marker di troncamento rispettati con dump off.【F:src/modules/narrative_flow.txt†L334-L401】 | `/qa_story` imposta `ready_for_export` prima di ogni export narrativo.【F:src/modules/narrative_flow.txt†L334-L401】 | Export narrativo vincolato al flag QA (nessun file custom). | Verifica manuale dei flag QA e troncamento secondo playlist; suite pytest passata.【F:reports/staging_test_playlist.md†L1-L46】 |
| adventurer_ledger | Download bloccato quando `allow_module_dump` è false; header/marker applicati.【F:src/app.py†L1517-L1580】 | CTA di validazione delta WBL e export ledger/loot gating.【F:src/modules/adventurer_ledger.txt†L666-L688】【F:src/modules/adventurer_ledger.txt†L780-L783】 | Export ledger/loot/PG con naming guidato e binding scheda.【F:src/modules/adventurer_ledger.txt†L1101-L1127】 | Test automatici coprono blocco dump; nessuna issue aperta.【F:reports/staging_test_playlist.md†L1-L46】 |

## Osservazioni
- Dump troncato e header di sicurezza risultano coerenti fra i moduli verificati, senza regressioni note.【F:reports/staging_sandbox_log.md†L10-L23】

## Errori
- Nessun errore rilevato nella sessione di verifica corrente.【F:reports/staging_sandbox_log.md†L25-L25】

## Miglioramenti
- Approfondire copertura playlist su moduli restanti per consolidare evidenze di dump/QA/export.【F:reports/staging_sandbox_log.md†L3-L23】

## Fix necessari
- Nessun fix richiesto sulla base delle prove riportate.【F:reports/staging_sandbox_log.md†L26-L26】

# Piano di lavoro esecutivo

Generato il 2025-12-10T22:00:06Z da `tools/generate_module_plan.py`
Fonte task: `planning/module_work_plan.md` (priorità P1→P3) e sequenza `planning/module_review_guide.md`.
Obiettivo: coprire tutte le azioni fino al completamento del piano operativo, con fasi sequenziali e dipendenze esplicite.

### Regole di ordinamento
- Prima i cluster critici: builder/bilanciamento (Encounter_Designer, minmax_builder) e hub/persistenza (Taverna_NPC, tavern_hub, Cartelle di servizio).
- All'interno del cluster, ordine di lettura della guida; poi priorità (P1→P3).

## Fase 1 (attuale) · P1 critici e cross-cutting

- Nessun task P1 aperto dopo la rigenerazione: i cluster builder/bilanciamento e hub/persistenza risultano coperti. Procedere con la Fase 2 per chiudere i miglioramenti P2.

## Seconda fase · P1 residui e P2 cooperativi

- **minmax_builder**
  - Nessun task aperto: le CTA di export mostrano il naming condiviso `MinMax_<nome>.pdf/.xlsx/.json` in linea con Encounter_Designer, chiarendo l’output previsto.【F:src/modules/minmax_builder.txt†L940-L943】【F:src/modules/minmax_builder.txt†L1070-L1088】
- **knowledge_pack**
  - ✅ **Allineamento estensioni:** i client/documentazione indirizzano ora i percorsi Knowledge Pack in `.txt`, eliminando i riferimenti legacy `.yaml`.【F:docs/api_usage.md†L20-L27】【F:src/modules/knowledge_pack.md†L3-L4】
  - ✅ **Metadati API:** l’endpoint `/modules/{name}/meta` espone `version` e `compatibility` ricavati dal modulo, senza parsing manuale lato client.【F:src/app.py†L392-L458】
- **meta_doc**
  - ⚠️ Valutare se rieseguire `/modules` con `ALLOW_MODULE_DUMP=false` per documentare eventuali differenze di suffix/size in ambienti futuri.
  - 🔧 Espandere `/render_brew_example` con snippet visivi aggiuntivi (es. box HR/Primary) seguendo il pattern attuale.【F:src/modules/meta_doc.txt†L488-L539】
- **narrative_flow**
  - **Troncamento vs policy**: valutare esposizione di lunghezza originaria o header `x-truncated` quando `ALLOW_MODULE_DUMP=false`, per chiarezza della dimensione residua.【F:src/app.py†L581-L601】【F:tests/test_app.py†L268-L295】
- **ruling_expert**
  - **Documentare payload stub builder**: chiarire nel modulo come i campi `build_state`/`sheet`/`benchmark`/`ledger`/`export`/`composite` si mappano su rulings/QA per agevolare l’integrazione con il builder.【F:src/app.py†L366-L572】
  - **Rafforzare CTA per PFS**: aggiungere un prompt CTA per confermare la stagione PFS nel `status_example`, riducendo ambiguità di giurisdizione.【F:src/modules/ruling_expert.txt†L300-L317】【F:src/modules/ruling_expert.txt†L417-L424】
- **scheda_pg_markdown_template**
  - Documentare nell'header i trigger/policy operative (es. quando abilitare Ledger/MinMax) per chiarezza d'uso nelle pipeline automatiche.【F:src/modules/scheda_pg_markdown_template.md†L115-L139】
- **Cartelle di servizio**
  - 🔧 Aggiungere messaggi guida quando Echo gate blocca (<8.5) o quando il self-check segnala QA="CHECK" per chiarire i passi di remediation.【F:src/modules/Taverna_NPC.txt†L279-L305】【F:src/modules/Taverna_NPC.txt†L785-L793】

## Terza fase · Rifiniture P3, doc e chiusura backlog

- Nessun task aperto

### Tracciamento avanzamento
| Modulo | Task aperti | Priorità massima | Stato |
| --- | --- | --- | --- |
| Encounter_Designer | 0 | — | Pronto per sviluppo |
| minmax_builder | 0 | — | Pronto per sviluppo |
| Taverna_NPC | 0 | — | Pronto per sviluppo |
| tavern_hub | 0 | — | Pronto per sviluppo |
| Cartelle di servizio | 1 | P2 | Pronto per sviluppo |
| adventurer_ledger | 0 | — | Pronto per sviluppo |
| archivist | 0 | — | Pronto per sviluppo |
| base_profile | 0 | — | Pronto per sviluppo |
| explain_methods | 0 | — | Pronto per sviluppo |
| knowledge_pack | 0 | — | Pronto per sviluppo |
| meta_doc | 2 | P2 | Pronto per sviluppo |
| narrative_flow | 1 | P2 | Pronto per sviluppo |
| ruling_expert | 2 | P2 | Pronto per sviluppo |
| scheda_pg_markdown_template | 1 | P2 | Pronto per sviluppo |
| sigilli_runner_module | 0 | — | Pronto per sviluppo |
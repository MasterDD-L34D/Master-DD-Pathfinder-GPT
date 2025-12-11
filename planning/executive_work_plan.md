# Piano di lavoro esecutivo

Generato il 2025-12-11T15:17:59Z da `tools/generate_module_plan.py`
Fonte task: `planning/module_work_plan.md` (priorità P1→P3) e sequenza `planning/module_review_guide.md`.
Obiettivo: coprire tutte le azioni fino al completamento del piano operativo, con fasi sequenziali e dipendenze esplicite.

### Regole di ordinamento
- Prima i cluster critici: builder/bilanciamento (Encounter_Designer, minmax_builder) e hub/persistenza (Taverna_NPC, tavern_hub, Cartelle di servizio).
- All'interno del cluster, ordine di lettura della guida; poi priorità (P1→P3).

## Fase 1 (attuale) · P1 critici e cross-cutting

- **Encounter_Designer**
  - Nessuno: i gate QA coprono ora pacing, loot e snapshot di bilanciamento e bloccano l’export con CTA esplicite verso `/auto_balance`, `/simulate_encounter`, `/set_pacing` e `/set_loot_policy`.【F:src/modules/Encounter_Designer.txt†L380-L404】
- **minmax_builder**
  - TODO
- **Taverna_NPC**
  - Nessuno: lo storage espone già `/storage_meta` con quota/pattern di auto-name e, con `ALLOW_MODULE_DUMP=false`, i dump vengono tronchi a 4k con marker `[…TRUNCATED ALLOW_MODULE_DUMP=false…]` e risposta standard “⚠️ Output parziale” anche per export plain/markdown, in linea con le policy dichiarate.【F:src/modules/Taverna_NPC.txt†L364-L386】【F:src/modules/Taverna_NPC.txt†L273-L305】【F:src/modules/Taverna_NPC.txt†L1285-L1317】
- **tavern_hub**
  - Nessuno: le CTA export sono allineate alla policy e allo stato dei gate QA.
- **Cartelle di servizio**
  - Nessuno: la risposta include ora marker e header parziale (`X-Content-Partial`, `X-Content-Remaining-Bytes`) con CTA dedicate, e lo storage espone `/storage_meta` con quota residua e auto_name_policy per `taverna_saves`.【F:src/modules/Taverna_NPC.txt†L364-L386】【F:src/modules/Taverna_NPC.txt†L1285-L1317】
- **adventurer_ledger**
  - Nessuno: la coerenza PFS è mantenuta perché `/buy` preserva `pfs_legal` sugli item importati e `enrich_badges` aggiunge badge `PFS:ILLEGAL` quando `policies.pfs_active` è attivo, mentre `craft_estimator` blocca la creazione di item non legali.【F:src/modules/adventurer_ledger.txt†L415-L470】【F:src/modules/adventurer_ledger.txt†L1389-L1435】
- **archivist**
  - Nessuno: la logica di troncamento con header/JSON di lunghezza è descritta e applicata anche ai `.txt`, coerentemente con la policy base/README.【F:src/modules/archivist.txt†L118-L177】【F:src/modules/base_profile.txt†L356-L366】
- **base_profile**
  - Nessuno: l’endpoint di documentazione (`/doc`/`/help`/`/manuale`) è instradato nel router di base_profile e rimanda al modulo `meta_doc.txt` per l’elenco comandi principali.【F:src/modules/base_profile.txt†L140-L175】【F:src/modules/base_profile.txt†L430-L472】
- **explain_methods**
  - Nessuno: l’header del modulo riporta già la versione **3.3-hybrid-kernel** in linea con il changelog e i requisiti QA, senza altre azioni pendenti.【F:src/modules/explain_methods.txt†L1-L4】【F:src/modules/explain_methods.txt†L318-L325】
- **knowledge_pack**
  - TODO
- **meta_doc**
  - TODO
- **narrative_flow**
  - Nessuno aperto: `/qa_story` usa validator concreti e blocca export finché arc/tema/thread/pacing/stile non sono tutti OK, includendo preview troncato e CTA dedicate.【F:src/modules/narrative_flow.txt†L320-L404】
- **ruling_expert**
  - Nessuno.
- **scheda_pg_markdown_template**
  - TODO
- **sigilli_runner_module**
  - TODO

## Seconda fase · P1 residui e P2 cooperativi

- **Encounter_Designer**
  - Nessun miglioramento aperto dopo l’estensione dei gate QA (pacing/loot/balance_snapshot) e dei messaggi di correzione verso i comandi di setup/bilanciamento.【F:src/modules/Encounter_Designer.txt†L380-L404】
- **minmax_builder**
  - Nessuno aperto: le CTA di export riportano ora il nome file previsto (`MinMax_<nome>.pdf/.xlsx/.json`) allineato con la nomenclatura condivisa di Encounter_Designer, riducendo gli equivoci sull’output.【F:src/modules/minmax_builder.txt†L940-L943】【F:src/modules/minmax_builder.txt†L1070-L1088】
- **Taverna_NPC**
  - Nessuno: lo storage espone `/storage_meta` con quota residua, pattern di auto-name e marker di troncamento quando `ALLOW_MODULE_DUMP=false`; i gate Echo/QA includono CTA di remediation (ripeti `/grade` o `/self_check` e disattiva Echo in sandbox) prima di sbloccare salvataggi/export.【F:src/modules/Taverna_NPC.txt†L364-L386】【F:src/modules/Taverna_NPC.txt†L996-L1008】【F:src/modules/Taverna_NPC.txt†L1194-L1208】
- **tavern_hub**
  - Nessuno: i gate QA di `/export_tavern`/`/adventure_outline` bloccono su QA fail con CTA univoca verso `/save_hub` o `/check_conversation`, e lo storage hub/ledger è validato con `schema_min` e quarantena attiva.【F:src/modules/Taverna_NPC.txt†L1285-L1317】【F:src/modules/Taverna_NPC.txt†L1225-L1247】
- **Cartelle di servizio**
  - ✅ CTA Echo/self-check aggiornate: i blocchi Echo<8.5 o QA="CHECK" ora includono passi espliciti (/grade→/self_check, toggle /echo off in sandbox) prima di consentire salvataggi/export.【F:src/modules/Taverna_NPC.txt†L788-L811】【F:src/modules/Taverna_NPC.txt†L1129-L1144】
- **adventurer_ledger**
  - Nessuno: il `cta_guard` mantiene una CTA sintetica nelle call principali e `vendor_cap_gp` ora parte da default 2000 gp con QA che segnala WARN solo se configurato a `null`.【F:src/modules/adventurer_ledger.txt†L29-L68】【F:src/modules/adventurer_ledger.txt†L1672-L1693】
- **archivist**
  - Nessuno aperto: la UX di troncamento include già i metadati di lunghezza residua richiesti.【F:src/modules/archivist.txt†L118-L177】
- **base_profile**
  - Nessuno: la documentazione copre ora health/404 e la distinzione dump/troncamento, in linea con la policy Documentazione.【F:tests/test_app.py†L282-L314】【F:tests/test_app.py†L547-L591】
- **explain_methods**
  - **Deleghe/quiz**: il modulo documenta deleghe ma ne delega enforcement al kernel; quiz teach-back e auto-suggest follow-up già descritti e coerenti con UI hints.【F:src/modules/explain_methods.txt†L30-L48】【F:src/modules/explain_methods.txt†L94-L117】
- **knowledge_pack**
  - Nessuno aperto: la documentazione/client fa già riferimento ai percorsi `.txt` e l’API di metadata restituisce `version`/`compatibility` dal modulo senza necessità di parsing aggiuntivo.【F:docs/api_usage.md†L20-L27】【F:src/app.py†L392-L458】【F:src/modules/knowledge_pack.md†L1-L6】
- **meta_doc**
  - ✅ L’elenco `/modules` ora documenta che, con `ALLOW_MODULE_DUMP=false`, i file possono comparire con size ridotta e suffix `-partial`, chiarendo il comportamento in ambienti a dump limitato.【F:src/modules/meta_doc.txt†L1-L18】
  - ✅ `/render_brew_example` include snippet aggiuntivi HR/Primary (anche combinati) e una CTA di export Homebrewery pronta all’uso.【F:src/modules/meta_doc.txt†L504-L562】【F:src/modules/meta_doc.txt†L614-L640】
- **narrative_flow**
  - Nessuno aperto: l’API fornisce ora header `x-truncated` e `x-original-length` per i dump troncati, chiarendo dimensione originaria e limite applicato.【F:tests/test_app.py†L319-L343】【F:src/app.py†L1420-L1492】
- **ruling_expert**
  - Nessuno: lo stub builder è già documentato con payload di esempio e mapping dei campi, e il `status_example` include CTA esplicito per confermare la stagione PFS prima dei rulings.【F:docs/api_usage.md†L99-L129】【F:src/modules/ruling_expert.txt†L448-L455】
- **scheda_pg_markdown_template**
  - Nessuno aperto: i trigger/policy operative sono documentati nel meta header con CTA di export e note di sblocco.【F:src/modules/scheda_pg_markdown_template.md†L13-L63】【F:src/modules/scheda_pg_markdown_template.md†L35-L63】
- **sigilli_runner_module**
  - Nessuno: logica di assegnazione sigilli e motivazioni MDA/CTA risultano allineate alla checklist.

## Terza fase · Rifiniture P3, doc e chiusura backlog

- Nessun task aperto

### Tracciamento avanzamento
| Modulo | Task aperti | Osservazioni | Errori | Dipendenze | Priorità massima | Stato |
| --- | --- | --- | --- | --- | --- | --- |
| Encounter_Designer | 2 | 2 | 1 | 0 | P1 | Pronto per sviluppo |
| minmax_builder | 2 | 2 | 1 | 0 | P1 | Pronto per sviluppo |
| Taverna_NPC | 2 | 1 | 2 | 0 | P1 | Pronto per sviluppo |
| tavern_hub | 2 | 1 | 1 | 0 | P1 | Pronto per sviluppo |
| Cartelle di servizio | 2 | 1 | 2 | 0 | P1 | Pronto per sviluppo |
| adventurer_ledger | 2 | 1 | 1 | 0 | P1 | Pronto per sviluppo |
| archivist | 2 | 2 | 1 | 0 | P1 | Pronto per sviluppo |
| base_profile | 2 | 2 | 1 | 1 | P1 | Pronto per sviluppo |
| explain_methods | 2 | 1 | 1 | 0 | P1 | Pronto per sviluppo |
| knowledge_pack | 2 | 1 | 1 | 0 | P1 | Pronto per sviluppo |
| meta_doc | 3 | 1 | 1 | 0 | P1 | Pronto per sviluppo |
| narrative_flow | 2 | 1 | 1 | 0 | P1 | Pronto per sviluppo |
| ruling_expert | 2 | 2 | 1 | 0 | P1 | Pronto per sviluppo |
| scheda_pg_markdown_template | 2 | 2 | 1 | 0 | P1 | Pronto per sviluppo |
| sigilli_runner_module | 2 | 3 | 4 | 0 | P1 | Pronto per sviluppo |
# Piano di lavoro esecutivo

Generato il 2025-12-10T15:35:34Z da `tools/generate_module_plan.py`
Fonte task: `planning/module_work_plan.md` (priorità P1→P3) e sequenza `planning/module_review_guide.md`.
Obiettivo: coprire tutte le azioni fino al completamento del piano operativo, con fasi sequenziali e dipendenze esplicite.

### Regole di ordinamento
- Prima i cluster critici: builder/bilanciamento (Encounter_Designer, minmax_builder) e hub/persistenza (Taverna_NPC, tavern_hub, Cartelle di servizio).
- All'interno del cluster, ordine di lettura della guida; poi priorità (P1→P3).

## Fase 1 (attuale) · P1 critici e cross-cutting

- **Encounter_Designer**
  - Nessuno: i gate QA coprono ora pacing, loot e snapshot di bilanciamento e bloccano l’export con CTA esplicite verso `/auto_balance`, `/simulate_encounter`, `/set_pacing` e `/set_loot_policy`.【F:src/modules/Encounter_Designer.txt†L380-L404】
- **minmax_builder**
  - Nessuno: l’help e le CTA finali includono i prerequisiti QA e il naming atteso dei file (`export_build`/`export_vtt`), riducendo gli export falliti o inattesi.【F:src/modules/minmax_builder.txt†L930-L959】【F:src/modules/minmax_builder.txt†L1995-L2017】【F:src/modules/minmax_builder.txt†L2214-L2245】
- **Taverna_NPC**
  - Nessuno: con `ALLOW_MODULE_DUMP=false` ora sono presenti policy di troncamento marcate (`[…TRUNCATED ALLOW_MODULE_DUMP=false…]`) e risposta standardizzata “⚠️ Output parziale” applicata anche agli export plain/markdown.【F:src/modules/Taverna_NPC.txt†L273-L305】
- **tavern_hub**
  - Nessuno: le CTA export sono allineate alla policy e allo stato dei gate QA.
- **Cartelle di servizio**
  - Esporre nella risposta con `ALLOW_MODULE_DUMP=false` un’indicazione chiara che il contenuto è parziale per ridurre confusione sui dump troncati.【F:reports/module_tests/Taverna_NPC.md†L11-L15】
- **adventurer_ledger**
  - Nessuno: la coerenza PFS è mantenuta perché `/buy` preserva `pfs_legal` sugli item importati e `enrich_badges` aggiunge badge `PFS:ILLEGAL` quando `policies.pfs_active` è attivo, mentre `craft_estimator` blocca la creazione di item non legali.【F:src/modules/adventurer_ledger.txt†L415-L470】【F:src/modules/adventurer_ledger.txt†L1389-L1435】
- **archivist**
  - Nessuno: la logica di troncamento/marker per `ALLOW_MODULE_DUMP=false` è ora descritta nel modulo e si applica anche ai `.txt`, coerentemente con la policy base/README.【F:src/modules/archivist.txt†L118-L177】【F:src/modules/base_profile.txt†L356-L366】
- **base_profile**
  - Nessuno: l’endpoint di documentazione (`/doc`/`/help`/`/manuale`) è instradato nel router di base_profile e rimanda al modulo `meta_doc.txt` per l’elenco comandi principali.【F:src/modules/base_profile.txt†L140-L175】【F:src/modules/base_profile.txt†L430-L472】
- **explain_methods**
  - Nessuno: l’header riporta ora la versione 3.3-hybrid-kernel coerente con changelog e tool di monitoraggio.【F:src/modules/explain_methods.txt†L1-L4】【F:src/modules/explain_methods.txt†L318-L325】
- **knowledge_pack**
  - Nessuno: l’endpoint `/modules/{name}/meta` espone `version`/`compatibility` in linea con quanto documentato nel modulo, eliminando parsing testuale lato client.【F:src/modules/knowledge_pack.md†L1-L6】
- **meta_doc**
  - Nessuno: gli esempi di errore per `export_doc` e le checklists Homebrewery (incluso `/render_brew_example`) coprono i gate QA e chiariscono i fallimenti attesi quando mancano fonti o outline.【F:src/modules/meta_doc.txt†L488-L539】【F:src/modules/meta_doc.txt†L820-L829】
- **narrative_flow**
  - Nessuno aperto: `/qa_story` usa validator concreti e blocca export finché arc/tema/thread/pacing/stile non sono tutti OK, includendo preview troncato e CTA dedicate.【F:src/modules/narrative_flow.txt†L320-L404】
- **ruling_expert**
  - Nessuno: la policy `no_raw_dump` è ora applicata lato server (default `ALLOW_MODULE_DUMP=false`), allineando runtime e dichiarazioni del modulo.【F:src/modules/ruling_expert.txt†L80-L85】【c08648†L20-L28】【88122c†L1-L74】
- **scheda_pg_markdown_template**
  - Nessuno: i campi di versione/compatibilità sono esposti nell’header e nei metadati, uniformando il QA automatico agli altri moduli.【F:src/modules/scheda_pg_markdown_template.md†L5-L23】

## Seconda fase · P1 residui e P2 cooperativi

- **Encounter_Designer**
  - Nessun miglioramento aperto dopo l’estensione dei gate QA (pacing/loot/balance_snapshot) e dei messaggi di correzione verso i comandi di setup/bilanciamento.【F:src/modules/Encounter_Designer.txt†L380-L404】
- **minmax_builder**
  - Nessuno: l’help rapido e le CTA finali già rimandano ai gate QA (`export_requires`) e specificano il naming degli export (`MinMax_<nome>.pdf/json`) per `export_build`/`export_vtt`.【F:src/modules/minmax_builder.txt†L930-L959】【F:src/modules/minmax_builder.txt†L1040-L1087】【F:src/modules/minmax_builder.txt†L1995-L2017】【F:src/modules/minmax_builder.txt†L2214-L2245】
- **Taverna_NPC**
  - Nessuno: lo storage espone `/storage_meta` con quota residua, pattern di auto-name e marker di troncamento quando `ALLOW_MODULE_DUMP=false`, e i gate QA/Echo forniscono ora CTA esplicite sugli export e sui blocchi QA.【F:src/modules/Taverna_NPC.txt†L364-L386】【F:src/modules/Taverna_NPC.txt†L1285-L1317】
- **tavern_hub**
  - Nessuno: i gate QA di `/export_tavern`/`/adventure_outline` bloccono su QA fail con CTA univoca verso `/save_hub` o `/check_conversation`, e lo storage hub/ledger è validato con `schema_min` e quarantena attiva.【F:src/modules/Taverna_NPC.txt†L1285-L1317】【F:src/modules/Taverna_NPC.txt†L1225-L1247】
- **Cartelle di servizio**
  - Nessuno: i dump con `ALLOW_MODULE_DUMP=false` includono ora marker di troncamento e note sul contenuto parziale, e i gate Echo/self-check forniscono CTA di remediation per blocchi QA.【F:src/modules/Taverna_NPC.txt†L279-L305】【F:src/modules/Taverna_NPC.txt†L785-L793】【F:reports/module_tests/Taverna_NPC.md†L11-L15】
- **adventurer_ledger**
  - Nessuno: il `cta_guard` mantiene una CTA sintetica nelle call principali e `vendor_cap_gp` ora parte da default 2000 gp con QA che segnala WARN solo se configurato a `null`.【F:src/modules/adventurer_ledger.txt†L29-L68】【F:src/modules/adventurer_ledger.txt†L1672-L1693】
- **archivist**
  - Considerare un header o campo JSON nei dump troncati per indicare size originale e percentuale servita, migliorando la UX rispetto all’attuale marcatore testuale.【F:src/modules/archivist.txt†L118-L177】
- **base_profile**
  - Nessuno: la documentazione copre ora health/404 e la distinzione dump/troncamento, in linea con la policy Documentazione.【F:tests/test_app.py†L282-L314】【F:tests/test_app.py†L547-L591】
- **explain_methods**
  - Nessuno: deleghe e quiz teach-back sono documentati, e il blocco export include filename/JSON e tag MDA allineati ai requisiti QA templati.【F:src/modules/explain_methods.txt†L30-L48】【F:src/modules/explain_methods.txt†L94-L117】
- **knowledge_pack**
  - Nessuno: tutti i percorsi sono documentati con estensione `.txt` e l’endpoint meta è coerente con i client aggiornati.【F:src/modules/knowledge_pack.md†L1-L6】
- **meta_doc**
  - Nessuno: la documentazione `/modules` è stata verificata con `ALLOW_MODULE_DUMP=false` e gli snippet Homebrewery coprono già i pattern richiesti (inclusi esempi aggiuntivi di `/render_brew_example`).【F:src/modules/meta_doc.txt†L488-L539】【F:src/modules/meta_doc.txt†L820-L829】
- **narrative_flow**
  - Nessuno: il troncamento con `ALLOW_MODULE_DUMP=false` espone ora header con size originale e porzione servita, allineando API e policy di comunicazione.【F:src/modules/narrative_flow.txt†L320-L404】
- **ruling_expert**
  - Nessuno: il payload `stub` di `/modules/minmax_builder.txt` è documentato con mappatura ai campi QA e le CTA PFS includono conferma esplicita di stagione/badge.【F:src/modules/ruling_expert.txt†L80-L85】【F:src/modules/ruling_expert.txt†L300-L317】【F:src/modules/ruling_expert.txt†L417-L424】
- **scheda_pg_markdown_template**
  - Nessuno: l'header descrive i trigger/policy operative per l’uso coordinato con Ledger e MinMax, senza task aperti.【F:src/modules/scheda_pg_markdown_template.md†L5-L23】【F:src/modules/scheda_pg_markdown_template.md†L115-L139】
- **sigilli_runner_module**
  - Nessuno: logica di assegnazione sigilli e motivazioni MDA/CTA risultano allineate alla checklist.

## Terza fase · Rifiniture P3, doc e chiusura backlog

- Nessun task aperto

### Tracciamento avanzamento
| Modulo | Task aperti | Priorità massima | Stato |
| --- | --- | --- | --- |
| Encounter_Designer | 0 | P1 | Completato |
| minmax_builder | 0 | P1 | Completato |
| Taverna_NPC | 0 | P1 | Completato |
| tavern_hub | 0 | P1 | Completato |
| Cartelle di servizio | 0 | P1 | Completato |
| adventurer_ledger | 0 | P1 | Completato |
| archivist | 0 | P1 | Completato |
| base_profile | 0 | P1 | Completato |
| explain_methods | 0 | P1 | Completato |
| knowledge_pack | 0 | P1 | Completato |
| meta_doc | 0 | P1 | Completato |
| narrative_flow | 0 | P1 | Completato |
| ruling_expert | 0 | P1 | Completato |
| scheda_pg_markdown_template | 0 | P1 | Completato |
| sigilli_runner_module | 0 | P2 | Completato |

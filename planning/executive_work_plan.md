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
  - Aggiornare l’help e le CTA finali con i prerequisiti QA e con il naming atteso dei file (`export_build`/`export_vtt`) per evitare export falliti o output inattesi.【F:src/modules/minmax_builder.txt†L930-L959】【F:src/modules/minmax_builder.txt†L1995-L2017】【F:src/modules/minmax_builder.txt†L2214-L2245】
- **Taverna_NPC**
  - Nessuno: con `ALLOW_MODULE_DUMP=false` ora sono presenti policy di troncamento marcate (`[…TRUNCATED ALLOW_MODULE_DUMP=false…]`) e risposta standardizzata “⚠️ Output parziale” applicata anche agli export plain/markdown.【F:src/modules/Taverna_NPC.txt†L273-L305】
- **tavern_hub**
  - Nessuno: le CTA export sono allineate alla policy e allo stato dei gate QA.
- **Cartelle di servizio**
  - Esporre nella risposta con `ALLOW_MODULE_DUMP=false` un’indicazione chiara che il contenuto è parziale e integrare un endpoint di quota/metadati per `taverna_saves`, così da ridurre confusione e monitorare l’uso disco delle directory di servizio.【F:reports/module_tests/Taverna_NPC.md†L11-L15】【F:src/modules/Taverna_NPC.txt†L364-L380】
- **adventurer_ledger**
  - Nessuno: la coerenza PFS è mantenuta perché `/buy` preserva `pfs_legal` sugli item importati e `enrich_badges` aggiunge badge `PFS:ILLEGAL` quando `policies.pfs_active` è attivo, mentre `craft_estimator` blocca la creazione di item non legali.【F:src/modules/adventurer_ledger.txt†L415-L470】【F:src/modules/adventurer_ledger.txt†L1389-L1435】
- **archivist**
  - Nessuno: la logica di troncamento/marker per `ALLOW_MODULE_DUMP=false` è ora descritta nel modulo e si applica anche ai `.txt`, coerentemente con la policy base/README.【F:src/modules/archivist.txt†L118-L177】【F:src/modules/base_profile.txt†L356-L366】
- **base_profile**
  - Nessuno: l’endpoint di documentazione (`/doc`/`/help`/`/manuale`) è instradato nel router di base_profile e rimanda al modulo `meta_doc.txt` per l’elenco comandi principali.【F:src/modules/base_profile.txt†L140-L175】【F:src/modules/base_profile.txt†L430-L472】
- **explain_methods**
  - Allineare la versione dichiarata nell’header (oggi 3.2-hybrid) con quella indicata nel changelog 3.3-hybrid-kernel per evitare mismatch in status/reporting e nei tool di monitoraggio versioni.【F:src/modules/explain_methods.txt†L1-L4】【F:src/modules/explain_methods.txt†L318-L325】
- **knowledge_pack**
  - Esportare `version`/`compatibility` direttamente nell’endpoint `/modules/{name}/meta` per coerenza con quanto documentato nel modulo e per evitare parsing testuale lato client.【F:src/modules/knowledge_pack.md†L1-L6】
- **meta_doc**
  - Aggiungere esempi di errore per `export_doc` e per le checklists Homebrewery (incluso `/render_brew_example`) in modo da coprire i gate QA e rendere più chiari i fallimenti attesi quando mancano fonti o outline.【F:src/modules/meta_doc.txt†L488-L539】【F:src/modules/meta_doc.txt†L820-L829】
- **narrative_flow**
  - Nessuno aperto: `/qa_story` usa validator concreti e blocca export finché arc/tema/thread/pacing/stile non sono tutti OK, includendo preview troncato e CTA dedicate.【F:src/modules/narrative_flow.txt†L320-L404】
- **ruling_expert**
  - Applicare la policy `no_raw_dump` anche lato server (configurando `ALLOW_MODULE_DUMP=false` by default o introducendo whitelist) così che il comportamento runtime sia coerente con quanto dichiarato nel modulo.【F:src/modules/ruling_expert.txt†L80-L85】【c08648†L20-L28】【88122c†L1-L74】
- **scheda_pg_markdown_template**
  - Esporre i nuovi campi di versione/compatibilità direttamente nell’header e nei metadati in modo coerente con gli altri moduli, così da abilitare un QA automatico uniforme.【F:src/modules/scheda_pg_markdown_template.md†L5-L23】

## Seconda fase · P1 residui e P2 cooperativi

- **Encounter_Designer**
  - Nessun miglioramento aperto dopo l’estensione dei gate QA (pacing/loot/balance_snapshot) e dei messaggi di correzione verso i comandi di setup/bilanciamento.【F:src/modules/Encounter_Designer.txt†L380-L404】
- **minmax_builder**
  - Integrare l’help rapido con un rimando esplicito ai gate QA (`export_requires`) per ridurre tentativi di export falliti; oggi l’help elenca i comandi ma non indica prerequisiti PFS/fonti.【F:src/modules/minmax_builder.txt†L930-L959】【F:src/modules/minmax_builder.txt†L1995-L2017】
  - Considerare di esporre nell’export o nelle CTA finali il nome file di output/format (es. `MinMax_<nome>.pdf/json`) per allineare le aspettative su `export_build`/`export_vtt`.【F:src/modules/minmax_builder.txt†L1040-L1087】【F:src/modules/minmax_builder.txt†L2214-L2245】
- **Taverna_NPC**
  - Nessuno: lo storage espone `/storage_meta` con quota residua, pattern di auto-name e marker di troncamento quando `ALLOW_MODULE_DUMP=false`, e i gate QA/Echo forniscono ora CTA esplicite sugli export e sui blocchi QA.【F:src/modules/Taverna_NPC.txt†L364-L386】【F:src/modules/Taverna_NPC.txt†L1285-L1317】
- **tavern_hub**
  - Nessuno: i gate QA di `/export_tavern`/`/adventure_outline` bloccono su QA fail con CTA univoca verso `/save_hub` o `/check_conversation`, e lo storage hub/ledger è validato con `schema_min` e quarantena attiva.【F:src/modules/Taverna_NPC.txt†L1285-L1317】【F:src/modules/Taverna_NPC.txt†L1225-L1247】
- **Cartelle di servizio**
  - ⚠️ Con `ALLOW_MODULE_DUMP=false` il contenuto è troncato senza indicare dimensione residua; suggerito header/note che l'output è parziale.【F:reports/module_tests/Taverna_NPC.md†L11-L15】
  - 🔧 Esporre endpoint sui metadati di storage (quota residua, `max_files`) basato su `storage.auto_name_policy` aiuterebbe il monitoraggio della saturazione.【F:src/modules/Taverna_NPC.txt†L364-L380】
  - 🔧 Aggiungere messaggi guida quando Echo gate blocca (<8.5) o quando il self-check segnala QA="CHECK" per chiarire i passi di remediation.【F:src/modules/Taverna_NPC.txt†L279-L305】【F:src/modules/Taverna_NPC.txt†L785-L793】
- **adventurer_ledger**
  - Nessuno: il `cta_guard` mantiene una CTA sintetica nelle call principali e `vendor_cap_gp` ora parte da default 2000 gp con QA che segnala WARN solo se configurato a `null`.【F:src/modules/adventurer_ledger.txt†L29-L68】【F:src/modules/adventurer_ledger.txt†L1672-L1693】
- **archivist**
  - Considerare un header o campo JSON nei dump troncati per indicare size originale e percentuale servita, migliorando la UX rispetto all’attuale marcatore testuale.【F:src/modules/archivist.txt†L118-L177】
- **base_profile**
  - Nessuno: la documentazione copre ora health/404 e la distinzione dump/troncamento, in linea con la policy Documentazione.【F:tests/test_app.py†L282-L314】【F:tests/test_app.py†L547-L591】
- **explain_methods**
  - **Deleghe/quiz**: il modulo documenta deleghe ma ne delega enforcement al kernel; quiz teach-back e auto-suggest follow-up già descritti e coerenti con UI hints.【F:src/modules/explain_methods.txt†L30-L48】【F:src/modules/explain_methods.txt†L94-L117】
  - **Miglioramento suggerito**: aggiungere export filename/JSON e tag MDA nel blocco logging/export per allineare ai requisiti di QA templati (attualmente assenti).【F:src/modules/explain_methods.txt†L193-L205】【F:src/modules/explain_methods.txt†L271-L277】
- **knowledge_pack**
  - **Allineamento estensioni:** il modulo ricorda la migrazione a `.txt` per tutti i percorsi; conviene verificare che eventuali client non referenzino più `.yaml`.【F:src/modules/knowledge_pack.md†L3-L4】
  - **Miglioria potenziale:** includere nelle API di metadata un campo `version`/`compatibility` già presente nel testo per evitare parsing dal corpo del modulo.【F:src/modules/knowledge_pack.md†L1-L6】
- **meta_doc**
  - ⚠️ L’endpoint `/modules` non è stato rieseguito con `ALLOW_MODULE_DUMP=false`, ma la lista non dovrebbe cambiare; verificare se si vuole documentare eventuali differenze di suffix/size in ambienti futuri.
  - 🔧 Potrebbe essere utile aggiungere esempi di `export_doc` fallito per mancanza di fonti/outline per coprire i gate QA definiti nel modulo.【F:src/modules/meta_doc.txt†L820-L829】
  - 🔧 Per chiarezza Homebrewery, si può espandere `/render_brew_example` con snippet visivi aggiuntivi (es. box HR/Primary) seguendo il pattern attuale.【F:src/modules/meta_doc.txt†L488-L539】
- **narrative_flow**
  - **Troncamento vs policy**: l’API tronca i file testuali a 4000 caratteri quando `ALLOW_MODULE_DUMP=false`, ma il comportamento non distingue dimensione residua né segnala header aggiuntivi; valutare esposizione di lunghezza originaria o header `x-truncated`.【F:src/app.py†L581-L601】【F:tests/test_app.py†L268-L295】
- **ruling_expert**
  - **Documentare payload stub builder**: l’endpoint `/modules/minmax_builder.txt` in modalità `stub` costruisce state compositi con `build_state`, `sheet`, `benchmark`, `ledger`, `export` e `composite` coerenti con lo schema del builder; chiarire nel modulo come questi campi si mappano su rulings/QA potrebbe agevolare l’integrazione.【F:src/app.py†L366-L572】
  - **Rafforzare CTA per PFS**: il flow indica season awareness e priorità PFS ma il `status_example` non mostra esplicitamente il badge/season derivato; aggiungere un prompt CTA per confermare la stagione PFS potrebbe ridurre ambiguità di giurisdizione.【F:src/modules/ruling_expert.txt†L300-L317】【F:src/modules/ruling_expert.txt†L417-L424】
- **scheda_pg_markdown_template**
  - Aggiungere un campo “versione” e “compatibilità sistema” nel riepilogo iniziale o nel payload meta per allinearsi ad altri moduli e supportare QA catalogo.【F:src/modules/scheda_pg_markdown_template.md†L5-L23】
  - Documentare nell'header i trigger/policy operative (es. quando abilitare Ledger/MinMax) per chiarezza d'uso nelle pipeline automatiche.【F:src/modules/scheda_pg_markdown_template.md†L115-L139】
- **sigilli_runner_module**
  - Nessuno: logica di assegnazione sigilli e motivazioni MDA/CTA risultano allineate alla checklist.

## Terza fase · Rifiniture P3, doc e chiusura backlog

- Nessun task aperto

### Tracciamento avanzamento
| Modulo | Task aperti | Priorità massima | Stato |
| --- | --- | --- | --- |
| Encounter_Designer | 2 | P1 | Pronto per sviluppo |
| minmax_builder | 3 | P1 | Pronto per sviluppo |
| Taverna_NPC | 2 | P1 | Pronto per sviluppo |
| tavern_hub | 2 | P1 | Pronto per sviluppo |
| Cartelle di servizio | 4 | P1 | Pronto per sviluppo |
| adventurer_ledger | 2 | P1 | Pronto per sviluppo |
| archivist | 2 | P1 | Pronto per sviluppo |
| base_profile | 2 | P1 | Pronto per sviluppo |
| explain_methods | 3 | P1 | Pronto per sviluppo |
| knowledge_pack | 3 | P1 | Pronto per sviluppo |
| meta_doc | 4 | P1 | Pronto per sviluppo |
| narrative_flow | 2 | P1 | Pronto per sviluppo |
| ruling_expert | 3 | P1 | Pronto per sviluppo |
| scheda_pg_markdown_template | 3 | P1 | Pronto per sviluppo |
| sigilli_runner_module | 1 | P2 | Pronto per sviluppo |
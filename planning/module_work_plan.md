# Piano operativo generato dai report

Generato il 2025-12-10T11:31:13Z
Fonte sequenza: `planning/module_review_guide.md`

## Checklist seguita (dal documento di guida)
- Sequenza completa: Encounter_Designer → Taverna_NPC → adventurer_ledger → archivist → base_profile → explain_methods → knowledge_pack → meta_doc → minmax_builder → narrative_flow → ruling_expert → scheda_pg_markdown_template → sigilli_runner_module → tavern_hub → Cartelle di servizio.
- Per ogni report: checklist Ambiente di test → Esiti API → Metadati → Comandi/Flow → QA → Errori → Miglioramenti → Fix necessari.
- Task derivati da Errori/Fix/Miglioramenti con priorità P1 bug/ambiguità, P2 QA/completezza, P3 UX/copy; collegare a sezioni/linee citate nei report.
- Stato modulo: Pronto per sviluppo se i task sono completi e scoped; In attesa se servono dati aggiuntivi.
- Cross-cutting: coordinare builder/bilanciamento (Encounter_Designer, minmax_builder) e hub/persistenza (Taverna_NPC, tavern_hub, Cartelle di servizio).

## Encounter_Designer
- Report: `reports/module_tests/Encounter_Designer.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1][Completato] `compute_effective_cr_from_enemies` unificato sulla versione clampata (qty ∈[1,64], CR ∈[0,40]) e `/auto_balance` puntato esplicitamente allo stesso helper per evitare ambiguità di calcolo.【F:src/modules/Encounter_Designer.txt†L293-L314】【F:src/modules/Encounter_Designer.txt†L777-L788】
- [P1] Ampliare `run_qagates` con gate aggiuntivi per pacing/loot e per la presenza di `balance_snapshot`, bloccando l’export se mancano ondate, loot o la simulazione di rischio/bilanciamento; aggiorna anche i messaggi di QA per guidare l’utente ai comandi `/set_pacing`, `/set_loot_policy`, `/auto_balance` o `/simulate_encounter`.【F:src/modules/Encounter_Designer.txt†L620-L637】【F:src/modules/Encounter_Designer.txt†L357-L398】
- [P2] Estendere i gate QA per coprire pacing/loot/export: oggi la checklist richiede solo nemici, CR stimato e badge/PFS, per cui export può passare anche con ondate vuote o loot mancante. Aggiungere controlli su `pacing`/`loot` eviterebbe snapshot incompleti.【F:src/modules/Encounter_Designer.txt†L620-L637】【F:src/modules/Encounter_Designer.txt†L357-L378】【F:src/modules/Encounter_Designer.txt†L379-L398】
- [P2] Allineare la validazione a `/simulate_encounter`: integrare un gate che verifichi la presenza di `balance_snapshot` (simulazione o auto-balance) garantirebbe export coerenti con i rischi stimati e ridurrebbe QA manuale.【F:src/modules/Encounter_Designer.txt†L316-L350】【F:src/modules/Encounter_Designer.txt†L379-L398】

### Note (Osservazioni/Errori)
- [Osservazione] Il modello dati evita riferimenti a testi protetti: stat e DC sono placeholder numerici astratti, mentre badge e gate PFS delimitano eventuali HR.【F:src/modules/Encounter_Designer.txt†L92-L140】【F:src/modules/Encounter_Designer.txt†L357-L419】
- [Osservazione] Il flusso incorporato consente pipeline completa: setup → generazione/auto-bilanciamento → QA → export VTT/MD/PDF, con CTA che richiamano i comandi chiave e auto-validate prima dell’export.【F:src/modules/Encounter_Designer.txt†L486-L523】【F:src/modules/Encounter_Designer.txt†L400-L419】
- [Osservazione] CR effettivo calcolato con helper unico clampato (qty ∈[1,64], CR ∈[0,40]) richiamato da `/auto_balance`, eliminando la precedente ambiguità di doppia definizione.【F:src/modules/Encounter_Designer.txt†L293-L314】【F:src/modules/Encounter_Designer.txt†L777-L788】

## Taverna_NPC
- Report: `reports/module_tests/Taverna_NPC.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Esporre nella risposta con `ALLOW_MODULE_DUMP=false` un’indicazione chiara che il contenuto è parziale (es. header dimensione residua o nota esplicita) per evitare confusione lato client. 【f250d4†L1-L76】
- [P2] ⚠️ Con `ALLOW_MODULE_DUMP=false` il contenuto viene troncato senza indicare dimensione residua; suggerito aggiungere header/note che l'output è parziale. 【f250d4†L1-L76】
- [P2] 🔧 Miglioria proposta: esporre endpoint dedicato ai metadati di storage (quota residua, `max_files`) basato su configurazione `storage.auto_name_policy` per monitorare saturazione. 【F:src/modules/Taverna_NPC.txt†L364-L380】
- [P2] 🔧 Valutare messaggio di guida quando Echo gate blocca (<8.5) o quando `qa_guard` disattivato da check falliti, per chiarezza UX. 【F:src/modules/Taverna_NPC.txt†L279-L305】【F:src/modules/Taverna_NPC.txt†L785-L793】

### Note (Osservazioni/Errori)
- [Osservazione] Il flusso guidato accompagna l’utente da onboarding lingua/universo/ritratto alle fasi di quiz e generazione PNG, con CTA e template UI dedicati per ogni step.【F:src/modules/Taverna_NPC.txt†L282-L518】【F:src/modules/Taverna_NPC.txt†L838-L974】
- [Errore] ✅ API core rispondono correttamente; `taverna_saves` non esposto (atteso per sicurezza). 【e01c22†L1-L8】
- [Errore] ⚠️ `curl | head` con dump abilitato ritorna errore di write locale, ma il server fornisce `content-length`; nessuna azione necessaria lato server. 【b21fe7†L3-L16】

## adventurer_ledger
- Report: `reports/module_tests/adventurer_ledger.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] **Coerenza PFS in craft/buy:** `craft_estimator` invalida `craft_can_make` su item illegali con PFS attivo ma `/buy` forza `pfs_legal` `true` di default; valutare se ereditare il flag per rispettare audit PFS sui nuovi acquisti.【F:src/modules/adventurer_ledger.txt†L430-L441】【F:src/modules/adventurer_ledger.txt†L1340-L1365】
- [P2] **CTA auto-invocazioni:** il flow `cta_guard` richiede CTA post-azione, ma alcuni output (es. `/qa_suite`) forniscono più CTA in coda; verificare coerenza con policy “1 CTA utile” ed eventualmente limitarla a una singola raccomandazione.【F:src/modules/adventurer_ledger.txt†L1672-L1733】【F:src/modules/adventurer_ledger.txt†L1769-L1772】
- [P2] **Vendor cap default:** `set_policies` accetta `vendor_cap_gp` ma il welcome suggerisce 2000 senza forzarlo; considerare default esplicito o messaggio che ricorda l’assenza di cap per evitare falsi PASS nel QA suite.【F:src/modules/adventurer_ledger.txt†L33-L35】【F:src/modules/adventurer_ledger.txt†L823-L863】【F:src/modules/adventurer_ledger.txt†L1682-L1693】

### Note (Osservazioni/Errori)
- [Osservazione] Il welcome e il flow guidato coprono cinque passi (policy, stile giocatore, profilo WBL, roll loot, export) con CTA e template Markdown/VTT per ledger, buylist e scheda PG pronti all’uso.【F:src/modules/adventurer_ledger.txt†L29-L45】【F:src/modules/adventurer_ledger.txt†L686-L750】【F:src/modules/adventurer_ledger.txt†L1760-L1772】
- [Errore] **Download con ALLOW_MODULE_DUMP=false:** asset JSON viene bloccato come previsto, ma i moduli `.txt` restano scaricabili; confermare se la policy deve valere solo per non testuali o se occorre estenderla ai moduli testuali (oggi non coperti).【0e8b5a†L1-L7】【fd69a0†L1-L41】

## archivist
- Report: `reports/module_tests/archivist.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] **Endpoint download moduli**: applicare la logica di troncamento/403 anche ai moduli `.txt` quando `ALLOW_MODULE_DUMP=false`, coerentemente con README e indicazioni di `base_profile.txt`/`meta_doc`. Esempio: limitare la risposta a 4000 caratteri con suffisso `[contenuto troncato]` per `archivist.txt`.【1411c6†L1-L67】【2130a0†L10-L14】【F:src/modules/base_profile.txt†L356-L366】
- [P2] Allineare il comportamento di `/modules/{name}` al README e ai profili (troncamento a 4000 caratteri o blocco) quando `ALLOW_MODULE_DUMP=false`, includendo un marcatore esplicito per i contenuti parziali.【1411c6†L1-L67】【2130a0†L10-L14】
- [P2] Considerare un header o campo JSON nei dump troncati per indicare size originale e percentuale servita, migliorando la UX rispetto all’attuale mancanza di segnali (vedi anche altri report sui moduli).【1411c6†L1-L67】

### Note (Osservazioni/Errori)
- [Osservazione] ALLOW_MODULE_DUMP=false blocca asset non testuali (`tavern_hub.json`) ma non tronca né blocca i moduli `.txt`: `archivist.txt` viene restituito integralmente, in conflitto con la documentazione che indica troncamento a 4000 caratteri quando il flag è disattivato.【1411c6†L1-L67】【f75b9a†L1-L7】【2130a0†L10-L14】
- [Osservazione] L’endpoint `/modules` rifiuta richieste senza API key con dettaglio chiaro; idem per `/modules/archivist.txt/meta` (401), fornendo copertura ai casi di autenticazione mancata.【d95840†L1-L7】
- [Errore] ⚠️ Mancato troncamento di `archivist.txt` con `ALLOW_MODULE_DUMP=false`: risposta `200` con contenuto completo invece di 403/troncamento.【1411c6†L1-L67】

## base_profile
- Report: `reports/module_tests/base_profile.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Documentare nel codice l’elenco comandi principali anche in un endpoint `/doc` o README per facilitarne la discovery (riferimento sezione `commands` del modulo).【F:src/modules/base_profile.txt†L452-L472】
- [P2] **Coverage API incompleto**: il report precedente non menzionava `/health` né l’errore 404 su modulo inesistente; ora coperti dai test 503/404 con path e status.【F:tests/test_app.py†L304-L314】【F:tests/test_app.py†L547-L591】
- [P2] **Chiarezza dump/troncamento**: esplicitata distinzione testo troncato vs blocco binari con ALLOW_MODULE_DUMP=false per allineare alla policy Documentazione.【F:tests/test_app.py†L282-L302】

### Note (Osservazioni/Errori)
- [Osservazione] Il router centralizza CTA e preset per le modalità specializzate (MinMax, Encounter, Taverna, Narrativa) guidando l’utente con flow e quiz sequenziali e welcome dedicato.【F:src/modules/base_profile.txt†L95-L176】【F:src/modules/base_profile.txt†L452-L560】
- [Osservazione] La pipeline QA integra badge/citazioni/sigilli e ricevute SHA256, collegando i log Echo e gli export di qualità per garantire trasparenza e auditabilità.【F:src/modules/base_profile.txt†L430-L447】【F:src/modules/base_profile.txt†L576-L614】
- [Errore] Nessun errore bloccante riscontrato durante i test di health check, listing e download dei moduli.

## explain_methods
- Report: `reports/module_tests/explain_methods.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Allineare la versione dichiarata nell’header (oggi 3.2-hybrid) con quella indicata nel changelog 3.3-hybrid-kernel per evitare mismatch in status/reporting e nei tool di monitoraggio versioni.【F:src/modules/explain_methods.txt†L1-L4】【F:src/modules/explain_methods.txt†L318-L325】
- [P2] **Deleghe/quiz**: il modulo documenta deleghe ma ne delega enforcement al kernel; quiz teach-back e auto-suggest follow-up già descritti e coerenti con UI hints.【F:src/modules/explain_methods.txt†L30-L48】【F:src/modules/explain_methods.txt†L94-L117】
- [P2] **Miglioramento suggerito**: aggiungere export filename/JSON e tag MDA nel blocco logging/export per allineare ai requisiti di QA templati (attualmente assenti).【F:src/modules/explain_methods.txt†L193-L205】【F:src/modules/explain_methods.txt†L271-L277】

### Note (Osservazioni/Errori)
- [Osservazione] Il flusso guidato con header/CTA seleziona metodo, profondità e speed, propone follow-up/quiz e fornisce template dedicati (ELI5, First Principles, Storytelling, Visualization, Analogies, Technical) con supporto ASCII per la resa visuale.【F:src/modules/explain_methods.txt†L42-L200】【F:src/modules/explain_methods.txt†L149-L171】【F:src/modules/explain_methods.txt†L231-L248】
- [Errore] **Protezione dump**: `exposure_guard` vieta dump integrali, ma con `ALLOW_MODULE_DUMP=true` l'API serve il file completo; con `ALLOW_MODULE_DUMP=false` il troncamento a 4000 char funziona ma non menziona header MIME nel corpo — comportamento conforme all'handler generico.【F:src/app.py†L543-L563】【F:src/modules/explain_methods.txt†L216-L225】【981c3b†L1-L6】

## knowledge_pack
- Report: `reports/module_tests/knowledge_pack.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Esportare `version`/`compatibility` direttamente nell’endpoint `/modules/{name}/meta` per coerenza con quanto documentato nel modulo e per evitare parsing testuale lato client.【F:src/modules/knowledge_pack.md†L1-L6】
- [P2] **Allineamento estensioni:** il modulo ricorda la migrazione a `.txt` per tutti i percorsi; conviene verificare che eventuali client non referenzino più `.yaml`.【F:src/modules/knowledge_pack.md†L3-L4】
- [P2] **Miglioria potenziale:** includere nelle API di metadata un campo `version`/`compatibility` già presente nel testo per evitare parsing dal corpo del modulo.【F:src/modules/knowledge_pack.md†L1-L6】

### Note (Osservazioni/Errori)
- [Osservazione] Il quick start orchestra i moduli principali (quiz PG → MinMax → Encounter → Ledger) e fornisce prompt “copia/incolla” parametrizzati per Taverna, Ruling, Archivist, Narrativa, Explain, semplificando CTA e integrazione UI.【F:src/modules/knowledge_pack.md†L45-L92】【F:src/modules/knowledge_pack.md†L126-L237】
- [Errore] Nessun errore rilevato sulle chiamate API; il troncamento con `ALLOW_MODULE_DUMP=false` è correttamente marcato con `[contenuto troncato]`.【7645d7†L1-L8】

## meta_doc
- Report: `reports/module_tests/meta_doc.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Aggiungere esempi di errore per `export_doc` e per le checklists Homebrewery (incluso `/render_brew_example`) in modo da coprire i gate QA e rendere più chiari i fallimenti attesi quando mancano fonti o outline.【F:src/modules/meta_doc.txt†L488-L539】【F:src/modules/meta_doc.txt†L820-L829】
- [P2] ⚠️ L’endpoint `/modules` non è stato rieseguito con `ALLOW_MODULE_DUMP=false`, ma la lista non dovrebbe cambiare; verificare se si vuole documentare eventuali differenze di suffix/size in ambienti futuri.
- [P2] 🔧 Potrebbe essere utile aggiungere esempi di `export_doc` fallito per mancanza di fonti/outline per coprire i gate QA definiti nel modulo.【F:src/modules/meta_doc.txt†L820-L829】
- [P2] 🔧 Per chiarezza Homebrewery, si può espandere `/render_brew_example` con snippet visivi aggiuntivi (es. box HR/Primary) seguendo il pattern attuale.【F:src/modules/meta_doc.txt†L488-L539】

### Note (Osservazioni/Errori)
- [Osservazione] Il flusso documentale segue le fasi Draft → PeerReview → QA → Publish con CTA esplicite e tool di editing/export (outline, patch suggestion, mappe ASCII, generatori di manuale/how-to) per coprire sia documentazione interna sia bundle Homebrewery.【F:src/modules/meta_doc.txt†L678-L724】【F:src/modules/meta_doc.txt†L831-L835】【F:src/modules/meta_doc.txt†L470-L539】
- [Errore] ✅ Troncamento e 403 sono coerenti con la policy: i dump sono chunked con marker finale e gli asset non testuali vengono bloccati se `ALLOW_MODULE_DUMP=false`.【3e8480†L1-L74】【da084a†L1-L8】

## minmax_builder
- Report: `reports/module_tests/minmax_builder.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Aggiornare l’help e le CTA finali con i prerequisiti QA e con il naming atteso dei file (`export_build`/`export_vtt`) per evitare export falliti o output inattesi.【F:src/modules/minmax_builder.txt†L930-L959】【F:src/modules/minmax_builder.txt†L1995-L2017】【F:src/modules/minmax_builder.txt†L2214-L2245】
- [P2] Integrare l’help rapido con un rimando esplicito ai gate QA (`export_requires`) per ridurre tentativi di export falliti; oggi l’help elenca i comandi ma non indica prerequisiti PFS/fonti.【F:src/modules/minmax_builder.txt†L930-L959】【F:src/modules/minmax_builder.txt†L1995-L2017】
- [P2] Considerare di esporre nell’export o nelle CTA finali il nome file di output/format (es. `MinMax_<nome>.pdf/json`) per allineare le aspettative su `export_build`/`export_vtt`.【F:src/modules/minmax_builder.txt†L1040-L1087】【F:src/modules/minmax_builder.txt†L2214-L2245】

### Note (Osservazioni/Errori)
- [Osservazione] Lo stub builder è validato contro schema `build_core`/`build_extended`; in caso di errore restituisce `500 Stub payload non valido ...` (testato in commit precedente, logica stabile).【F:src/app.py†L556-L570】
- [Osservazione] Il troncamento con `ALLOW_MODULE_DUMP=false` applica `[contenuto troncato]` ai moduli testuali, coerente con handler streaming; utile per review di sicurezza senza esporre l’intero asset.【02412a†L1-L1】【430a71†L3-L3】【F:src/app.py†L589-L600】
- [Errore] Nessun errore bloccante emerso nei test API e negli stub di build.【1cc753†L6-L7】

## narrative_flow
- Report: `reports/module_tests/narrative_flow.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Implementare validator effettivi in `/qa_story` (arc/theme/thread/pacing/style) sostituendo gli stub che restituiscono sempre `True`, così da far emergere errori e coerenze mancanti nelle storie generate.【F:src/modules/narrative_flow.txt†L320-L346】【F:src/modules/narrative_flow.txt†L690-L715】
- [P2] **Troncamento vs policy**: l’API tronca i file testuali a 4000 caratteri quando `ALLOW_MODULE_DUMP=false`, ma il comportamento non distingue dimensione residua né segnala header aggiuntivi; valutare esposizione di lunghezza originaria o header `x-truncated`.【F:src/app.py†L581-L601】【F:tests/test_app.py†L268-L295】
- [P2] **CTA export**: i comandi `/export_*` non specificano filename; definire convenzioni (es. `story_<titolo>.md/pdf`, `beats.csv`) per allineamento con altri moduli di export e con le checklist MDA.【F:src/modules/narrative_flow.txt†L330-L386】【F:src/modules/narrative_flow.txt†L659-L688】

### Note (Osservazioni/Errori)
- [Osservazione] Il flow narrativo in 11 step guida genere, tono, protagonisti, conflitto e arc/tema con retry e cache, integrando template per scene/outline/bible e interfacce con Taverna, Encounter e Ledger tramite seed condivisi.【F:src/modules/narrative_flow.txt†L465-L658】【F:src/modules/narrative_flow.txt†L397-L463】
- [Errore] **Validator stub**: tutte le funzioni `validate_*` ritornano `True`, quindi `/qa_story` non segnala mai errori; implementare logica reale per coerenza con checklist QA.【F:src/modules/narrative_flow.txt†L320-L346】【F:src/modules/narrative_flow.txt†L690-L715】

## ruling_expert
- Report: `reports/module_tests/ruling_expert.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Applicare la policy `no_raw_dump` anche lato server (configurando `ALLOW_MODULE_DUMP=false` by default o introducendo whitelist) così che il comportamento runtime sia coerente con quanto dichiarato nel modulo.【F:src/modules/ruling_expert.txt†L80-L85】【c08648†L20-L28】【88122c†L1-L74】
- [P2] **Documentare payload stub builder**: l’endpoint `/modules/minmax_builder.txt` in modalità `stub` costruisce state compositi con `build_state`, `sheet`, `benchmark`, `ledger`, `export` e `composite` coerenti con lo schema del builder; chiarire nel modulo come questi campi si mappano su rulings/QA potrebbe agevolare l’integrazione.【F:src/app.py†L366-L572】
- [P2] **Rafforzare CTA per PFS**: il flow indica season awareness e priorità PFS ma il `status_example` non mostra esplicitamente il badge/season derivato; aggiungere un prompt CTA per confermare la stagione PFS potrebbe ridurre ambiguità di giurisdizione.【F:src/modules/ruling_expert.txt†L300-L317】【F:src/modules/ruling_expert.txt†L417-L424】

### Note (Osservazioni/Errori)
- [Osservazione] Il flow guidato RAW→FAQ→PFS applica guardrail anti-injection, disambiguazione con soglia 0.65 e CTA post-risposta, offrendo template UI per sezioni RAW/RAI/PFS/HR e strumenti di diagnostica per cache/offline e arithmetic_guard.【F:src/modules/ruling_expert.txt†L284-L356】【F:src/modules/ruling_expert.txt†L331-L410】
- [Errore] **Allineare policy di esposizione**: il modulo dichiara `exposure_policy: no_raw_dump`, ma l’API di default (`ALLOW_MODULE_DUMP=true`) serve il file completo; solo con `ALLOW_MODULE_DUMP=false` avviene il troncamento.【F:src/modules/ruling_expert.txt†L80-L85】【c08648†L20-L28】【88122c†L1-L74】

## scheda_pg_markdown_template
- Report: `reports/module_tests/scheda_pg_markdown_template.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Esporre i nuovi campi di versione/compatibilità direttamente nell’header e nei metadati in modo coerente con gli altri moduli, così da abilitare un QA automatico uniforme.【F:src/modules/scheda_pg_markdown_template.md†L5-L23】
- [P2] Aggiungere un campo “versione” e “compatibilità sistema” nel riepilogo iniziale o nel payload meta per allinearsi ad altri moduli e supportare QA catalogo.【F:src/modules/scheda_pg_markdown_template.md†L5-L23】
- [P2] Documentare nell'header i trigger/policy operative (es. quando abilitare Ledger/MinMax) per chiarezza d'uso nelle pipeline automatiche.【F:src/modules/scheda_pg_markdown_template.md†L115-L139】

### Note (Osservazioni/Errori)
- [Osservazione] Il troncamento mantiene il titolo e il marker finale, utile per audit in ambienti con dump limitato; la lunghezza compatta (4k) preserva contesto iniziale.【300994†L1-L4】
- [Osservazione] Mancano metadati espliciti su versione/compatibilità o policy di trigger; potrebbero essere esposti nel blocco meta iniziale insieme ai toggle per facilitare QA automatizzato.【F:src/modules/scheda_pg_markdown_template.md†L5-L23】
- [Errore] Nessun errore funzionale nelle API; 404 atteso su file mancante.【bff25f†L6-L6】

## sigilli_runner_module
- Report: `reports/module_tests/sigilli_runner_module.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Integrare `code_ok` in `compute_seals` (es. bonus token o sigillo dedicato) oppure rimuoverlo per coerenza con il resto della pipeline di assegnazione sigilli.【F:src/modules/sigilli_runner_module.txt†L108-L118】
- [P2] Esporre motivazioni esplicite per il raro (indice corrente, cooldown residuo) nell’output, seguendo la checklist di trasparenza.【F:src/modules/sigilli_runner_module.txt†L116-L148】【F:src/modules/sigilli_runner_module.txt†L155-L159】
- [P2] Aggiungere tagging MDA/CTA in `output_checklist` o nei seals per allineare il modulo alle convenzioni degli altri report/export.【F:src/modules/sigilli_runner_module.txt†L28-L34】【F:src/modules/sigilli_runner_module.txt†L155-L159】

### Note (Osservazioni/Errori)
- [Osservazione] L’euristica `code_ok` è calcolata ma non influenza sigilli/token: manca qualsiasi uso downstream.【F:src/modules/sigilli_runner_module.txt†L108-L118】
- [Osservazione] Il raro può attivarsi solo da indice 14 con stato di default; documentare la finestra di attivazione per evitare percezione di malfunzionamento iniziale.【F:src/modules/sigilli_runner_module.txt†L116-L148】
- [Osservazione] Il portale viene aggiunto anche quando nessun sigillo è stato assegnato, garantendo almeno un elemento in `seals`.【F:src/modules/sigilli_runner_module.txt†L144-L154】
- [Osservazione] Il presente report incorpora tutti i punti richiesti nelle due iterazioni precedenti (API, metadati, modello dati, flow/CTA, errori simulati e fix suggeriti), senza ulteriori lacune note.
- [Errore] API key mancante: `/modules*` ritorna `401 Invalid or missing API key`, confermato con TestClient.【fc8c1a†L3-L12】
- [Errore] Modulo inesistente: `/modules/bogus.txt` → `404 Module not found`.【5c31d3†L9-L10】
- [Errore] Dump disabilitato: `ALLOW_MODULE_DUMP=false` restituisce header troncato, utile per evitare leak completi.【5c31d3†L11-L18】

## tavern_hub
- Report: `reports/module_tests/tavern_hub.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Allineare le rotte Hub con i gate QA dichiarati, includendo controlli espliciti prima di `/export_tavern`/`/adventure_outline` e aggiungendo messaggio/header di troncamento per asset bloccati, così da mantenere la coerenza con la policy e con il comportamento osservato su altri moduli.【F:src/modules/Taverna_NPC.txt†L1158-L1162】【F:src/modules/Taverna_NPC.txt†L1221-L1231】【3bedc0†L1-L8】
- [P2] **CTA export dipendenti da QA:** i gate QA sono descritti come bloccanti ma alcune rotte stub (`/export_tavern`, `/adventure_outline`) non verificano esplicitamente lo stato prima dell’output; utile allineare implementazione con la policy “Export bloccato se QA FAIL”.【F:src/modules/Taverna_NPC.txt†L1158-L1162】【F:src/modules/Taverna_NPC.txt†L1221-L1231】【F:src/modules/Taverna_NPC.txt†L789-L802】
- [P2] **Storage hub/ledger condiviso:** `ledger_storage` punta a `tavern_hub.json` ma la validazione `hub_storage.validation.schema_min` non è inclusa nello stato; aggiungere schema o riferimenti per ridurre rischi di corruption fra moduli Hub/ledger.【F:src/modules/Taverna_NPC.txt†L382-L386】
- [P2] **Pattern CTA di salvataggio:** `/check_conversation` segnala salvataggi/export pendenti ma non forza snapshot pre-export come raccomandato dal Knowledge Pack; potrebbe auto-invocare `/save_hub`/`/snapshot` quando `handoff_log` è non vuoto.【F:src/modules/Taverna_NPC.txt†L1257-L1259】【F:src/modules/knowledge_pack.md†L111-L113】

### Note (Osservazioni/Errori)
- [Osservazione] L’Hub aggrega quest/rumor/bounty/eventi con flow GameMode, CTA di salvataggio e export, mantenendo storage con rate limit/quarantena e integrazioni con Encounter/Ledger per outline e inventari WBL.【F:src/modules/Taverna_NPC.txt†L1133-L1256】【F:src/modules/Taverna_NPC.txt†L365-L386】【F:src/modules/Taverna_NPC.txt†L789-L802】
- [Errore] **Nessun troncamento con `ALLOW_MODULE_DUMP=false`:** la policy blocca correttamente gli asset non testuali via `403` ma non fornisce versione redatta/troncata; valutare se serve un messaggio più guida o un body minificato per QA automatico.【3bedc0†L1-L8】

## Cartelle di servizio
- Report: `reports/module_tests/service_dirs.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Esporre nella risposta con `ALLOW_MODULE_DUMP=false` un’indicazione chiara che il contenuto è parziale e integrare un endpoint di quota/metadati per `taverna_saves`, così da ridurre confusione e monitorare l’uso disco delle directory di servizio.【F:reports/module_tests/Taverna_NPC.md†L11-L15】【F:src/modules/Taverna_NPC.txt†L364-L380】
- [P2] ⚠️ Con `ALLOW_MODULE_DUMP=false` il contenuto è troncato senza indicare dimensione residua; suggerito header/note che l'output è parziale.【F:reports/module_tests/Taverna_NPC.md†L11-L15】
- [P2] 🔧 Esporre endpoint sui metadati di storage (quota residua, `max_files`) basato su `storage.auto_name_policy` aiuterebbe il monitoraggio della saturazione.【F:src/modules/Taverna_NPC.txt†L364-L380】
- [P2] 🔧 Aggiungere messaggi guida quando Echo gate blocca (<8.5) o quando il self-check segnala QA="CHECK" per chiarire i passi di remediation.【F:src/modules/Taverna_NPC.txt†L279-L305】【F:src/modules/Taverna_NPC.txt†L785-L793】

### Note (Osservazioni/Errori)
- [Osservazione] Le directory di servizio aggregano i template e i workflow Taverna (onboarding, quiz MaxDiff/Pairwise/SJT, export `taverna_saves`) garantendo naming coerente, guardrail Echo e CTA guidate per generazione e salvataggio PNG/quest/rumor.【F:src/modules/Taverna_NPC.txt†L364-L386】【F:src/modules/Taverna_NPC.txt†L428-L965】
- [Errore] ✅ API core rispondono correttamente; `taverna_saves` non esposto (scelta di sicurezza).【F:reports/module_tests/Taverna_NPC.md†L7-L13】
- [Errore] ⚠️ `curl | head` con dump abilitato può fallire in locale per errore di scrittura ma il server fornisce `content-length`; nessuna azione lato server.【F:reports/module_tests/Taverna_NPC.md†L11-L13】

## Cross-cutting e dipendenze
- Builder/Bilanciamento (Encounter_Designer, minmax_builder): usare i task sopra per valutare epic condivise su export/QA o flow di bilanciamento; ordinare i fix P1 prima dei miglioramenti.
- Hub/Persistenza (Taverna_NPC, tavern_hub, Cartelle di servizio): verificare coerenza delle policy di salvataggio/quarantena e annotare eventuali blocchi prima di procedere con altri moduli dipendenti.

## Chiusura
- Compila il sommario sprint con numero task, priorità massima e blocchi per modulo usando la tabella seguente.

| Modulo | Task totali | Priorità massima | Stato |
| --- | --- | --- | --- |
| Encounter_Designer | 4 | P1 | Pronto per sviluppo |
| Taverna_NPC | 4 | P1 | Pronto per sviluppo |
| adventurer_ledger | 3 | P1 | Pronto per sviluppo |
| archivist | 3 | P1 | Pronto per sviluppo |
| base_profile | 3 | P1 | Pronto per sviluppo |
| explain_methods | 3 | P1 | Pronto per sviluppo |
| knowledge_pack | 3 | P1 | Pronto per sviluppo |
| meta_doc | 4 | P1 | Pronto per sviluppo |
| minmax_builder | 3 | P1 | Pronto per sviluppo |
| narrative_flow | 3 | P1 | Pronto per sviluppo |
| ruling_expert | 3 | P1 | Pronto per sviluppo |
| scheda_pg_markdown_template | 3 | P1 | Pronto per sviluppo |
| sigilli_runner_module | 3 | P1 | Pronto per sviluppo |
| tavern_hub | 4 | P1 | Pronto per sviluppo |
| Cartelle di servizio | 4 | P1 | Pronto per sviluppo |
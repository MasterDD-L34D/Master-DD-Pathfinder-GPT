# Piano operativo generato dai report

Generato il 2025-12-10T15:35:34Z
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
- [P1] Nessuno: i gate QA coprono ora pacing, loot e snapshot di bilanciamento e bloccano l’export con CTA esplicite verso `/auto_balance`, `/simulate_encounter`, `/set_pacing` e `/set_loot_policy`.【F:src/modules/Encounter_Designer.txt†L380-L404】
- [P2] Nessun miglioramento aperto dopo l’estensione dei gate QA (pacing/loot/balance_snapshot) e dei messaggi di correzione verso i comandi di setup/bilanciamento.【F:src/modules/Encounter_Designer.txt†L380-L404】

### Note (Osservazioni/Errori)
- [Osservazione] Il modello dati evita riferimenti a testi protetti: stat e DC sono placeholder numerici astratti, mentre badge e gate PFS delimitano eventuali HR.【F:src/modules/Encounter_Designer.txt†L92-L140】【F:src/modules/Encounter_Designer.txt†L357-L419】
- [Osservazione] Il flusso incorporato consente pipeline completa: setup → generazione/auto-bilanciamento → QA → export VTT/MD/PDF, con CTA che richiamano i comandi chiave e auto-validate prima dell’export.【F:src/modules/Encounter_Designer.txt†L486-L523】【F:src/modules/Encounter_Designer.txt†L400-L419】
- [Errore] Nessun errore bloccante sul calcolo CR/QA dopo l’allineamento al singolo helper clampato.【F:src/modules/Encounter_Designer.txt†L293-L314】【F:src/modules/Encounter_Designer.txt†L777-L788】

## Taverna_NPC
- Report: `reports/module_tests/Taverna_NPC.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Nessuno: con `ALLOW_MODULE_DUMP=false` ora sono presenti policy di troncamento marcate (`[…TRUNCATED ALLOW_MODULE_DUMP=false…]`) e risposta standardizzata “⚠️ Output parziale” applicata anche agli export plain/markdown.【F:src/modules/Taverna_NPC.txt†L273-L305】
- [P2] Nessuno: lo storage espone `/storage_meta` con quota residua, pattern di auto-name e marker di troncamento quando `ALLOW_MODULE_DUMP=false`, e i gate QA/Echo forniscono ora CTA esplicite sugli export e sui blocchi QA.【F:src/modules/Taverna_NPC.txt†L364-L386】【F:src/modules/Taverna_NPC.txt†L1285-L1317】

### Note (Osservazioni/Errori)
- [Osservazione] Il flusso guidato accompagna l’utente da onboarding lingua/universo/ritratto alle fasi di quiz e generazione PNG, con CTA e template UI dedicati per ogni step.【F:src/modules/Taverna_NPC.txt†L282-L518】【F:src/modules/Taverna_NPC.txt†L838-L974】
- [Errore] ✅ API core rispondono correttamente; `taverna_saves` non esposto (atteso per sicurezza). 【e01c22†L1-L8】
- [Errore] ⚠️ `curl | head` con dump abilitato ritorna errore di write locale, ma il server fornisce `content-length`; nessuna azione necessaria lato server. 【b21fe7†L3-L16】

## adventurer_ledger
- Report: `reports/module_tests/adventurer_ledger.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Nessuno: la coerenza PFS è mantenuta perché `/buy` preserva `pfs_legal` sugli item importati e `enrich_badges` aggiunge badge `PFS:ILLEGAL` quando `policies.pfs_active` è attivo, mentre `craft_estimator` blocca la creazione di item non legali.【F:src/modules/adventurer_ledger.txt†L415-L470】【F:src/modules/adventurer_ledger.txt†L1389-L1435】
- [P2] Nessuno: il `cta_guard` mantiene una CTA sintetica nelle call principali e `vendor_cap_gp` ora parte da default 2000 gp con QA che segnala WARN solo se configurato a `null`.【F:src/modules/adventurer_ledger.txt†L29-L68】【F:src/modules/adventurer_ledger.txt†L1672-L1693】

### Note (Osservazioni/Errori)
- [Osservazione] Il welcome e il flow guidato coprono cinque passi (policy, stile giocatore, profilo WBL, roll loot, export) con CTA e template Markdown/VTT per ledger, buylist e scheda PG pronti all’uso.【F:src/modules/adventurer_ledger.txt†L29-L45】【F:src/modules/adventurer_ledger.txt†L686-L750】【F:src/modules/adventurer_ledger.txt†L1760-L1772】
- [Errore] **Download con ALLOW_MODULE_DUMP=false:** asset JSON viene bloccato come previsto, ma i moduli `.txt` restano scaricabili; confermare se la policy deve valere solo per non testuali o se occorre estenderla ai moduli testuali (oggi non coperti).【0e8b5a†L1-L7】【fd69a0†L1-L41】

## archivist
- Report: `reports/module_tests/archivist.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Nessuno: la logica di troncamento/marker per `ALLOW_MODULE_DUMP=false` è ora descritta nel modulo e si applica anche ai `.txt`, coerentemente con la policy base/README.【F:src/modules/archivist.txt†L118-L177】【F:src/modules/base_profile.txt†L356-L366】
- [P2] Considerare un header o campo JSON nei dump troncati per indicare size originale e percentuale servita, migliorando la UX rispetto all’attuale marcatore testuale.【F:src/modules/archivist.txt†L118-L177】

### Note (Osservazioni/Errori)
- [Osservazione] I dump seguono ora la policy `no_raw_dump`: con `ALLOW_MODULE_DUMP=false` i moduli testuali vengono troncati e marcati con `[…TRUNCATED ALLOW_MODULE_DUMP=false…]`, mentre asset non testuali restano bloccati; gli endpoint proteggono comunque l’accesso senza API key con 401 esplicito.【F:src/modules/archivist.txt†L118-L177】【F:src/modules/archivist.txt†L280-L311】【F:src/modules/archivist.txt†L312-L332】
- [Osservazione] L’endpoint `/modules` rifiuta richieste senza API key con dettaglio chiaro; idem per `/modules/archivist.txt/meta` (401), fornendo copertura ai casi di autenticazione mancata.【d95840†L1-L7】
- [Errore] Nessun errore bloccante rilevato dopo l’allineamento della dump policy.

## base_profile
- Report: `reports/module_tests/base_profile.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Nessuno: l’endpoint di documentazione (`/doc`/`/help`/`/manuale`) è instradato nel router di base_profile e rimanda al modulo `meta_doc.txt` per l’elenco comandi principali.【F:src/modules/base_profile.txt†L140-L175】【F:src/modules/base_profile.txt†L430-L472】
- [P2] Nessuno: la documentazione copre ora health/404 e la distinzione dump/troncamento, in linea con la policy Documentazione.【F:tests/test_app.py†L282-L314】【F:tests/test_app.py†L547-L591】

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
- [P2] **Allineamento estensioni:** il modulo ricorda la migrazione a `.txt` per tutti i percorsi; conviene verificare che eventuali client puntino ai percorsi Knowledge Pack in `.txt` (non a suffix legacy).【F:src/modules/knowledge_pack.md†L3-L4】
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
- [P1] Nessuno aperto: `/qa_story` usa validator concreti e blocca export finché arc/tema/thread/pacing/stile non sono tutti OK, includendo preview troncato e CTA dedicate.【F:src/modules/narrative_flow.txt†L320-L404】
- [P2] **Troncamento vs policy**: l’API tronca i file testuali a 4000 caratteri quando `ALLOW_MODULE_DUMP=false`, ma il comportamento non distingue dimensione residua né segnala header aggiuntivi; valutare esposizione di lunghezza originaria o header `x-truncated`.【F:src/app.py†L581-L601】【F:tests/test_app.py†L268-L295】

### Note (Osservazioni/Errori)
- [Osservazione] Il flow narrativo in 11 step guida genere, tono, protagonisti, conflitto e arc/tema con retry e cache, integrando template per scene/outline/bible e interfacce con Taverna, Encounter e Ledger tramite seed condivisi; il QA ora fornisce checklist dettagliata, flag export e CTA su arc/tema/hook/pacing/stile.【F:src/modules/narrative_flow.txt†L465-L658】【F:src/modules/narrative_flow.txt†L320-L404】
- [Errore] Nessun errore bloccante rilevato dopo l’attivazione dei validator reali in `/qa_story`.

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
- [P2] Nessuno: logica di assegnazione sigilli e motivazioni MDA/CTA risultano allineate alla checklist.

### Note (Osservazioni/Errori)
- [Osservazione] Il raro può attivarsi solo da indice 14 con stato di default; documentare la finestra di attivazione per evitare percezione di malfunzionamento iniziale.【F:src/modules/sigilli_runner_module.txt†L116-L148】
- [Osservazione] Il portale viene aggiunto anche quando nessun sigillo è stato assegnato, garantendo almeno un elemento in `seals`.【F:src/modules/sigilli_runner_module.txt†L144-L154】
- [Osservazione] Il presente report incorpora tutti i punti richiesti nelle due iterazioni precedenti (API, metadati, modello dati, flow/CTA, errori simulati e fix applicati), senza ulteriori lacune note.
- [Errore] API key mancante: `/modules*` ritorna `401 Invalid or missing API key`, confermato con TestClient.【fc8c1a†L3-L12】
- [Errore] Modulo inesistente: `/modules/bogus.txt` → `404 Module not found`.【5c31d3†L9-L10】
- [Errore] Dump disabilitato: `ALLOW_MODULE_DUMP=false` restituisce header troncato, utile per evitare leak completi.【5c31d3†L11-L18】
- [Errore] Nessun errore bloccante dopo l’integrazione di `code_ok` e il tagging MDA/CTA nei sigilli.

## tavern_hub
- Report: `reports/module_tests/tavern_hub.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Nessuno: le CTA export sono allineate alla policy e allo stato dei gate QA.
- [P2] Nessuno: i gate QA di `/export_tavern`/`/adventure_outline` bloccono su QA fail con CTA univoca verso `/save_hub` o `/check_conversation`, e lo storage hub/ledger è validato con `schema_min` e quarantena attiva.【F:src/modules/Taverna_NPC.txt†L1285-L1317】【F:src/modules/Taverna_NPC.txt†L1225-L1247】

### Note (Osservazioni/Errori)
- [Osservazione] L’Hub aggrega quest/rumor/bounty/eventi con flow GameMode, CTA di salvataggio e export, mantenendo storage con rate limit/quarantena e integrazioni con Encounter/Ledger per outline e inventari WBL.【F:src/modules/Taverna_NPC.txt†L1133-L1256】【F:src/modules/Taverna_NPC.txt†L365-L386】【F:src/modules/Taverna_NPC.txt†L789-L802】
- [Errore] Nessun errore aperto: con `ALLOW_MODULE_DUMP=false` gli asset JSON vengono bloccati via `403` come da policy, mentre gli export hub ereditano ora marker di troncamento e logging gate quando necessario.【3bedc0†L1-L8】【F:src/modules/Taverna_NPC.txt†L1285-L1310】

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

## Riepilogo osservazioni ed errori
| Modulo | Osservazioni | Errori | Totale note |
| --- | --- | --- | --- |
| sigilli_runner_module | 3 | 4 | 7 |
| Encounter_Designer | 2 | 1 | 3 |
| Taverna_NPC | 1 | 2 | 3 |
| archivist | 2 | 1 | 3 |
| base_profile | 2 | 1 | 3 |
| minmax_builder | 2 | 1 | 3 |
| scheda_pg_markdown_template | 2 | 1 | 3 |
| Cartelle di servizio | 1 | 2 | 3 |
| adventurer_ledger | 1 | 1 | 2 |
| explain_methods | 1 | 1 | 2 |
| knowledge_pack | 1 | 1 | 2 |
| meta_doc | 1 | 1 | 2 |
| narrative_flow | 1 | 1 | 2 |
| ruling_expert | 1 | 1 | 2 |
| tavern_hub | 1 | 1 | 2 |
## Cross-cutting e dipendenze
- Builder/Bilanciamento (Encounter_Designer, minmax_builder): usare i task sopra per valutare epic condivise su export/QA o flow di bilanciamento; ordinare i fix P1 prima dei miglioramenti.
- Hub/Persistenza (Taverna_NPC, tavern_hub, Cartelle di servizio): verificare coerenza delle policy di salvataggio/quarantena e annotare eventuali blocchi prima di procedere con altri moduli dipendenti.

## Chiusura
- Compila il sommario sprint con numero task, priorità massima e blocchi per modulo usando la tabella seguente.

| Modulo | Task totali | Priorità massima | Osservazioni | Errori | Stato |
| --- | --- | --- | --- | --- | --- |
| Encounter_Designer | 2 | P1 | 2 | 1 | Pronto per sviluppo |
| Taverna_NPC | 2 | P1 | 1 | 2 | Pronto per sviluppo |
| adventurer_ledger | 2 | P1 | 1 | 1 | Pronto per sviluppo |
| archivist | 2 | P1 | 2 | 1 | Pronto per sviluppo |
| base_profile | 2 | P1 | 2 | 1 | Pronto per sviluppo |
| explain_methods | 3 | P1 | 1 | 1 | Pronto per sviluppo |
| knowledge_pack | 3 | P1 | 1 | 1 | Pronto per sviluppo |
| meta_doc | 4 | P1 | 1 | 1 | Pronto per sviluppo |
| minmax_builder | 3 | P1 | 2 | 1 | Pronto per sviluppo |
| narrative_flow | 2 | P1 | 1 | 1 | Pronto per sviluppo |
| ruling_expert | 3 | P1 | 1 | 1 | Pronto per sviluppo |
| scheda_pg_markdown_template | 3 | P1 | 2 | 1 | Pronto per sviluppo |
| sigilli_runner_module | 1 | P2 | 3 | 4 | Pronto per sviluppo |
| tavern_hub | 2 | P1 | 1 | 1 | Pronto per sviluppo |
| Cartelle di servizio | 4 | P1 | 1 | 2 | Pronto per sviluppo |
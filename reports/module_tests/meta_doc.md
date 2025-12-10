# Verifica API e analisi modulo `meta_doc.txt`

## Ambiente di test
- **Run A (dump completo):** `API_KEY=testing ALLOW_ANONYMOUS=true uvicorn src.app:app --port 8000`.
- **Run B (dump troncato/blocco binari):** `API_KEY=testing ALLOW_ANONYMOUS=true ALLOW_MODULE_DUMP=false uvicorn src.app:app --port 8000`.

## Esiti API
- `/health` → `200 OK` con check directory e file richiesti per i moduli.【197691†L1-L8】【5e978c†L1-L8】
- `/modules` → `200 OK`; 14 asset elencati con `meta_doc.txt` (31.380 B, `.txt`).【8d0cc7†L1-L13】
- `/modules/meta_doc.txt/meta` → `200 OK`; `{name,size_bytes,suffix}` coerente con l’elenco.【0c57c4†L1-L8】
- `/modules/meta_doc.txt` con dump abilitato → `200 OK`, header `text/plain`, download completo 31.380 B.【3f926b†L1-L25】
- `/modules/meta_doc.txt` con `ALLOW_MODULE_DUMP=false` → `200 OK`, risposta chunked con terminatore `[contenuto troncato]`.【3e8480†L1-L74】
- `/modules/wrongname.txt` → `404` con dettaglio `Module not found`.【5a3066†L1-L8】
- `/modules/tavern_hub.json` con `ALLOW_MODULE_DUMP=false` → `403 Module download not allowed` (asset non testuale).【da084a†L1-L8】

## Metadati e scopo
- **Identità/integrazioni:** modulo `Documenti` v1.6 (2025-08-23) ereditato da `base_profile.txt`; integra MinMax, Taverna, Encounter, Ledger, Archivist, Explain/Ruling.【F:src/modules/meta_doc.txt†L1-L28】
- **Principi & policy:** recupero via API con header `x-api-key`, badge RAW/RAI/PFS/HR/🧠META e preferenza per estratti; dump completo solo se `ALLOW_MODULE_DUMP=true`.【F:src/modules/meta_doc.txt†L7-L18】【F:src/modules/meta_doc.txt†L836-L846】
- **Scopo operativo:** blueprint per Spec/README/Changelog/Release Notes/Knowledge Pack/Homebrewery, peer review simulata a tre esperti e pacchetti ZIP finali.【F:src/modules/meta_doc.txt†L13-L18】【F:src/modules/meta_doc.txt†L97-L105】
- **Trigger:** creazione documenti (README/Release/Changelog/Knowledge Pack), peer review, indice/TOC, merge moduli, conversione GPT→YAML.【F:src/modules/meta_doc.txt†L29-L45】

## Modello dati (campi principali)
- `doc_state`: `id`, `title`, `kind`, `module_targets/targets`, `outline`, `sections`, fonti RAW/RAI/PFS/META/archivist/reference, embed per MinMax/Taverna/Encounter/Ledger/diagrammi, stile (tone/audience/language), review checklist/commenti, export flags e struttura ZIP `ProjectName_GPT` con cartelle 1-5 e README_FIRST.【F:src/modules/meta_doc.txt†L52-L110】
- `sources.META`: libreria PDF (Gear Guide, Items Master List, Useful Items, Ultimate Crafter) come fonti META di supporto.【F:src/modules/meta_doc.txt†L106-L113】

## Comandi principali (parametri, effetti sullo stato, output)
- `/new_doc <kind> <titolo>`: imposta `doc_state.id/title/kind/outline` e conferma creazione.【F:src/modules/meta_doc.txt†L228-L240】
- `/set_targets [..]`: aggiorna `doc_state.module_targets/targets` e output di conferma.【F:src/modules/meta_doc.txt†L242-L250】
- `/import_template <blueprint>`: valida blueprint (spec/readme/release/changelog/knowledge/briefing/manuale_brew), aggiorna outline o warning se invalido.【F:src/modules/meta_doc.txt†L252-L263】
- `/embed_from <module> <opts>`: append embed generici e per modulo (MinMax/Taverna/Encounter/Ledger/Archivist/Explain/Ruling) con output dedicati.【F:src/modules/meta_doc.txt†L264-L308】
- `/diagram <label>`: aggiunge mermaid scaffold a `embeds.diagrams`, output di conferma.【F:src/modules/meta_doc.txt†L310-L316】
- `/attach_sources <raw_refs> <pfs_refs> <meta_refs>`: sincronizza fonti RAW/PFS/META e contatori nel review state.【F:src/modules/meta_doc.txt†L318-L333】
- `/checklist <preset>`: imposta checklist coerente con spec/readme/release e output ✅.【F:src/modules/meta_doc.txt†L334-L343】
- `/peer_review`: popola commenti dei tre ruoli (LLM Specialist, Master Pathfinder, Prompt Designer) e output 🧐.【F:src/modules/meta_doc.txt†L345-L360】
- `/toc`: genera indice dalle sezioni in outline.【F:src/modules/meta_doc.txt†L362-L368】
- `/section set|append <name> <md>`: set/append sezione in `doc_state.sections` con output di conferma.【F:src/modules/meta_doc.txt†L369-L383】
- `/manuale`, `/doc`, `/howto`, `/map_docs`: output informativi/ricerca semantica/ASCII map basati su registri core.【F:src/modules/meta_doc.txt†L384-L408】
- `/lint_docs`, `/patch_suggest`, `/examples`, `/convert_gpt_to_module`, `/status_docs`, `/doc_export`: diagnostica e export sintetici.【F:src/modules/meta_doc.txt†L409-L439】
- `/export_doc <format>`: valida presenza outline e fonti RAW/PFS prima di esportare md/pdf/canvas/zip (set variabili locali).【F:src/modules/meta_doc.txt†L440-L458】
- `/doc_pack`: esporta ZIP finale mostrando la struttura della cartella standard e invoca export zip.【F:src/modules/meta_doc.txt†L459-L469】
- `/brew_lint`, `/export_doc_brew`, `/render_brew_example <kind>`: checklist Homebrewery V3, export brew, snippet cover/toc/box/raw/pfs/meta/wrap/watercolor/center.【F:src/modules/meta_doc.txt†L470-L539】

## Flow guidato e CTA
- Pipeline `Draft → PeerReview → QA → Publish` con CTA primaria “Avvia Peer Review” che lancia `/peer_review`.【F:src/modules/meta_doc.txt†L831-L835】
- `visual_mapping` abilita mappe ASCII per scope Core/Module/Flow; `manual_generator` produce manuale dinamico (intro, modalità, flussi, file, sicurezza, glossario) con export md/pdf.【F:src/modules/meta_doc.txt†L678-L724】【F:src/modules/meta_doc.txt†L679-L694】
- `doc_search` (metodo hybrid) con sezioni output Sintesi/Estratto/Fonte/Voci correlate; `howto_engine` template per guide rapide.【F:src/modules/meta_doc.txt†L695-L715】

## QA templates, helper e policy
- Gates export: outline >0, almeno una fonte RAW/PFS, e versione presente per Release Notes; errori dedicati per mancanza fonti/outline/versione.【F:src/modules/meta_doc.txt†L820-L829】
- `lint_docs` controlla sezioni mancanti, ref interrotte, coerenza termini, presenza how-to per ogni comando; `patch_suggest` propone fix con diff unified.【F:src/modules/meta_doc.txt†L738-L749】
- Policy sicurezza: output consentiti solo come estratti/riassunti/tabelle/ASCII; vietati dump integrali/codice interno; leak_guards attivi.【F:src/modules/meta_doc.txt†L638-L644】
- Community Use assets marcati META (Record Sheets, Pregenerated Characters), da non citare come RAW/PFS.【F:src/modules/meta_doc.txt†L662-L677】
- Helper: badge renderer, outline di default per tipo documento, scaffold mermaid, utilities Homebrewery (footer/center/watercolor/wrap).【F:src/modules/meta_doc.txt†L114-L193】

## Osservazioni
- Il flusso documentale segue le fasi Draft → PeerReview → QA → Publish con CTA esplicite e tool di editing/export (outline, patch suggestion, mappe ASCII, generatori di manuale/how-to) per coprire sia documentazione interna sia bundle Homebrewery.【F:src/modules/meta_doc.txt†L678-L724】【F:src/modules/meta_doc.txt†L831-L835】【F:src/modules/meta_doc.txt†L470-L539】

## Errori
- ✅ Troncamento e 403 sono coerenti con la policy: i dump sono chunked con marker finale e gli asset non testuali vengono bloccati se `ALLOW_MODULE_DUMP=false`.【3e8480†L1-L74】【da084a†L1-L8】

## Miglioramenti suggeriti
- ⚠️ L’endpoint `/modules` non è stato rieseguito con `ALLOW_MODULE_DUMP=false`, ma la lista non dovrebbe cambiare; verificare se si vuole documentare eventuali differenze di suffix/size in ambienti futuri.
- 🔧 Potrebbe essere utile aggiungere esempi di `export_doc` fallito per mancanza di fonti/outline per coprire i gate QA definiti nel modulo.【F:src/modules/meta_doc.txt†L820-L829】
- 🔧 Per chiarezza Homebrewery, si può espandere `/render_brew_example` con snippet visivi aggiuntivi (es. box HR/Primary) seguendo il pattern attuale.【F:src/modules/meta_doc.txt†L488-L539】

## Fix necessari
- Aggiungere esempi di errore per `export_doc` e per le checklists Homebrewery (incluso `/render_brew_example`) in modo da coprire i gate QA e rendere più chiari i fallimenti attesi quando mancano fonti o outline.【F:src/modules/meta_doc.txt†L488-L539】【F:src/modules/meta_doc.txt†L820-L829】

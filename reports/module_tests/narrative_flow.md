# Verifica API e analisi modulo `narrative_flow.txt`

## Ambiente di test
- Client: `TestClient` FastAPI con API key forzata (`allow_anonymous=false`) e reset dello stato di backoff ad ogni test.【F:tests/test_app.py†L19-L114】
- Flag: run default con `ALLOW_MODULE_DUMP=true`; scenari di sicurezza con `disable_module_dump` per simulare `ALLOW_MODULE_DUMP=false` sui download.【F:tests/test_app.py†L25-L33】【F:tests/test_app.py†L268-L295】
- Percorsi fittizi per directory mancanti e validazione `_validate_directories` mockata per coprire health check e listing moduli/knowledge.【F:tests/test_app.py†L33-L96】【F:tests/test_app.py†L529-L546】

## Esiti API
1. **`GET /health`** — `200 OK` con stato `ok` e percorsi `modules`/`data`; errori `503` quando directory o file obbligatori mancanti.【F:tests/test_app.py†L549-L616】
2. **`GET /modules`** — `503` se la directory moduli è assente; altrimenti elenco disponibile (coperto dai fixture health).【F:tests/test_app.py†L529-L536】
3. **`GET /modules/narrative_flow.txt/meta`** — `200 OK`, payload `name/size_bytes/suffix` coerente con il file su disco.【F:tests/test_app.py†L298-L307】
4. **`GET /modules/narrative_flow.txt`** — con dump abilitato: `200 OK`, `content-type: text/plain`, nessun troncamento.【F:src/app.py†L573-L601】
5. **Dump disabilitato (`ALLOW_MODULE_DUMP=false`)** — file testuali restano accessibili ma troncati a 4000 caratteri con marker finale `[contenuto troncato]` e header aggiuntivi `x-truncated=true` / `x-original-length=<byte>` che riportano dimensione originaria e limite di troncamento; asset binari/PDF restituiscono `403 Module download not allowed`.【F:tests/test_app.py†L252-L295】【F:tests/test_app.py†L319-L343】【F:src/app.py†L1420-L1492】
6. **Errori standard** — path traversal → `400 Invalid module path`; nome errato → `404 Module not found`; knowledge traversal → `404 Knowledge file not found`.【F:tests/test_app.py†L214-L340】

## Metadati, scopo e integrazioni
- Profilo: Modalità **Narrativa** v2.3, erede di `base_profile.txt`, focalizzata su storie/ambientazioni/roleplay con Story Bible, Outline/Beats, Scene Tracker, guard-rail immagini, mappa ASCII e ponti verso moduli tattici.【F:src/modules/narrative_flow.txt†L1-L35】
- Trigger e tools: frasi naturali per storie/salvataggi/visualizzazioni e compat con tool legacy `dall-e`, `memory`, `interactive_flow` più router hint per intent Narrativa/Explain/Archivist/MinMax.【F:src/modules/narrative_flow.txt†L15-L34】
- Registrazione router: il profilo base mappa la modalità Narrativa nel kernel router per prompt segmentati multiruolo.【F:src/modules/base_profile.txt†L107-L135】
- Knowledge Pack: indicizzata come endpoint `/modules/narrative_flow` nella tabella router della documentazione rapida.【F:src/modules/knowledge_pack.md†L56-L64】

## Modello dati e safety/QA
- **State**: `story_state` include genere/tono/premise, Bible (protagonisti/cast/luoghi), timeline con `continuity_flags`, `open_threads`, stile e safety defaults (content_safety).【F:src/modules/narrative_flow.txt†L35-L64】
- **Image guardrails**: blacklist (minorenni/gore/hate symbols), sanitizer con azioni reject/soften e strategy di sostituzione; policy di carry dello style seed quando lock attivo.【F:src/modules/narrative_flow.txt†L65-L87】
- **Metriche**: `narrative_metrics` per tensione/valenza/pacing, `arc_engine` (want/need/lie/ghost/flaw/change_signal), `theme_engine` con tagging per scena, `motif_registry` con regole di richiamo Chekhov, `continuity_watch` e `style_bible` con preset HighFantasy/DashiellNoir e pacing controller per words/dialogo.【F:src/modules/narrative_flow.txt†L88-L156】
- **QA templates**: validator enum/non-empty, gate `story_requires`, checklist `story_qa`, retry 2 tentativi; validator operativi su arco/tema/thread/pacing/stile aggiornano `story_state.qa.*`, calcolano `ready_for_export` e includono preview troncato a 520 caratteri con marker `[TRUNCATED]` quando necessario.【F:src/modules/narrative_flow.txt†L158-L186】【F:src/modules/narrative_flow.txt†L320-L404】

## Comandi principali e impatto sullo stato
- **Setup/Storia**: `/create_story`, `/generate_scene`, `/continue_story`+alias `/load_story`, `/save_story`, `/list_saved_stories`, `/check_conversation` — settano `genre/tone`, caricano/salvano `story_state`, serializzano sessioni con chiave `story_<titolo>`.【F:src/modules/narrative_flow.txt†L190-L262】
- **Personaggi**: `/save_character`, `/list_saved_characters` aggiornano `protagonists`; `/visualize` produce placeholder visual con art_style/seed correnti.【F:src/modules/narrative_flow.txt†L238-L258】
- **Stile/Sicurezza**: `/set_art_style`, `/style_lock` (autogenera seed se ON), `/content_safety` aggiornano `story_state.style` e `safety`; output conferma lock/seed e livello filtro.【F:src/modules/narrative_flow.txt†L263-L288】
- **Outline/Bible/Tracker**: `/outline`, `/beat`, `/bible`, `/scene_tracker`, `/explain_theme` gestiscono timeline/hook e inoltri didattici (emit event).【F:src/modules/narrative_flow.txt†L290-L318】
- **QA/Arc/Theme/Motif/Metrics/Export**: `/qa_story` calcola preview e lancia i validator reali, setta flag QA e blocca gli export se non tutti `ok`; `/arc`, `/theme`, `/motif_add`/`/register_chekhov`, `/plot_curve`, export MD/CSV/PDF con filename espliciti (`story_bible.md`, `story_beats.csv`, `narrative_story.md/.pdf`) e nota “partial preview” se il QA è stato troncato.【F:src/modules/narrative_flow.txt†L320-L404】
- **Integrazioni cross-modulo**: seed PNG → Taverna NPC, encounter seed → Encounter Designer, ledger log → Adventurer Ledger, explain/ruling requests, export arco/tema a MinMax, continuity ad Archivist (via emit_event).【F:src/modules/narrative_flow.txt†L397-L463】
- **UI templates**: schede scena/outline/bible/arc e sparkline tensione pronti per rendering (campi e struttura).【F:src/modules/narrative_flow.txt†L465-L503】

## Flusso guidato e CTA
- Flow di 11 step con cache e retry=3: genere → tono → protagonista (validazione non empty) → conflitto → mondo → arco/tema/Chekhov → scena apertura (apre hook e setta `last_scene_id`) → curva narrativa → visual protagonista → roleplay → salvataggi storia/PG → chiusura con call a `/check_conversation`.【F:src/modules/narrative_flow.txt†L504-L658】

## QA templates, helper e formule
- Gates/checklist descritti sopra; helper `now` per seed/time; estensioni `mda` con checklist tecnica/operativa e visual mapping ASCII. Export supporta MD/CSV/PDF, con naming implicito dai comandi `/export_*`.【F:src/modules/narrative_flow.txt†L659-L732】【F:src/modules/narrative_flow.txt†L717-L724】

## Osservazioni
- Il flow narrativo in 11 step guida genere, tono, protagonisti, conflitto e arc/tema con retry e cache, integrando template per scene/outline/bible e interfacce con Taverna, Encounter e Ledger tramite seed condivisi; il QA ora fornisce checklist dettagliata, flag export e CTA su arc/tema/hook/pacing/stile.【F:src/modules/narrative_flow.txt†L465-L658】【F:src/modules/narrative_flow.txt†L320-L404】

## Errori
- Nessun errore bloccante rilevato dopo l’attivazione dei validator reali in `/qa_story`.

## Miglioramenti suggeriti
- Nessuno aperto: l’API fornisce ora header `x-truncated` e `x-original-length` per i dump troncati, chiarendo dimensione originaria e limite applicato.【F:tests/test_app.py†L319-L343】【F:src/app.py†L1420-L1492】

## Fix necessari
- Nessuno aperto: `/qa_story` usa validator concreti e blocca export finché arc/tema/thread/pacing/stile non sono tutti OK, includendo preview troncato e CTA dedicate.【F:src/modules/narrative_flow.txt†L320-L404】

# Verifica API e analisi modulo `base_profile.txt`

## Ambiente di test
- Pytest mirato su endpoint `/modules` e policy di autenticazione/troncamento: `python -m pytest tests/test_app.py::test_correct_api_key_allows_access tests/test_app.py::test_get_module_content_valid_file tests/test_app.py::test_get_module_meta_valid_file tests/test_app.py::test_text_module_truncated_when_dump_disabled tests/test_app.py::test_missing_api_key_returns_unauthorized tests/test_app.py::test_allow_anonymous_access` (6 test passati, solo warning di deprecazione jsonschema).【56fa11†L1-L12】
- Verifica manuale con `TestClient` FastAPI impostando `API_KEY=inline-test` e `ALLOW_ANONYMOUS=false` per ottenere metadati e contenuto reali di `base_profile.txt`.【fe5e21†L1-L3】
- Server FastAPI locale con `ALLOW_MODULE_DUMP` variabile per simulare download intero vs troncato e override temporaneo di `MODULES_DIR`/`DATA_DIR` per gli health check.【F:tests/test_app.py†L282-L294】【F:tests/test_app.py†L547-L591】

## Esiti API
1. **`GET /health`** — Con directory e file richiesti presenti ritorna `200 OK` e payload `status: ok`; se `MODULES_DIR`/`DATA_DIR` mancano o se manca un file richiesto, risponde `503` con dettaglio puntuale degli errori.【F:tests/test_app.py†L547-L591】
2. **`GET /modules`** — Con API key valida `200 OK`, confermando la visibilità della lista moduli.【F:tests/test_app.py†L417-L419】
3. **`GET /modules/base_profile.txt/meta`** — `200 OK` con metadati `name/size_bytes/suffix` come da schema di `test_get_module_meta_valid_file`.【F:tests/test_app.py†L294-L303】
4. **`GET /modules/base_profile.txt`** — `200 OK`, content-type `text/plain`; la prima riga riporta `module_name: "Pathfinder Master DD - Base Profile"`. Download completo ammesso quando `ALLOW_MODULE_DUMP=true`.【F:src/modules/base_profile.txt†L1-L25】
5. **Errore nome errato** — `/modules/missing_module.txt/meta` restituisce `404 Module not found`, confermando la protezione da enumerazione.【F:tests/test_app.py†L304-L314】
6. **Troncamento con `ALLOW_MODULE_DUMP=false`** — I file di testo vengono restituiti con marcatore finale `[contenuto troncato]` (esempio su `large_module.txt`); PDF e binari vengono bloccati (`403 Module download not allowed`).【F:tests/test_app.py†L282-L302】
7. **Accesso senza API key (predefinito)** — Con `ALLOW_ANONYMOUS=false` viene risposto `401 Invalid or missing API key` su `/modules`.【F:tests/test_app.py†L390-L399】
8. **Accesso anonimo opzionale** — Con `ALLOW_ANONYMOUS=true` e nessuna API key `/modules` torna `200 OK`, consentendo l’elenco anonimo.【F:tests/test_app.py†L444-L448】
9. **`GET /modules/preload_all_modules.txt`** — Senza API key risponde `401 Invalid or missing API key`; con header `x-api-key` valido ritorna il bundle di preload (status `206` per troncamento con `ALLOW_MODULE_DUMP=false`), confermando l’endpoint protetto e pronto al warmup.【3ae972†L1-L4】【F:src/modules/preload_all_modules.txt†L1-L15】
10. **Verifica BAS-CHK-19 (API key + preload)** — Esecuzione manuale con `TestClient` e `API_KEY=test-api-key`: `/modules/preload_all_modules.txt` restituisce `206` con header `X-Content-Partial=true`, `ALLOW_MODULE_DUMP` disattivo e guard `runtime.preload_done` attiva nel router.【4fce5c†L1-L7】【F:src/modules/base_profile.txt†L148-L156】
11. **Riesecuzione BAS-CHK-19 (preload protetto con API key)** — Con `settings.api_key=test-api-key` e dump disattivo, `GET /modules/preload_all_modules.txt` restituisce `206` con header `X-Content-Partial=true` e warning di troncamento, confermando il warmup protetto; la guard `runtime.preload_done` resta configurata nel router per marcare l’avvenuto preload.【9a9887†L1-L2】【F:src/modules/base_profile.txt†L148-L156】
12. **BAS-CHK-19 — verifica odierna con API key dedicata** — Con `API_KEY=qa-preload-key` e dump disattivo, `GET /modules/preload_all_modules.txt` risponde `206` con header `X-Content-Partial=true` e testo troncato, confermando il preload protetto che abilita la guard `runtime.preload_done` nel router.【8c37bc†L1-L6】【F:src/modules/base_profile.txt†L148-L156】
13. **BAS-CHK-19 — verifica automatizzata (API key, troncamento, binding su disco)** — Senza header `x-api-key` `/modules/preload_all_modules.txt` risponde `401`; con chiave valida ritorna `206` con header di parzialità (`ALLOW_MODULE_DUMP=false`) e, attivando `ALLOW_MODULE_DUMP=true`, espone l’elenco completo dei binding core, tutti presenti su disco. La guard `runtime.preload_done` resta dichiarata nel router base_profile per marcare il preload.【F:tests/test_app.py†L581-L619】【F:tests/test_app.py†L242-L246】【F:src/modules/preload_all_modules.txt†L1-L15】【F:src/modules/base_profile.txt†L148-L156】

- Copertura API completata con test automatici e run manuali: health/modules/meta/download hanno esiti attesi, 401/404 vengono restituiti correttamente e il troncamento è verificato quando `ALLOW_MODULE_DUMP=false`.【56fa11†L1-L12】【F:tests/test_app.py†L282-L314】

## Metadati e scopo del modulo
- Kernel interno versione **3.7-kernel** aggiornato al **2025-09-05**, ruolo “Assistente AI multifunzionale specializzato in Pathfinder 1e” con welcome message dedicato alla Taverna Master DD.【F:src/modules/base_profile.txt†L1-L24】
- Principi chiave: priorità RAW/RAI/PFS, separazione per ambiti (Ruling, Archivist, MinMax, Encounter, Loot, Narrativa), trasparenza fonti e controlli anti-allucinazione/drift.【F:src/modules/base_profile.txt†L29-L52】
- Router integrato con modalità specializzate (Archivist, Ruling Expert, Taverna NPC, Narrativa, Explain, MinMax Builder, Encounter Designer, Libro Mastro, Documentazione) e binding ai rispettivi file modulo.【F:src/modules/base_profile.txt†L107-L117】
- Scopi operativi: garantire routing hard-gate, enforcement tag trasparenza, compatibilità PFS e governance Sigilli/Echo con logger QA e warmup preload.【F:src/modules/base_profile.txt†L360-L374】【F:src/modules/base_profile.txt†L600-L645】

## Dipendenze
- Elencare moduli esterni, API o asset (file, immagini, modelli) su cui il modulo fa affidamento, includendo per ciascuno una citazione in linea al blocco di codice che definisce il link o l’endpoint di riferimento.【F:src/modules/base_profile.txt†L95-L117】【F:src/modules/base_profile.txt†L430-L447】
- Preload silente: la regola iniziale del router imposta `runtime.preload_done` e richiama `Preload_Warmup`/`Ingest` usando il bundle `preload_all_modules.txt` o l’endpoint omonimo protetto da API key.【F:src/modules/base_profile.txt†L142-L150】【F:src/modules/base_profile.txt†L252-L262】【F:src/modules/preload_all_modules.txt†L1-L15】
- Controllo file binding: tutti i `file_binding` del router puntano a moduli core presenti su disco; nessun riferimento mancante rilevato.【2879d6†L2-L3】【F:src/modules/base_profile.txt†L114-L122】【F:src/modules/preload_all_modules.txt†L1-L15】

## Modello dati e stato
- **Toggles**: pfs, language, terse_mode, show_badges/show_sources, spoiler, echo_gate/echo_persona, image_constraints, expert; controllano filtri PFS, lingua, lunghezza, spoiler e grading Echo.【F:src/modules/base_profile.txt†L368-L388】
- **Session state**: reset ad ogni nuova chat, default output_mode `tldr`, seasonal e user_tone disattivati, QA log interno attivo; `/state reset` ripristina i default.【F:src/modules/base_profile.txt†L382-L401】【F:src/modules/base_profile.txt†L469-L472】
- **Sigilli meta**: tokens, threshold, storage_dir `.sigilli_state`, awardHint high per moduli MinMax/Encounter/Ledger; receipt SHA256 via post-processor.【F:src/modules/base_profile.txt†L568-L617】
- **Policy citazioni e filtri PFS**: tag RAW/RAI/PFS/🏛️/📖, callout `⚠️ Non PFS-legal: <elemento> — motivo/sorgente`, preferenza EN per nomi ufficiali.【F:src/modules/base_profile.txt†L29-L52】【F:src/modules/base_profile.txt†L402-L416】

## Comandi principali
- **Setup/Diagnostica**: `/set_mode <mode>`, `/status`, `/diagnostic`, `/base_self_check`, `/show_base_map`, `/state reset`, `/expert on|off` per attivare log sicuro; auto-invocazioni: preload silente e QA autotest on-build.【F:src/modules/base_profile.txt†L107-L117】【F:src/modules/base_profile.txt†L452-L472】【F:src/modules/base_profile.txt†L642-L666】
- **Ambiente/obiettivi**: `/mode tldr|full|sources|fast|full` modifica output_mode; `/lang en|it|mixed` imposta lingua; `/pfs on|off` abilita filtro PFS; `/spoiler on|off` gestisce indice AP spoiler.【F:src/modules/base_profile.txt†L452-L470】【F:src/modules/base_profile.txt†L532-L546】
- **Nemici/bilanciamento & simulazione**: `/start_build` avvia build in 7 fasi (brief→QA→export); `/start_encounter` nel router indirizza a Encounter Designer; quiz core guida raccolta requisiti PG/PNG.【F:src/modules/base_profile.txt†L452-L459】【F:src/modules/base_profile.txt†L520-L531】【F:src/modules/base_profile.txt†L553-L560】
- **Pacing/loot**: `/token reset|spend <n>`, `/sigilli threshold <n>`, `/sigilli status|award|help|mode`, `/quest claim`, `/sigilli on|off` governano mini-gioco Sigilli e Gettoni; export template per loot/build in markdown/VTT/CSV.【F:src/modules/base_profile.txt†L460-L472】【F:src/modules/base_profile.txt†L520-L524】【F:src/modules/base_profile.txt†L580-L609】
- **QA/Export**: `/grade` mostra quality_report (Echo), `/portrait_validate` valida prompt immagine, `quality_report_json` e `portrait_prompt_txt` template dedicati, `qa_logging` attacca log a diagnostic/export.【F:src/modules/base_profile.txt†L468-L472】【F:src/modules/base_profile.txt†L520-L529】【F:src/modules/base_profile.txt†L576-L584】
- **Narrazione/lifecycle**: `/estrai_pg` crea schede da chat, `/seasonal ...` applica temi, router indirizza prompt narrativi a Taverna/Narrativa; conferme `✅ Profilo '{nome}' caricato` e `✅ Modalità attiva: {modalita}` a ogni cambio stato.【F:src/modules/base_profile.txt†L452-L464】【F:src/modules/base_profile.txt†L95-L105】

## Flow guidato, CTA e template
- Router con preload silente e segmenter per dividere richieste multi-intento; regole CTA per comandi diretti (/help, /start_build, /start_encounter, /quiz).【F:src/modules/base_profile.txt†L120-L176】
- Workflow MinMax Builder in 7 fasi più export `markdown_sheet`, `vtt_json`, `excel_csv`; CTA implicito a chiudere con QAExport/quality_report.【F:src/modules/base_profile.txt†L520-L528】
- Quiz core limita domande (≤10) con sequenza razza→classe→archetipo→talenti e output duale (profilo personalità + raccomandazioni build).【F:src/modules/base_profile.txt†L553-L560】

## QA templates e helper
- **QA pipeline**: soglia qualità 8.8, step sanity_check → rules_consistency → pfs_gate → citation_attach → echo_grade/echo_gate → echo_self_audit.【F:src/modules/base_profile.txt†L430-L447】
- **Helpers**: `build_reply_meta` arricchisce risposte con badge/policy/sigilli, `build_quality_receipt` genera receipt SHA256, `attach_sigilli` applica post-processor condizionale.【F:src/modules/base_profile.txt†L576-L614】
- **Export QA**: template `quality_report_json` e `audit_report` (Echo) più log QA allegato su diagnostic/export.【F:src/modules/base_profile.txt†L520-L529】【F:src/modules/base_profile.txt†L596-L602】

## Osservazioni
- Il router centralizza CTA e preset per le modalità specializzate (MinMax, Encounter, Taverna, Narrativa) guidando l’utente con flow e quiz sequenziali e welcome dedicato.【F:src/modules/base_profile.txt†L95-L176】【F:src/modules/base_profile.txt†L452-L560】
- La pipeline QA integra badge/citazioni/sigilli e ricevute SHA256, collegando i log Echo e gli export di qualità per garantire trasparenza e auditabilità.【F:src/modules/base_profile.txt†L430-L447】【F:src/modules/base_profile.txt†L576-L614】

## Errori
- Nessun errore bloccante riscontrato durante i test di health check, listing e download dei moduli.

## Miglioramenti suggeriti
- Nessuno: la documentazione copre ora health/404 e la distinzione dump/troncamento, in linea con la policy Documentazione.【F:tests/test_app.py†L282-L314】【F:tests/test_app.py†L547-L591】

## Fix necessari
- BAS-OBS-01: confermato l’instradamento `/doc`/`/help`/`/manuale` verso `meta_doc.txt` nel router base_profile, con nota nel modulo.【F:src/modules/base_profile.txt†L130-L176】【F:src/modules/base_profile.txt†L430-L472】
- BAS-ERR-01: nessun errore bloccante dopo l’allineamento documentazione/dump; validato dal run pytest sugli endpoint `/modules*` (401, 404, troncamento, download valido).【ca78a1†L1-L14】【F:src/modules/base_profile.txt†L356-L366】

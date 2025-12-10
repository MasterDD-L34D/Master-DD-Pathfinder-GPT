# Verifica API e analisi modulo `archivist.txt`

## Ambiente di test
- Server FastAPI locale avviato con `uvicorn src.app:app --port 8000`, variabili `API_KEY=testing`, `ALLOW_ANONYMOUS=false`.
- Riavvio con `ALLOW_MODULE_DUMP=false` per verificare il blocco/troncamento dei dump modulo.

## Esiti API
1. **`GET /health`** — `200 OK`; directory moduli/dati presenti, nessun file richiesto mancante.【9757cf†L1-L9】
2. **`GET /modules`** con API key — `200 OK`; elenca 14 asset con size/suffix, incluso `archivist.txt` (31.533 byte).【1f1e71†L1-L10】
3. **`GET /modules/archivist.txt/meta`** — `200 OK`; metadati `{name, size_bytes, suffix}` coerenti con la lista.【eb4fae†L1-L7】
4. **`GET /modules/archivist.txt`** con `ALLOW_MODULE_DUMP=false` — `200 OK`; il file viene comunque restituito integralmente (nessun troncamento/403).【1411c6†L1-L67】
5. **`GET /modules/tavern_hub.json`** con `ALLOW_MODULE_DUMP=false` — `403 Forbidden`; download asset non testuale bloccato come da policy.【f75b9a†L1-L7】
6. **`GET /modules/notfound.txt`** — `404 Not Found`; errore strutturato `{detail:"Module not found"}`.【cc5c36†L1-L7】
7. **`GET /knowledge`** — `200 OK`; sette asset disponibili (4 PDF, 3 JSON) con size/suffix.【580f0e†L1-L10】
8. **`GET /knowledge/Items%20Master%20List.pdf/meta`** — `200 OK`; metadati coerenti con elenco (256.148 byte, `.pdf`).【647b50†L1-L7】
9. **`GET /knowledge/doesnotexist/meta`** — `404 Not Found`; dettaglio `Knowledge file not found`.【ef67b0†L1-L7】
10. **Errore autenticazione** — `GET /modules/archivist.txt/meta` senza API key → `401 Invalid or missing API key`.【d95840†L1-L7】

## Metadati / Scopo del modulo
- Nome **Archivist** v3.6.1 (last_updated 2025-08-20); eredità `base_profile.txt`; tipo `lore+qa+vtt`; descrizione: modulo monolitico per lore PF1e con QA citazioni, gestione campagne (AV/NC/SX/SX00/SX10) e generatore mappe VTT gridless.【F:src/modules/archivist.txt†L1-L19】
- Principi/sicurezza: `block_prompt_leak: true` con frase di rifiuto esplicita; core_min 3.0; monolith_mode false; integrazioni dichiarate con Explain, Ruling Expert, Taverna NPC, MinMax Builder.【F:src/modules/archivist.txt†L20-L33】
- Trigger/obiettivi: frasi multi-parola per lore, campagne interne e VTT, con alias legacy mappati a intent/command; obiettivi centrati su fonti citabili, gestione campagne e mappe gridless.【F:src/modules/archivist.txt†L36-L84】【F:src/modules/archivist.txt†L86-L99】
- Fonti/badge: priorità ISWG > CS_PC > AP > PFS > AON > PRD_MOE > WIKI > ALTERVISTA > DEV, con regole di conflitto e tag 🧭 PFS-Lore; badge RAW/PFS/Dev/House/Secondary definiti.【F:src/modules/archivist.txt†L101-L126】
- Policy filtro: citazioni obbligatorie (≤25 parole, min 1 fonte), edition/spoiler/exposure guard, low confidence policy che forza ❗House Lore e richiesta di restringimento.【F:src/modules/archivist.txt†L128-L176】
- Scopi VTT: camera ortografica 90°, gridless, preset parametri/temi, ID e snapshot SX00, badge canon, liste spoiler AP e bundle export.【F:src/modules/archivist.txt†L178-L243】【F:src/modules/archivist.txt†L210-L236】

## Modello dati (state/logging)
- Stato runtime: modalità locale automatica, spoiler_mode `light`, output modes (Sintesi/Completo/Solo fonti), speed `balanced/fast/full` definiscono il profilo di risposta.【F:src/modules/archivist.txt†L280-L297】
- Oggetti mappa: campi obbligatori per metadata (map_id, theme/features/complexity/mood/size/format, badge, seed/prompt_hash/engine_params, safe_area/bleed, tile/grid hints) più note GM.【F:src/modules/archivist.txt†L430-L457】
- Session log lite: registra timestamp, topic, entity_type, speed/spoiler_mode, fonti e varianti PFS, conflitti, flag incertezza, asset mappa, badge, aggiornamenti SX00 e flag qualità mappa (top_down/gridless/leggibilità/coerenza/max-space/anti-pattern/ground).【F:src/modules/archivist.txt†L530-L554】
- Stato campagna: esempio `/status` mostra SX00 attiva con conteggi AV/NC/SX, confermando che lo stato conserva parametri campagna e deleghe abilitate.【F:src/modules/archivist.txt†L608-L628】

## Comandi principali
- **Setup/UI**: greeting iniziale per intent VTT con CTA su tema/feature/mood/complexity/size; hint prompt e follow-up su timeline, confronto 🧭, agganci PNG, dashboard SX00.【F:src/modules/archivist.txt†L300-L320】
- **Lore**: `/lore`, `/timeline`, `/deity`, `/region`, `/city`, `/faction`, `/person`, `/plane`, `/artifact`, `/pfs_lore_diff`, `/source`, `/list_sources`; parametri per topic/profondità/output/speed/spoiler. Effetti: attivano pipeline lore con citazioni e badge.【F:src/modules/archivist.txt†L322-L349】
- **Campaign**: `/campaign_new`, `/av_generate`, `/nc_create`, `/sx_table`, `/sx00_dashboard`, `/sx10_balance_check`, `/rel_update`, `/export`, `/status`; aggiornano SX00, generano AV/NC/SX, bilanciano campagne e producono export MD/PDF/VTT.【F:src/modules/archivist.txt†L336-L362】
- **VTT**: `/vtt_map`, `/vtt_random`, `/vtt_custom`, `/vtt_attach_to`, `/vtt_hazards`, `/vtt_features`, `/vtt_lighting`, `/vtt_scale`, `/vtt_variants`, `/vtt_export_notes`, `/vtt_preset_*`, `/vtt_balance_*`, `/vtt_export_map`, `/vtt_export_bundle`; parametri per tema/feature/complexity/mood/size/variants/badge/export format; effetti: generazione immagini, QA map_audit, collegamenti SX00, export bundle/notes.【F:src/modules/archivist.txt†L351-L388】【F:src/modules/archivist.txt†L398-L424】
- **QA/Diagnostica**: `quality_checks` per fonti/badge/spoiler/redirect/tono/conflitti/varietà sessioni/crosslink e regole VTT (top_down, gridless, leggibilità, coerenza, anti-pattern, ground_only, SX00 link). Strumenti `/lore_self_check`, `/map_audit`, `/spoiler_scan`, `/confidence_report` ecc. per audit automatici.【F:src/modules/archivist.txt†L470-L498】【F:src/modules/archivist.txt†L516-L529】
- **Flow guidato**: pipeline core (guardrails → intent → disambiguate → retrieve/cross-verify → conflicts → confidence_gate → format/cite → QA), subpipeline campaign e VTT con retry/backoff/failover e spoiler scan; auto-CTA in suggestion_engine che propone Explain/Ruling/PNG/mappa/dashboard SX00 dopo ogni output.【F:src/modules/archivist.txt†L400-L468】【F:src/modules/archivist.txt†L500-L514】
- **Template UI/Narrativi**: output_structure con sezioni default e template per divinità/regioni/città/fazioni/personaggi/timeline/cosmologia/piani/artefatti/AV/NC/SX/SX00/SX10; voce narrante world-builder con focus scenico; map_metadata template e GM notes incluse.【F:src/modules/archivist.txt†L438-L469】【F:src/modules/archivist.txt†L458-L468】

## QA templates & helper
- Gate principali: fonti minime, badge corretti, rispetto spoiler_mode, redirect meccaniche, tono accademico, conflitti esplicitati, varietà sessioni, crosslink AV↔NC↔SX00; per mappe: top_down/gridless/leggibilità/coerenza/maximize_space/anti_pattern/ground_only/SX00_linked.【F:src/modules/archivist.txt†L470-L498】
- Formule e badge: preferenza fonti primarie ISWG/CS con tag 🧭 PFS-Lore su varianti; canon_badge input accetta 📗/🔎/❗ e alias HOUSE; map_id formato `MAP-{yy}{mm}{dd}-{rand4hex}`; snapshot SX00 con backlinks e policy di logging/metrics su generazioni e errori.【F:src/modules/archivist.txt†L203-L236】【F:src/modules/archivist.txt†L220-L237】【F:src/modules/archivist.txt†L530-L554】
- Export: profili bundle con immagine+gm_notes+metadata_json (png/json/md) e comandi /export per AV/NC/SX; output citation_format definito con campi book/page/url.【F:src/modules/archivist.txt†L236-L243】【F:src/modules/archivist.txt†L260-L279】

## Osservazioni
- ALLOW_MODULE_DUMP=false blocca asset non testuali (`tavern_hub.json`) ma non tronca né blocca i moduli `.txt`: `archivist.txt` viene restituito integralmente, in conflitto con la documentazione che indica troncamento a 4000 caratteri quando il flag è disattivato.【1411c6†L1-L67】【f75b9a†L1-L7】【2130a0†L10-L14】
- L’endpoint `/modules` rifiuta richieste senza API key con dettaglio chiaro; idem per `/modules/archivist.txt/meta` (401), fornendo copertura ai casi di autenticazione mancata.【d95840†L1-L7】

## Errori riscontrati
- ⚠️ Mancato troncamento di `archivist.txt` con `ALLOW_MODULE_DUMP=false`: risposta `200` con contenuto completo invece di 403/troncamento.【1411c6†L1-L67】

## Miglioramenti suggeriti
- Allineare il comportamento di `/modules/{name}` al README e ai profili (troncamento a 4000 caratteri o blocco) quando `ALLOW_MODULE_DUMP=false`, includendo un marcatore esplicito per i contenuti parziali.【1411c6†L1-L67】【2130a0†L10-L14】
- Considerare un header o campo JSON nei dump troncati per indicare size originale e percentuale servita, migliorando la UX rispetto all’attuale mancanza di segnali (vedi anche altri report sui moduli).【1411c6†L1-L67】 

## Fix necessari (puntuali)
- **Endpoint download moduli**: applicare la logica di troncamento/403 anche ai moduli `.txt` quando `ALLOW_MODULE_DUMP=false`, coerentemente con README e indicazioni di `base_profile.txt`/`meta_doc`. Esempio: limitare la risposta a 4000 caratteri con suffisso `[contenuto troncato]` per `archivist.txt`.【1411c6†L1-L67】【2130a0†L10-L14】【F:src/modules/base_profile.txt†L356-L366】

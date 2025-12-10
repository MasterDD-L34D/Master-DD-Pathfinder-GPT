# Verifica API e analisi modulo `tavern_hub.json`

## Ambiente di test
- Server FastAPI locale avviato con `uvicorn src.app:app --port 8000 --reload`, variabili `API_KEY=testing`, `ALLOW_ANONYMOUS=false`.
- Run 1: `ALLOW_MODULE_DUMP=true` per verificare elenco, metadati, download completo e 404.
- Run 2: `ALLOW_MODULE_DUMP=false` per verificare blocco/troncamento asset non testuali.

## Esiti API
1. `GET /health` → `200 OK`, stato `ok`; directory `modules` e `data` raggiungibili.【31f235†L1-L8】
2. `GET /modules` (`ALLOW_MODULE_DUMP=true`) → `200 OK`; elenco di 14 asset incluso `tavern_hub.json` (740 B, `.json`).【b0c8a7†L1-L12】
3. `GET /modules/tavern_hub.json/meta` → `200 OK`; `{name:"tavern_hub.json", size_bytes:740, suffix:".json"}`.【e86fef†L1-L8】
4. `GET /modules/tavern_hub.json` (`ALLOW_MODULE_DUMP=true`) → `200 OK`; dump completo dello stato persistente (feature flags, router, liste vuote, ledger con `sell_rate` 0.5, contatori).【a92a13†L1-L45】
5. `GET /modules/not_exists.json` → `404 Not Found`, body `{ "detail": "Module not found" }`.【94c18a†L1-L8】
6. `GET /modules/tavern_hub.json` (`ALLOW_MODULE_DUMP=false`) → `403 Forbidden`; download asset non testuale bloccato (nessun troncamento parziale).【3bedc0†L1-L8】

## Metadati, scopo e principi
- Nome modulo: `tavern_hub.json`, versione **1.0**, aggiornato **2025-08-23**, core **3.3**; raccoglie stato Hub con flag PFS/ABP/EitR, router, run quiz, personaggi, build, incontri, ledger, export e log di handoff.【F:src/modules/tavern_hub.json†L1-L44】
- Integrazione dichiarata dal modulo Taverna: ledger storage punta a `src/modules/tavern_hub.json` con schema di riferimento `adventurer_ledger.txt` e rate limit 8 op/min; il modulo serve da storage condiviso per Hub/ledger.【F:src/modules/Taverna_NPC.txt†L382-L386】
- Principi operativi (Knowledge Pack): snapshot prima di export e default `sell_rate` 0.5 su ledger; salvataggi includono flag regolistici e collezioni Hub (quiz/personaggi/build/incontri/export/id_counter/notes).【F:src/modules/knowledge_pack.md†L111-L113】

## Modello dati (state)
- `meta`: versioning + core compatibility.
- `feature_flags`: `pfs/abp/eitr` booleani default `false`.
- `router.last_mode`: tracking modalità recente.
- Collezioni vuote per `quiz_runs`, `characters`, `builds`, `encounters`, `vtt_exports`, `snapshots`, `hooks`, `handoff_log`, `notes`.
- `ledger`: valuta, inventario, `policies` (`sell_rate` 0.5, `encumbrance_variant` nullo), `wbl_target_level`, `audit` log.
- `id_counter`: contatori per `character`, `build`, `encounter`, `ledger_tx` (tutti a 1).【F:src/modules/tavern_hub.json†L1-L44】

## Comandi principali e flusso (Taverna)
- **Setup/storage**: `/save_hub`, `/load_hub`, `/reset_hub`, `/storage_clean` richiedono `hub_board==on`, validano schema minimo e usano cartella quarantena su errori; rate limit 8 op/min.【F:src/modules/Taverna_NPC.txt†L1225-L1247】
- **Ambiente/obiettivi**: `/tavern_status` riassume conteggi Hub (NPC/Quest/Rumor/Bounty/Fazioni/Shops/Eventi).【F:src/modules/Taverna_NPC.txt†L1133-L1147】
- **Nemici/bilanciamento**: `/quest_board`, `/quest_seed`, `/adventure_outline`, `/bounty_board` generano outline e hook verso Encounter/Loot; `/events` gestisce calendario con ID/timebox.【F:src/modules/Taverna_NPC.txt†L1149-L1212】
- **Simulazione/pacing/loot**: `/shop_setup` costruisce inventari WBL-linked; `/events_weekly_digest` e `/map_tavern` forniscono digest/mappa; `/downtime_jobs` genera payout downtime.【F:src/modules/Taverna_NPC.txt†L1175-L1256】
- **QA/export**: `/export_tavern` produce report Hub; export vincolati dai gate QA “export bloccato se QA FAIL” (sezione checklist).【F:src/modules/Taverna_NPC.txt†L1221-L1231】【F:src/modules/Taverna_NPC.txt†L794-L802】
- **Narrazione/lifecycle**: `/play_game`, `/tavern_event`, `/npc_boon`, `/chase_start`, `/hazard`, `/gamble` instradano verso GameMode e mini-giochi, aggiornando hub/router e CTA in stile CTA guard.【F:src/modules/Taverna_NPC.txt†L1268-L1306】
- **Auto-invocazioni/output**: onboarding/traits applicano `/update_build` e `/bench -q` automaticamente; `/events schedule` genera ID timestamp e output di conferma.【F:src/modules/Taverna_NPC.txt†L494-L505】【F:src/modules/Taverna_NPC.txt†L1184-L1198】

## Flow guidato, CTA e template
- Flow Onboarding GameMode con prompt sequenziali lingua→universo→ritratto→traits, con CTA a `/next` e azioni auto su build/bench; mantiene diario e richiami ai moduli Build/MinMax/Encounter.【F:src/modules/Taverna_NPC.txt†L400-L514】
- CTA salvataggio: `/check_conversation` suggerisce salvataggi/chiusura sessione quando sono presenti elementi pendenti (NPC/HUB/export).【F:src/modules/Taverna_NPC.txt†L1257-L1259】
- Export/report: `/export_tavern` e `/adventure_outline` danno CTA verso export o outline con tag emoji per stato.【F:src/modules/Taverna_NPC.txt†L1158-L1162】【F:src/modules/Taverna_NPC.txt†L1221-L1224】

## QA templates e helper
- Gate QA: sezione “QA Checklists / Digests / Usage” nota blocco export su FAIL e report sintetico `QA=OK | Canvas=OK | MinMax=OK | Ledger=OK | Hub=ON/OFF`.【F:src/modules/Taverna_NPC.txt†L789-L802】
- Errori/risoluzioni storage: `hub_storage.validation.on_error.quarantine_dir` sposta file invalidi in `src/modules/quarantine/`; helper `storage_clean` rigenera stub minimi secondo `schema_min`.【F:src/modules/Taverna_NPC.txt†L1225-L1247】【F:src/modules/quarantine/README.md†L1-L4】
- Formule/metriche: `events schedule` genera ID `EV-YYYYMMDD-HHMMSS`; `ledger_storage` applica rate limit 8 op/min; `auto_name_policy` per NPC usa pattern `NPC-YYYYMMDD-HHMM` con sanitize regex.【F:src/modules/Taverna_NPC.txt†L374-L386】【F:src/modules/Taverna_NPC.txt†L1187-L1198】【F:src/modules/Taverna_NPC.txt†L374-L379】
- Export filename/JSON: Hub e NPC salvano in `src/modules/taverna_saves/` con naming automatico; ledger export fa riferimento a `tavern_hub.json` e `adventurer_ledger.txt` per schema.【F:src/modules/Taverna_NPC.txt†L365-L386】【F:src/modules/taverna_saves/README.md†L1-L3】
- Tagging MDA/MDA gates: QA digest riporta `MDA=PASS`/`CHECK` come parte del monitoraggio Hub/Canvas/MinMax/Leaderboard.【F:src/modules/Taverna_NPC.txt†L789-L802】

## Osservazioni
- L’Hub aggrega quest/rumor/bounty/eventi con flow GameMode, CTA di salvataggio e export, mantenendo storage con rate limit/quarantena e integrazioni con Encounter/Ledger per outline e inventari WBL.【F:src/modules/Taverna_NPC.txt†L1133-L1256】【F:src/modules/Taverna_NPC.txt†L365-L386】【F:src/modules/Taverna_NPC.txt†L789-L802】

## Errori
- Nessun errore aperto: con `ALLOW_MODULE_DUMP=false` gli asset JSON vengono bloccati via `403` come da policy, mentre gli export hub ereditano ora marker di troncamento e logging gate quando necessario.【3bedc0†L1-L8】【F:src/modules/Taverna_NPC.txt†L1285-L1310】

## Miglioramenti suggeriti
- Nessuno: i gate QA di `/export_tavern`/`/adventure_outline` bloccono su QA fail con CTA univoca verso `/save_hub` o `/check_conversation`, e lo storage hub/ledger è validato con `schema_min` e quarantena attiva.【F:src/modules/Taverna_NPC.txt†L1285-L1317】【F:src/modules/Taverna_NPC.txt†L1225-L1247】

## Fix necessari
- Nessuno: le CTA export sono allineate alla policy e allo stato dei gate QA.

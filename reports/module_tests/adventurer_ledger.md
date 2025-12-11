# Verifica API e analisi modulo `adventurer_ledger.txt`

## Ambiente di test
- Server locale avviato con `uvicorn src.app:app --port 8000 --reload` e flag `ALLOW_ANONYMOUS=true` per i test di elenco e metadati; riavviato con `ALLOW_MODULE_DUMP=false` per verificare il blocco degli asset non testuali e dei `.txt` del ledger.【ebbacc†L1-L7】【873ec7†L1-L5】

## Esiti API
1. `GET /health` → `200 OK`, stato `ok`, directories `modules` e `data` raggiungibili.【8c75ea†L1-L8】
2. `GET /modules` → `200 OK` con elenco che include `adventurer_ledger.txt` (size 78578, `.txt`).【0c43f4†L1-L12】
3. `GET /modules/adventurer_ledger.txt/meta` → `200 OK`, metadati `{name, size_bytes, suffix}` coerenti.【a6fe46†L1-L7】
4. `GET /modules/adventurer_ledger.txt` con `ALLOW_MODULE_DUMP=false` → `403 Forbidden`, download del ledger bloccato come per gli asset non testuali.【fd69a0†L1-L41】
5. `GET /modules/nonexistent.txt` → `404 Not Found` con body `{"detail":"Module not found"}`.【339dff†L1-L7】
6. `GET /modules/tavern_hub.json` con `ALLOW_MODULE_DUMP=false` → `403 Forbidden`, download asset non testuale bloccato.【0e8b5a†L1-L7】

## Metadati, scopo e principi
- Nome: **Libro Mastro dell’Avventuriero**, versione **1.5**, tipo `economy/loot/crafting`, erede di `base_profile.txt`; export dichiarati: `ledger:api`, `qa:pfs_flags`, `pg_binding`, `vtt_json`.【F:src/modules/adventurer_ledger.txt†L1-L14】
- Scopo: gestione economica/loot/WBL/PFS/MIC con integrazione scheda PG/MinMax e stile giocatore; descrizione sintetica in linea con questi obiettivi.【F:src/modules/adventurer_ledger.txt†L15-L27】
- Principi: solo RAW Paizo, marcatura fonti RAW/PFS/HR/META, gate QA su Δ WBL rispetto a tolleranza, filtri/badge PFS, trasparenza con seed/ledger, blocchi MIC obbligatori, badge origine kernel.【F:src/modules/adventurer_ledger.txt†L47-L55】

## Modello dati
- `loot_state` include contesto (CR/mode/seed/player_style/crafter), valuta, profilo WBL e delta, pack tesoro, inventario, policy snapshot, ledger e consigli (buylist/gaps/big_six_score).【F:src/modules/adventurer_ledger.txt†L140-L175】
- Tipi principali: `Item`/`MagicItem` con campi di legalità e badge, `Art`/`Gem` per loot, `BuyAdvice` con craft e priorità.【F:src/modules/adventurer_ledger.txt†L176-L187】

## Policy e PFS
- Stato policy iniziale: `pfs_active:false`, `sell_rate:0.5`, `wbl_tolerance_pct:20`, rounding e toni MIC configurabili; welcome suggerisce setup rapido coerente (sell_rate 0.5, vendor cap 2000, tolerance 10%).【F:src/modules/adventurer_ledger.txt†L59-L68】【F:src/modules/adventurer_ledger.txt†L29-L45】
- Helpers PFS: `enrich_badges` applica `PFS:ILLEGAL` sugli item non legali quando il filtro è attivo; craft estimator rende `craft_can_make` falso se `pfs_legal` è `False` con filtro attivo.【F:src/modules/adventurer_ledger.txt†L440-L457】
- Toggle: `/toggle_pfs` aggiorna policy e stato con messaggio di applicazione filtri.【F:src/modules/adventurer_ledger.txt†L873-L882】

## Template ledger e WBL
- `loot_card_compact` e `loot_ledger_md` mostrano riepilogo monete/WBL/Big Six, ultima pack e ledger con Δ%.【F:src/modules/adventurer_ledger.txt†L686-L710】
- Card WBL compatta (`wbl_card_md`) riporta stato LOW/OK/HIGH e raccomandazione in funzione di `validate_wbl_gap`.【F:src/modules/adventurer_ledger.txt†L742-L748】

## Comandi principali e flusso
- Setup: `/set_wbl_profile`, `/set_wbl_target`, `/set_policies`, `/set_player_style`, `/set_settlement` configurano profili, tolleranze e vendor cap, con snapshot policy e messaggi di conferma.【F:src/modules/adventurer_ledger.txt†L809-L897】
- Ambiente/loot: `/roll_loot` genera pack (coins/goods/mundane/magic) con badge PFS, aggiorna ledger, valuta WBL e Big Six; `/shop_list` costruisce buylist priorizzata e marcata.【F:src/modules/adventurer_ledger.txt†L898-L920】【F:src/modules/adventurer_ledger.txt†L5-L21】【F:src/modules/adventurer_ledger.txt†L18-L24】
- Crafting/bilanciamento: `/craft_estimator`, `/craft_bulk_estimator`, `/craft_formula`, `/price_compare`, `/set_crafter_feats` stimano costi/tempi RAW-safe e applicano flag legali.【F:src/modules/adventurer_ledger.txt†L986-L1037】【F:src/modules/adventurer_ledger.txt†L430-L470】
- Simulazione/monetica: `/buy`, `/sell`, `/remove_item`, `/merge_loot`, `/import_loot`, `/normalize_coins` gestiscono inventario/ledger con controlli vendor cap, rounding e aggiornamento Big Six/WBL.【F:src/modules/adventurer_ledger.txt†L1320-L1670】
- Pacing/loot/export: `/export_loot`, `/export_pack`, `/export_slots`, `/export_pg_sheet(_json)`, `/export_vtt` producono MD/JSON/VTT; `/save_loot`/`/load_loot`/`/list_loot` serializzano lo stato.【F:src/modules/adventurer_ledger.txt†L1055-L1189】【F:src/modules/adventurer_ledger.txt†L1219-L1295】
- QA/monitor: `/audit_wbl`, `/validate_wbl_gap`, `/wbl_check_card`, `/qa_suite` forniscono gate export, badge su Δ WBL, heuristics su rounding/vendor cap/sorgenti e suggerimenti CTA.【F:src/modules/adventurer_ledger.txt†L1189-L1258】【F:src/modules/adventurer_ledger.txt†L1672-L1733】
- Narrazione/lifecycle: `/help` offre CTA globale; alias `/loot_help`, `/loot_export_vtt`, `/loot_toggle_pfs` evitano conflitti; integrazioni router/minmax/encounter suggeriscono trigger e campi esposti.【F:src/modules/adventurer_ledger.txt†L755-L787】【F:src/modules/adventurer_ledger.txt†L1320-L1336】【F:src/modules/adventurer_ledger.txt†L1749-L1759】

## Flow guidato, CTA e template
- Welcome guida al setup in 5 passi (policies, player_style, profilo WBL, roll loot, export) e richiama `/help`.【F:src/modules/adventurer_ledger.txt†L29-L45】
- Output checklist richiede header con policies correnti, marcatura fonti/badge, unità esplicite, QA rapido e CTA `/export_pg_sheet_json`; `cta_guard` impone una CTA utile dopo ogni azione.【F:src/modules/adventurer_ledger.txt†L1760-L1772】
- Template UI: ledger/buylist/slot/pg_sheet/WBL card offrono presentazioni Markdown pronte per export e VTT.【F:src/modules/adventurer_ledger.txt†L686-L750】

## QA templates, helper e formule
- `qa_suite` verifica gate WBL, vendor cap, normalizzazione valuta, gap Big Six, craft singolo/bulk, flag PFS, presenza charges/badge, rounding policy, heuristic fonti, binding PG ed export gate, restituendo elenco PASS/WARN/FAIL con CTA finale.【F:src/modules/adventurer_ledger.txt†L1672-L1733】
- Helper chiave: `round_gp` per arrotondamenti (nearest/floor), `vendor_cap_for_settlement` per cap da insediamento, `lookup_treasure_profile` e generatori coins/goods/mundane/magic per ondate loot, `enrich_badges`/`enrich_collection_badges` per tagging legale, `craft_estimator`/`craft_estimator_bulk` per formule costi/tempi e requisiti feat.【F:src/modules/adventurer_ledger.txt†L192-L236】【F:src/modules/adventurer_ledger.txt†L213-L218】【F:src/modules/adventurer_ledger.txt†L214-L236】【F:src/modules/adventurer_ledger.txt†L440-L470】
- Export filename/JSON: `/export_pg_sheet_json` e `/export_vtt` serializzano currency/inventory/ledger/WBL; binding PG condiviso con `minmax_builder` e `pg_binding` export dichiarato.【F:src/modules/adventurer_ledger.txt†L1219-L1246】【F:src/modules/adventurer_ledger.txt†L11-L14】【F:src/modules/adventurer_ledger.txt†L1754-L1759】

## Osservazioni
- Il welcome e il flow guidato coprono cinque passi (policy, stile giocatore, profilo WBL, roll loot, export) con CTA e template Markdown/VTT per ledger, buylist e scheda PG pronti all’uso.【F:src/modules/adventurer_ledger.txt†L29-L45】【F:src/modules/adventurer_ledger.txt†L686-L750】【F:src/modules/adventurer_ledger.txt†L1760-L1772】

## Errori
- Nessuno: il blocco del download in modalità `ALLOW_MODULE_DUMP=false` si applica ora anche al ledger testuale.【fd69a0†L1-L41】

## Miglioramenti suggeriti
- Nessuno: il `cta_guard` mantiene una CTA sintetica nelle call principali e `vendor_cap_gp` ora parte da default 2000 gp con QA che segnala WARN solo se configurato a `null`.【F:src/modules/adventurer_ledger.txt†L29-L68】【F:src/modules/adventurer_ledger.txt†L1672-L1693】

## Fix necessari
- Nessuno: la coerenza PFS è mantenuta perché `/buy` preserva `pfs_legal` sugli item importati e `enrich_badges` aggiunge badge `PFS:ILLEGAL` quando `policies.pfs_active` è attivo, mentre `craft_estimator` blocca la creazione di item non legali.【F:src/modules/adventurer_ledger.txt†L415-L470】【F:src/modules/adventurer_ledger.txt†L1389-L1435】
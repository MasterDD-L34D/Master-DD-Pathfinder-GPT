## Ambiente di test
- Client locale con `TestClient` FastAPI e flag `ALLOW_ANONYMOUS=true` per interrogare direttamente `src.app`; secondo run con `ALLOW_MODULE_DUMP=false` per verificare il troncamento dei moduli.【1cc753†L1-L7】【02412a†L1-L1】

## Esiti API
1. **`GET /health`** → `200 ok` con diagnostica dir pronta.【1cc753†L1-L1】【F:src/app.py†L213-L219】
2. **`GET /modules`** → elenco (14 file) include `minmax_builder.txt`.【1cc753†L2-L2】 
3. **`GET /modules/minmax_builder.txt/meta`** → `200` con `name/size_bytes/suffix`.【1cc753†L3-L3】【F:src/app.py†L339-L352】
4. **`GET /modules/minmax_builder.txt`** con dump abilitato → `200`, testo completo (~82k caratteri).【1cc753†L4-L4】【F:src/app.py†L572-L588】
5. **`GET /modules/minmax_builder.txt`** con `ALLOW_MODULE_DUMP=false` → `200`, contenuto troncato con suffisso `[contenuto troncato]` (≈4k caratteri).【02412a†L1-L1】【430a71†L3-L3】【F:src/app.py†L589-L600】
6. **`GET /modules/unknown.txt`** → `404 Module not found`.【1cc753†L5-L5】【F:src/app.py†L572-L577】
7. **`GET /modules/minmax_builder.txt?stub=true&class=Fighter&race=Elf&archetype=Lore Warden`** → stub `extended` con `step_total=16`, `benchmark.meta_tier=T3`.【1cc753†L6-L6】【F:src/app.py†L396-L523】
8. **`POST /modules/minmax_builder.txt?stub=true&class=Ranger&race=Human&archetype=Trapper` + body `{ "mode": "core", "hooks": ["hello"] }`** → stub `core` `step_total=8`, hook propagato in `export.sheet_payload`.【1cc753†L7-L7】【F:src/app.py†L396-L521】

- Copertura API completa: health/modules/meta/download (dump on/off), 404 per asset mancanti e percorsi stub `stub=true`/`mode=stub` validati sia in GET che in POST.【1cc753†L6-L7】【02412a†L1-L1】

## Metadati / Scopo
- Nome/versione/tipo: **MinMax Builder v5** (`type: minmax`), file binding `src/modules/minmax_builder.txt`.【F:src/modules/minmax_builder.txt†L1-L6】
- Principi & policy: priorità RAW→RAI→PFS, blocco HR/META in PFS, citazioni obbligatorie, flusso vincolato Setup→Export.【F:src/modules/minmax_builder.txt†L41-L60】
- Trigger/Router: attiva su richieste di ottimizzazione (DPR/benchmark/minmax) con CTA automatiche; suggerimenti per snapshot DPR, action plan e build alternativa.【F:src/modules/minmax_builder.txt†L21-L37】
- Meta-reference: banner META e livelli di autorevolezza (RAW_CANON→HR) con sorgenti ufficiali e community.【F:src/modules/minmax_builder.txt†L61-L99】

## Modello dati
- `build_state` iniziale: identificativi (nome/ruolo/classe/razza), regole (PFS/ABP/EitR), anagrafica, psico/legami, statistiche base (For 16, Des 14, Cos 14...), salvezze, derived (AC, speed, attacks, skills), magia, equipaggiamento, progressione, fonti/meta, flag QA e struttura benchmark (`statistiche_chiave`, `benchmark_comparison`) pronta per essere popolata dai comandi di simulazione.【F:src/modules/minmax_builder.txt†L117-L143】【F:src/modules/minmax_builder.txt†L716-L820】
- Flow labels per CTA: core 8 step, extended 16; sincronizzati con `step_labels` e `step_total` nel runtime dello stub e nel flusso interattivo.【F:src/app.py†L412-L446】【F:src/modules/minmax_builder.txt†L1860-L1936】

## Comandi principali (azioni/effect)
- **Setup/ambiente**: `/start_build` normalizza `mode` e resetta `build_state` con stats default; `/toggle_rules` applica PFS/ABP/EitR e stampa la Build Card; `/set_player_style` incluso nel help rapido.【F:src/modules/minmax_builder.txt†L708-L822】【F:src/modules/minmax_builder.txt†L930-L960】
- **Obiettivi & profilo**: `/update_build` aggiorna ruolo/classi/razza/stats/background/fonti, ricalcola iniziativa/CA e lancia benchmark quick; `/add_level` aggiunge livelli/talenti e aggiorna sinergie/benchmark.【F:src/modules/minmax_builder.txt†L960-L1030】
- **Nemici/bilanciamento & simulazione**: benchmark/simulazione attivati da `/bench`, `/run_benchmark`, `/simulate_build` e `auto` nello step 7 (benchmark) con exit checks `validate_core_ok/feats_ok/simulate_ok`.【F:src/modules/minmax_builder.txt†L1869-L1935】
- **Pacing/loot & economia**: `/set_currency`, `/set_inventory_weight`, ledger stub incluso nell’export per tracciare movimenti e valute.【F:src/modules/minmax_builder.txt†L1556-L1584】【F:src/app.py†L526-L541】
- **QA/export**: `/qa_check` popola flag `sources_ok/pfs_ok/hr_flagged` e blocca export se fallisce; `/export_build` e `/export_vtt` protetti da `qa_templates.gates.export_requires` con fallback `@export_blocked`.【F:src/modules/minmax_builder.txt†L1040-L1087】【F:src/modules/minmax_builder.txt†L1995-L2017】
- **Narrazione/lifecycle**: `/fork_build`, `/rollback_phase`, `/report_summary`, CTA finali su step 15-16 per report/chiusura, e companion import da modulo narrativo.【F:src/modules/minmax_builder.txt†L1088-L1157】【F:src/modules/minmax_builder.txt†L1943-L1994】【F:src/modules/minmax_builder.txt†L1658-L1676】

## Flow guidato / CTA e template UI/narrativi
- Flow core (8) e extended (16) con CTA primarie per avanzare/benchmark/export; step 7 auto-esegue `/run_benchmark`, step 8 auto-esegue `/qa_check`, step 10-12 richiedono gate QA per export/comparativa.【F:src/modules/minmax_builder.txt†L1860-L1936】
- UI templates: Build Card compatta/estesa, export VTT JSON, con badge fonti meta e toggles PFS/ABP/EitR; integrano progressione livelli, stats e benchmark per CTA narrative.【F:src/modules/minmax_builder.txt†L2212-L2245】

## QA templates e helper
- Error keys (`invalid_class`, `invalid_race`, `archetype_stack`, `feats_invalid`, `export_blocked`) più retry policy; gate `export_requires` impone core/feats/simulate OK + fonti e conformità PFS prima dell’export. 【F:src/modules/minmax_builder.txt†L1995-L2017】
- Helper: validatori stub per classi/razze/feat/companion/archetype stack e cross-validate, abilitazione MDA multi-pass e visual mapping del flow (mappe ASCII).【F:src/modules/minmax_builder.txt†L2021-L2186】【F:src/modules/minmax_builder.txt†L2034-L2043】
- Formula/Badge: meta tags (Nova/BFC/CR ecc.) e glossario DPR/ABP/EitR/RAI; export filename/JSON tramite template `export_build`/`vtt_export_json`.【F:src/modules/minmax_builder.txt†L2187-L2245】

## Osservazioni
- Lo stub builder è validato contro schema `build_core`/`build_extended`; in caso di errore restituisce `500 Stub payload non valido ...` (testato in commit precedente, logica stabile).【F:src/app.py†L556-L570】
- Il troncamento con `ALLOW_MODULE_DUMP=false` applica `[contenuto troncato]` ai moduli testuali, coerente con handler streaming; utile per review di sicurezza senza esporre l’intero asset.【02412a†L1-L1】【430a71†L3-L3】【F:src/app.py†L589-L600】

## Errori
- Nessun errore bloccante emerso nei test API e negli stub di build.【1cc753†L6-L7】

## Miglioramenti suggeriti
- Nessuno aperto: le CTA di export riportano ora il nome file previsto (`MinMax_<nome>.pdf/.xlsx/.json`) allineato con la nomenclatura condivisa di Encounter_Designer, riducendo gli equivoci sull’output.【F:src/modules/minmax_builder.txt†L940-L943】【F:src/modules/minmax_builder.txt†L1070-L1088】

## Note di verifica
- ✅ L’help rapido ora include i gate QA (`export_requires`) e il naming atteso dei file (`MinMax_<nome>.pdf/.xlsx/.json`), riducendo i tentativi di export falliti: non risultano più fix aperti su questo punto.【F:src/modules/minmax_builder.txt†L930-L960】【F:src/modules/minmax_builder.txt†L1995-L2017】

## Fix necessari
- Nessuno: export e gate QA (`export_requires`) risultano già documentati con naming condiviso `MinMax_<nome>.*`, senza ulteriori azioni aperte.【F:src/modules/minmax_builder.txt†L930-L960】【F:src/modules/minmax_builder.txt†L1995-L2017】

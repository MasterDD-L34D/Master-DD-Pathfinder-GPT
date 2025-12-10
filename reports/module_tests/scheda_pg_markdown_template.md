# Verifica API e analisi del modulo `scheda_pg_markdown_template.md`

## Ambiente di test
- **Run 1 (dump abilitato):** `ALLOW_ANONYMOUS=true` con `TestClient` su `src.app` per `/health`, `/modules`, `/modules/<file>/meta`, download completo e stub `?stub=true`.【bff25f†L1-L6】
- **Run 2 (dump disabilitato):** `ALLOW_ANONYMOUS=true ALLOW_MODULE_DUMP=false` per verificare troncamento e marker finale.【300994†L1-L4】

## Esiti API
1. `GET /health` → `200 OK` con directory ok.【bff25f†L1-L1】
2. `GET /modules` → `200 OK`, 14 asset.【bff25f†L2-L2】
3. `GET /modules/scheda_pg_markdown_template.md/meta` → `200 OK`, `{name,size_bytes,suffix}` coerenti (23497 B, `.md`).【bff25f†L3-L3】
4. `GET /modules/scheda_pg_markdown_template.md` → `200 OK`, `content-type: text/markdown`, 23.3k char; stub `?stub=true` restituisce 200.【bff25f†L4-L5】
5. `ALLOW_MODULE_DUMP=false` produce `200` con 4k char, header preservato e suffisso `[contenuto troncato]`.【300994†L1-L4】
6. `GET /modules/missing_file.md` → `404 Module not found` su nome errato.【bff25f†L6-L6】

## Metadati / Scopo
- Template markdown PF1e con macro di setup (print mode, toggle MINMAX/VTT/QA/EXPLAIN/LEDGER, separatore decimale, fallback descrizioni) e helper per mod, firma, badge.【F:src/modules/scheda_pg_markdown_template.md†L5-L33】
- Header anagrafico con classi/archetipi, allineamento/divinità, ruolo consigliato e stile interpretativo; include background breve e indicatori opzionali su taglia/età ecc.【F:src/modules/scheda_pg_markdown_template.md†L95-L111】
- Scopo dichiarato via toggle badges nel riepilogo rapido: mostra attivazione MINMAX/VTT/QA/EXPLAIN/LEDGER e flash economico/VTT/QA/Explain.【F:src/modules/scheda_pg_markdown_template.md†L115-L139】

## Modello dati / stato
- Statistiche base e breakdown CA/CMD, salvezze, iniziativa, velocità, XP e PF con calcolo macro `mod`, includendo CA touch/ff e CMD dettagliato.【F:src/modules/scheda_pg_markdown_template.md†L144-L162】
- Tabelle dinamiche per armi, manovre CMB, skills (gradi+mod+var+classe), risorse giornaliere, slot incantesimi e spell table opzionale.【F:src/modules/scheda_pg_markdown_template.md†L196-L307】
- Economia: conversioni valutarie (to_gp, coin_str, fmt_gp), ledger con liquidità/investimenti/WBL e badge nel sommario iniziale.【F:src/modules/scheda_pg_markdown_template.md†L24-L33】【F:src/modules/scheda_pg_markdown_template.md†L115-L135】【F:src/modules/scheda_pg_markdown_template.md†L355-L391】

## Macro / Comandi principali e impatto sullo stato
- **Setup/ambiente:** macro `PRINT_MODE`, `SHOW_*` e `DECIMAL_COMMA` controllano visibilità sezioni e formattazione numerica; macro `d`, `mod`, `toggle_badge` gestiscono fallback e badge.【F:src/modules/scheda_pg_markdown_template.md†L5-L23】
- **Obiettivi e benchmark (MinMax):** riepilogo DPR/CA e meta tier, breakdown PF/CA, benchmark comparativi e heatmap rischi; parametri BM/STK/ac_breakdown pilotano le tabelle.【F:src/modules/scheda_pg_markdown_template.md†L115-L185】【F:src/modules/scheda_pg_markdown_template.md†L442-L471】
- **Nemici/bilanciamento:** benchmark auto/manuale con Δ% e stato scaling/azioni/buff; risk heatmap su feat/spell per minacce ricorrenti.【F:src/modules/scheda_pg_markdown_template.md†L445-L471】
- **Simulazione/pacing/loot:** routine di round, risorse giornaliere con delta residuo, consumabili, e ledger con audit PFS, loot/crafting e KPI economici.【F:src/modules/scheda_pg_markdown_template.md†L288-L313】【F:src/modules/scheda_pg_markdown_template.md†L296-L307】【F:src/modules/scheda_pg_markdown_template.md†L355-L391】
- **QA/export:** badge QA nel riepilogo, checklist su tabelle popolate, valute normalizzate, coerenza WBL e tag lingua/PFS; CTA export VTT/ledger via `/export_pg_sheet(_json)` e JSON vtt_json/ledger.【F:src/modules/scheda_pg_markdown_template.md†L115-L136】【F:src/modules/scheda_pg_markdown_template.md†L475-L482】【F:src/modules/scheda_pg_markdown_template.md†L393-L403】
- **Narrazione/lifecycle:** explain multi-metodo (tldr, contesto, step-by-step, algoritmo, analogia, errori, RAW/RAI, quiz, fonti) e profilo ruolistico/canone per mantenere coerenza di personaggio e campagna.【F:src/modules/scheda_pg_markdown_template.md†L407-L439】【F:src/modules/scheda_pg_markdown_template.md†L492-L520】

## Flow guidato / CTA
- Riepilogo rapido con badge attivi guida l'utente su sezioni da riempire (MinMax, VTT, QA, Explain, Ledger) e mostra prompt “QA ready”/“Explain (tldr)”.【F:src/modules/scheda_pg_markdown_template.md†L115-L139】
- CTA export esplicite per scheda e JSON (ledger/vtt_json) e note localizzazione numerica per VTT; suggeriti percorsi Foundry/Roll20 nelle note GM.【F:src/modules/scheda_pg_markdown_template.md†L393-L403】
- Output checklist vincola la consegna finale a header con toggle attivi, tag RAW/PFS/HR/META e formattazione numerica coerente.【F:src/modules/scheda_pg_markdown_template.md†L485-L490】

## QA templates e helper
- **Gates:** tabelle armi/skill/incantesimi non vuote o placeholder, valute normalizzate con `fmt_gp`, Δ WBL loggato, badge lingua/PFS.【F:src/modules/scheda_pg_markdown_template.md†L475-L482】
- **Errori comuni:** sezione Explain prevede “Errori comuni (e come evitarli)” e RAW vs RAI per edge case, con quiz rapido e fonti citate.【F:src/modules/scheda_pg_markdown_template.md†L423-L439】
- **Formule chiave:** CA ricostruita (10 + mod), CMD base con scelta For/Des, conversioni valutarie `to_gp`/`fmt_gp`, benchmark Δ% e heatmap rischi.【F:src/modules/scheda_pg_markdown_template.md†L70-L160】【F:src/modules/scheda_pg_markdown_template.md†L24-L33】【F:src/modules/scheda_pg_markdown_template.md†L445-L471】
- **Export:** filename/JSON implicito via CTA `/export_pg_sheet` e `_json`, con sezioni ledger/vtt_json e tagging MDA/Foundry (map/token/grid/safe/bleed).【F:src/modules/scheda_pg_markdown_template.md†L355-L403】

## Osservazioni
- Il troncamento mantiene il titolo e il marker finale, utile per audit in ambienti con dump limitato; la lunghezza compatta (4k) preserva contesto iniziale.【300994†L1-L4】
- Mancano metadati espliciti su versione/compatibilità o policy di trigger; potrebbero essere esposti nel blocco meta iniziale insieme ai toggle per facilitare QA automatizzato.【F:src/modules/scheda_pg_markdown_template.md†L5-L23】

## Errori rilevati
- Nessun errore funzionale nelle API; 404 atteso su file mancante.【bff25f†L6-L6】

## Miglioramenti suggeriti / Fix necessari
- Aggiungere un campo “versione” e “compatibilità sistema” nel riepilogo iniziale o nel payload meta per allinearsi ad altri moduli e supportare QA catalogo.【F:src/modules/scheda_pg_markdown_template.md†L5-L23】
- Documentare nell'header i trigger/policy operative (es. quando abilitare Ledger/MinMax) per chiarezza d'uso nelle pipeline automatiche.【F:src/modules/scheda_pg_markdown_template.md†L115-L139】

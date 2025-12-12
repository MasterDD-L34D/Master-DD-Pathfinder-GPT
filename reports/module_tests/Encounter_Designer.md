# Verifica API e analisi modulo `Encounter_Designer.txt`

## Ambiente di test
- Server avviato con `uvicorn src.app:app --port 8000 --reload`.
- `ALLOW_ANONYMOUS=true` per le chiamate senza header.
- `ALLOW_MODULE_DUMP=true` (default) per scaricare il contenuto completo; riavvio con `ALLOW_MODULE_DUMP=false` per verificare il troncamento.

## Esiti API
1. **`GET /health`** — `200 OK`; stato `ok` e percorsi `modules`/`data` validi.
2. **`GET /modules`** — `200 OK`; elenco include `Encounter_Designer.txt`.
3. **`GET /modules/Encounter_Designer.txt/meta`** — `200 OK`; metadati `{ name: Encounter_Designer.txt, size_bytes: 34933, suffix: .txt }`.
4. **`GET /modules/Encounter_Designer.txt`** con `ALLOW_MODULE_DUMP=true` — `200 OK`; restituito il file completo.
5. **`GET /modules/DoesNotExist.txt`** — `404 Not Found` con body `{ "detail": "Module not found" }`.
6. **`GET /modules/Encounter_Designer.txt`** con `ALLOW_MODULE_DUMP=false` — `200 OK`; risposta troncata con marcatore finale `[contenuto troncato]`.

- Copertura API completata: health/modules/meta/download verificati con dump on/off, 404 su nomi errati e conferma della dimensione/metadati coerenti con il file su disco.【F:src/modules/Encounter_Designer.txt†L1-L60】

## Metadati e scopo del modulo
- `module_name`: **Encounter Designer**, versione **1.0**, ultimo aggiornamento **2025-08-21**, eredita da `base_profile.txt`. Descrive un designer di incontri PF1e con benchmark MinMax, export VTT e gating QA.【F:src/modules/Encounter_Designer.txt†L1-L60】
- Trigger supportati: `encounter`, `genera_incontro`, `bilancia_incontro`, `encounter designer`, `crea_nemici`. Messaggio di benvenuto dedicato con identità “Maestro di Guerra e Stratega Narrativo” e doppio tono tecnico/narrativo, attivabile via `/narrativo {on|off}`.【F:src/modules/Encounter_Designer.txt†L12-L29】
- Principi e policy: materiale Paizo PF1e, distinzione RAW/RAI/PFS/HR, ogni incontro deve fornire CR/XP/ruoli/terrains/loot; ruling prioritizza RAW→RAI→PFS→HR con gate PFS ed esclusione offline.【F:src/modules/Encounter_Designer.txt†L30-L39】
- Modalità operative (Encounter Builder, Auto Balance, Narrative Hook, Loot Generator, VTT Export, QA Ruling) e vincoli (export bloccato senza QA, gating PFS, difficoltà astratte).【F:src/modules/Encounter_Designer.txt†L40-L52】
- Integrazioni: MinMax builder, template scheda PG markdown, Ruling Expert, Explain Methods, Archivist per lore.【F:src/modules/Encounter_Designer.txt†L53-L60】

## Modello dati `encounter_state`
- Party: livello medio, taglia, hint di composizione e toggles di regola (PFS/ABP/EitR).【F:src/modules/Encounter_Designer.txt†L67-L75】
- Difficoltà e ambiente: target (Easy/Moderate/Challenging/Deadly), CR target, budget XP, biome/terrain/light/weather/space/hazard.【F:src/modules/Encounter_Designer.txt†L76-L86】
- Obiettivi: tipo, secondari, condizioni di vittoria/fallimento, timer in round.【F:src/modules/Encounter_Designer.txt†L87-L91】
- Nemici: ruolo, CR, quantità, allineamento, tipo, tag e riassunto statistico sintetico con tattiche, policy loot, badge ruling.【F:src/modules/Encounter_Designer.txt†L92-L116】
- Pacing e bilanciamento: waves, escalation, rest pressure, snapshot con xp_budget_est, cr_effective_est, etichette, heatmap rischi, DPR party/enemy e gap difensivi/mda tags.【F:src/modules/Encounter_Designer.txt†L117-L133】
- Loot/export/audit: hint GP, items, percorso bundle VTT, map hint, note GM, timestamps e decision log.【F:src/modules/Encounter_Designer.txt†L134-L145】

## Comandi principali
- **Setup e parametri**: `/start_encounter`, `/random_encounter`, `/set_party`, `/set_difficulty`, `/narrativo`, `/set_environment`, `/set_objectives` gestiscono identificativo, titolo, livello/taglia party, difficoltà, ambiente, obiettivi e toggle narrativo.【F:src/modules/Encounter_Designer.txt†L146-L247】
- **Nemici e bilanciamento**: `/add_enemy` aggiunge blocchi sintetici con badge normalizzati; `/auto_pick_enemies` genera nemici coerenti con bioma; `/auto_balance` calcola XP/CR e label; `/simulate_encounter` stima DPR/CA/DC e heatmap rischi; `/risk_heatmap_encounter` visualizza i rischi.【F:src/modules/Encounter_Designer.txt†L248-L356】
- **Economia/pacing/QA/export**: `/set_loot_policy`, `/set_pacing` gestiscono loot e ondate; `/validate_encounter` applica QA gates (badge, PFS gate, CR stimato); `/export_encounter` produce JSON/MD/PDF solo se QA OK.【F:src/modules/Encounter_Designer.txt†L357-L419】
- **Narrazione e lifecycle**: `/flavor_encounter`, `/add_wave`, `/save_encounter`, `/load_encounter`, `/fork_encounter` per flavor, ondate aggiuntive e persistenza; `/explain_rule` e `/ruling_check` delegano a explain/ruling modules.【F:src/modules/Encounter_Designer.txt†L420-L485】

## Dettaglio operativo dei comandi e CTA
- **Setup e toggles**: `/start_encounter` inizializza `encounter_state` con ID, titolo, livello/taglia, difficoltà e timestamp; `/set_party` e `/set_difficulty` aggiornano livello medio, size, toggles PFS/ABP/EitR e CR target; `/narrativo` aggiunge un flag alle note; `/random_encounter` imposta biome/difficoltà e auto-invoca `/auto_pick_enemies`, `/auto_balance`, `/simulate_encounter` prima dell’output riassuntivo.【F:src/modules/Encounter_Designer.txt†L146-L213】【F:src/modules/Encounter_Designer.txt†L165-L176】
- **Ambiente e obiettivi**: `/set_environment` scrive biome, luce, meteo, spazio, feature e hazard nell’oggetto `environment`; `/set_objectives` copre tipo/secondari, condizioni di vittoria/fallimento e timer, restituendo un riepilogo sintetico con emoji target.【F:src/modules/Encounter_Designer.txt†L214-L247】
- **Nemici e generazione**: `/add_enemy` appende blocchi con ruolo, CR, quantità, tipo/tag, statistiche sintetiche e badge normalizzato; `/auto_pick_enemies` genera una lista coerente con biome/difficoltà rispettando il gate PFS, la inserisce in `enemies` e notifica quanti elementi sono stati creati.【F:src/modules/Encounter_Designer.txt†L248-L299】
- **Bilanciamento e simulazione**: `/auto_balance` calcola XP target da livello/size/difficoltà, stima il CR effettivo dagli enemy e classifica le label, salvando tutto in `balance_snapshot` e annunciando XP/CR/etichette; `/simulate_encounter` ricava benchmark party/nemici (o da profilo MinMax), popola DPR, gap difensive, heatmap rischi e mda tags, e logga i rischi nel messaggio; `/risk_heatmap_encounter` mostra rapidamente le label di rischio correnti.【F:src/modules/Encounter_Designer.txt†L300-L356】
- **Pacing e loot**: `/set_loot_policy` registra budget GP e lista item; `/set_pacing` definisce ondate/escalation/pressione riposo con output sul conteggio waves; `/add_wave` permette aggiunte puntuali per round, appending nel pacing con conferma testuale.【F:src/modules/Encounter_Designer.txt†L357-L379】【F:src/modules/Encounter_Designer.txt†L420-L439】
- **QA e export**: `/validate_encounter` lancia `/auto_balance` se manca `cr_effective_est`, assegna badge/PFS gate, esegue `run_qagates` e marca `qa_ok`, restituendo checklist e stato QA; `/export_encounter` blocca se `qa_ok` è falso, altrimenti assegna filename, esporta JSON via `vtt_export_json` o card estesa (MD/PDF) e conferma il path bundle.【F:src/modules/Encounter_Designer.txt†L380-L419】
- **Persistenza e supporto**: `/flavor_encounter` richiama il template narrativo “locandiere”; `/save_encounter`, `/load_encounter`, `/fork_encounter` gestiscono storage in sessione, fallback “non trovato” e branch varianti; `/explain_rule` e `/ruling_check` emettono CTA per i moduli Explain/Ruling tramite template stub dedicati.【F:src/modules/Encounter_Designer.txt†L400-L485】
- **CTA e flow guidato**: i 6 step del flow (Setup→Ambiente/Obiettivi→Nemici→Bilanciamento→Pacing/Loot→QA/Export) includono CTA primarie e alternative (`/set_party`, `/set_environment`, `/auto_pick_enemies`, `/simulate_encounter`, `/set_pacing`, `/set_loot_policy`, `/export_encounter`) e auto-invocazioni su bilanciamento e QA al cambio step.【F:src/modules/Encounter_Designer.txt†L486-L523】

## Flow guidato e template UI
- Flow in 6 step (setup party, ambiente/obiettivi, aggiunta nemici, bilanciamento, pacing/loot, QA/export) con CTA predefinite e auto-invocazioni su bilanciamento/QA.【F:src/modules/Encounter_Designer.txt†L486-L523】
- Template: `explain_stub` e `ruling_stub` sono stub di inoltro per Explain/Ruling; `encounter_card_compact` e `encounter_card_extended` forniscono formati brevi ed estesi con sezioni party, difficoltà, obiettivi, nemici, pacing, bilanciamento, loot ed export.【F:src/modules/Encounter_Designer.txt†L524-L589】
- Narrazione: `flavor_locandiere` offre intro, tattiche e gancio “nova” in stile locandiere; `vtt_export_json` esporta snapshot strutturato per VTT/JSON.【F:src/modules/Encounter_Designer.txt†L590-L618】

## QA templates e helper
- **QA templates**: i gate coprono esistenza nemici, stima CR, badge e PFS ma ora includono anche pacing/loot e presenza di `balance_snapshot` (`enemies_exist`, `cr_estimated`, `balance_estimated`, `sources_tagged`, `pfs_gate_ok`, `pacing_defined`, `loot_resolved`); errori specifici guidano verso `/auto_balance` o `/simulate_encounter` se manca lo snapshot e verso `/set_pacing`/`/set_loot_policy` se i campi sono vuoti.【F:src/modules/Encounter_Designer.txt†L380-L404】
- **Badge, PFS e stato regole**: `rules_status_text` restituisce “PFS/ABP/EitR ON|OFF” concatenati; `normalize_ruling_badge` forza badge in un set chiuso e, con PFS attivo, rimpiazza ogni HR (`❗`) in `🧭 PFS` per non bloccare i gate; `enemies_badge_ok` verifica che ogni nemico esponga un badge, mentre `pfs_hr_gate` respinge qualsiasi nemico HR quando PFS è attivo.【F:src/modules/Encounter_Designer.txt†L651-L688】
- **Stime XP/CR e label**: `compute_xp_budget_estimate` calcola XP con formula `100 * livello * size * mult` dove `mult` varia per difficoltà (Easy 0.8, Moderate 1.0, Challenging 1.25, Deadly 1.6); `compute_effective_cr_from_enemies` clampa quantità e CR nei range [1,64]/[0,40] prima di pesare i duplicati e normalizzare per conteggio nemici, mentre `classify_balance_label` mappa CR_eff in Too Easy/Moderate/Challenging/Deadly o `unrated` se nullo.【F:src/modules/Encounter_Designer.txt†L690-L707】【F:src/modules/Encounter_Designer.txt†L777-L788】
- **Simulazione e rischi**: `estimate_party_benchmarks` produce DPR/CA/saves da profilo MinMax o livello medio (DPR 12/16 + 2×lvl, CA 16+lvl, saves 4+lvl//2); `estimate_enemy_benchmarks` deduce DPR/Atk/DC medi dal CR e quantità; `detect_risks` etichetta rischi se atk supera CA di ≥6, DPR t1-3 eccede di ≥10 o il gap saves vs DC è ≤-4 (alpha-strike, high-accuracy, save-or-suck).【F:src/modules/Encounter_Designer.txt†L710-L744】
- **Export, ondate e MDA**: `export_filename` sanifica il titolo (regex non alfanumerici → `_`, max 40 char) e aggiunge livello medio e timestamp UTC; `materialize_wave` clona nemici base secondo le addizioni per ondate; `map_mda_tags` trasforma hint di composizione in etichette Timmy/Johnny/Spike senza duplicati.【F:src/modules/Encounter_Designer.txt†L745-L798】
## Osservazioni
- ENC-OBS-01: modello dati e policy rimangono numerici/astratti senza testo protetto, con badge PFS/RAW che delimitano HR.【F:src/modules/Encounter_Designer.txt†L92-L140】
- ENC-OBS-02: pipeline e CTA guidate tracciate (setup → auto-bilanciamento → QA → export) con gate obbligatorio prima dell’export.【F:src/modules/Encounter_Designer.txt†L486-L523】【F:src/modules/Encounter_Designer.txt†L400-L419】【F:src/modules/Encounter_Designer.txt†L520-L528】
- ENC-ERR-01: helper clampato e QA rerun segnano “nessun errore bloccante” dopo l’allineamento CR/QA.【F:src/modules/Encounter_Designer.txt†L293-L314】【F:src/modules/Encounter_Designer.txt†L777-L788】

## Errori
- Nessun errore bloccante sul calcolo CR/QA dopo l’allineamento al singolo helper clampato.【F:src/modules/Encounter_Designer.txt†L293-L314】【F:src/modules/Encounter_Designer.txt†L777-L788】

## Miglioramenti suggeriti
- Nessun miglioramento aperto dopo l’estensione dei gate QA (pacing/loot/balance_snapshot) e dei messaggi di correzione verso i comandi di setup/bilanciamento.【F:src/modules/Encounter_Designer.txt†L380-L404】

## Fix necessari
- Nessuno: i gate QA coprono ora pacing, loot e snapshot di bilanciamento e bloccano l’export con CTA esplicite verso `/auto_balance`, `/simulate_encounter`, `/set_pacing` e `/set_loot_policy`.【F:src/modules/Encounter_Designer.txt†L380-L404】

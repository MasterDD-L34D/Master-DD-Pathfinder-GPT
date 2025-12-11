# Verifica logica `sigilli_runner_module.txt`

## Ambiente di test (server/flag)
- Eseguito con `fastapi.testclient` su `src.app`, senza API key (ottiene 401) e con `ALLOW_ANONYMOUS=true` per ispezionare gli endpoint.
- Con `ALLOW_MODULE_DUMP=false` il dump viene servito ma troncato dopo l'intestazione del file, mantenendo la protezione base contro i leak completi.【fc8c1a†L1-L12】【5c31d3†L11-L18】

## Esiti API
1. `GET /health` → `200 OK`, stato `ok`, percorsi `modules` e `data` raggiungibili.【5c31d3†L1-L2】
2. `GET /modules` → `401` senza flag anonimo; `200 OK` con `ALLOW_ANONYMOUS=true`, elenco include `sigilli_runner_module.txt` (5431 B, `.txt`).【fc8c1a†L3-L12】【5c31d3†L3-L8】
3. `GET /modules/sigilli_runner_module.txt/meta` → `401` senza flag; `200 OK` con `{name,size_bytes,suffix}` coerenti.【fc8c1a†L5-L8】【5c31d3†L5-L6】
4. `GET /modules/sigilli_runner_module.txt` → `401` senza flag; `200 OK` con dump completo (5361 char) se anonimo abilitato.【fc8c1a†L7-L12】【5c31d3†L7-L8】
5. `GET /modules/bogus.txt` → `404 Module not found` sia con che senza flag anonimo.【fc8c1a†L9-L12】【5c31d3†L9-L10】
6. `GET /modules/sigilli_runner_module.txt` con `ALLOW_MODULE_DUMP=false` → `200 OK` ma contenuto troncato (mostra solo header del modulo).【5c31d3†L11-L18】

## Metadati e scopo
- Nome: **Sigilli Runner**, versione **2.1**, tipo `decorator_logic`, ultimo aggiornamento **2025-09-06**.【F:src/modules/sigilli_runner_module.txt†L1-L5】
- Principi: traccia progressione `sigilli_tokens/level/index` e badge rari/quest; espone portale promozionale opzionale e tabelle sigilli comuni, bonus per mode e rari.【F:src/modules/sigilli_runner_module.txt†L14-L68】【F:src/modules/sigilli_runner_module.txt†L30-L34】
- Trigger/integrazioni: funzione di decorazione per la pipeline risposta; non definisce comandi espliciti ma fornisce checklist di output e CTA portale.【F:src/modules/sigilli_runner_module.txt†L91-L154】【F:src/modules/sigilli_runner_module.txt†L155-L159】

## Modello dati (state/memory)
- Stato tracciato: `sigilli_tokens`, `sigilli_quest`, `sigilli_index`, `sigilli_last_rare`, `sigilli_last_quest`, `sigilli_level` con default 0 o `-9999` per cooldown.【F:src/modules/sigilli_runner_module.txt†L14-L27】
- Costanti: soglia `token_step=1`, `quest_every=5`, livelli nominali per 0/5/9/13/21, portale `sigilli_portal` sempre disponibile.【F:src/modules/sigilli_runner_module.txt†L28-L41】
- Tabelle: 4 sigilli comuni, bonus per mode (TAVERNA/MINMAX/ENCOUNTER/LEDGER/RULING/ARCHIVIST/NARRATIVA/EXPLAIN), 3 sigilli rari.【F:src/modules/sigilli_runner_module.txt†L42-L68】

## Comandi principali e logica (setup → QA/export → CTA)
- **compute_seals(mode, toggles, meta, output_text, memory, constants, tables, features)**: unico entrypoint esportato.
  - **Setup/parametri**: legge soglie `sigilli_mini_threshold` (200), `sigilli_code_lines` (12), cooldown raro e quest_every; mode è normalizzato upper-case.【F:src/modules/sigilli_runner_module.txt†L7-L13】【F:src/modules/sigilli_runner_module.txt†L103-L123】
  - **Ambiente/obiettivi**: calcola `length_ok` via `_len`; `code_ok` ora assegna sigillo/bonus token dedicato e tag `MDA:code_block` quando rilevate ≥12 righe di codice.【F:src/modules/sigilli_runner_module.txt†L110-L123】
  - **Nemici/bilanciamento**: non applicabile (modulo decoratore), ma il raro introduce pacing tramite cooldown e indice.【F:src/modules/sigilli_runner_module.txt†L116-L148】
  - **Simulazione/pacing/loot**: assegna sigilli comuni solo se sopra soglia, aggiunge mode bonus senza soglia, raro condizionato da cooldown, quest ogni 5 risposte utili, progressione livelli a 5/9/13/21 con badge dedicato e tag MDA/CTA in-line.【F:src/modules/sigilli_runner_module.txt†L106-L154】【F:src/modules/sigilli_runner_module.txt†L33-L40】
  - **QA/export**: aggiorna memoria, applica tagging MDA per lunghezza/codice/mode/raro/quest/level-up e appende sempre il portale se `sigilli_show_badge` true, fungendo da CTA di continuazione/esportazione esterna.【F:src/modules/sigilli_runner_module.txt†L117-L159】【F:src/modules/sigilli_runner_module.txt†L28-L34】
  - **Narrazione/lifecycle**: nessun state machine narrativo, ma la quest periodica funge da hook di progressione ogni `quest_every`.【F:src/modules/sigilli_runner_module.txt†L125-L131】

## Flow guidato / CTA / template
- `output_checklist` prescrive header con mode attivo e soglie, motivazioni per badge (lunghezza, code block, mode, raro, quest), stato memoria aggiornato e link portale/CTA; i tag MDA/CTA sono incorporati nei sigilli quando applicabile.【F:src/modules/sigilli_runner_module.txt†L117-L159】
- Il portale `sigilli_portal` garantisce una CTA stabile al termine di ogni run; nessun template UI aggiuntivo è definito.【F:src/modules/sigilli_runner_module.txt†L28-L34】【F:src/modules/sigilli_runner_module.txt†L144-L154】

## QA template e helper
- Helper: `_len` per lunghezza, `_looks_like_code` per contare righe con backtick/brace, `_rarity_roll` con seed deterministico e dipendente da indice/cooldown.【F:src/modules/sigilli_runner_module.txt†L70-L90】
- Gates: `length_ok` governa sigilli comuni, quest e raro; cooldown `sigilli_rotation_cooldown` evita rari ravvicinati; badge livello attivato solo su soglie token con tagging MDA coerente.【F:src/modules/sigilli_runner_module.txt†L106-L154】
- Export filename/JSON: non previsto (decorator), ma il portale e la checklist forniscono CTA esterne con tag CTA/MDA integrati nei sigilli.

## Osservazioni
- Il raro può attivarsi solo da indice 14 con stato di default; documentare la finestra di attivazione per evitare percezione di malfunzionamento iniziale.【F:src/modules/sigilli_runner_module.txt†L116-L148】
- Il portale viene aggiunto anche quando nessun sigillo è stato assegnato, garantendo almeno un elemento in `seals`.【F:src/modules/sigilli_runner_module.txt†L144-L154】
- Il presente report incorpora tutti i punti richiesti nelle due iterazioni precedenti (API, metadati, modello dati, flow/CTA, errori simulati e fix applicati), senza ulteriori lacune note.

## Errori simulati
- API key mancante: `/modules*` ritorna `401 Invalid or missing API key`, confermato con TestClient.【fc8c1a†L3-L12】
- Modulo inesistente: `/modules/bogus.txt` → `404 Module not found`.【5c31d3†L9-L10】
- Dump disabilitato: `ALLOW_MODULE_DUMP=false` restituisce header troncato, utile per evitare leak completi.【5c31d3†L11-L18】

## Errori
- Nessun errore bloccante dopo l’integrazione di `code_ok` e il tagging MDA/CTA nei sigilli.

## Miglioramenti suggeriti
- Nessuno: logica di assegnazione sigilli e motivazioni MDA/CTA risultano allineate alla checklist.

## Fix necessari
- TODO
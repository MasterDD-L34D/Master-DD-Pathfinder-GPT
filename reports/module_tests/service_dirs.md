# Verifica directory di servizio Taverna/HUB

## Copertura
- `src/modules/quarantine`
- `src/data/modules/quarantine`
- `src/modules/taverna_saves`

## Ambiente di test
- Server locale avviato con `uvicorn src.app:app --host 0.0.0.0 --port 8000`.
- API key: `testkey`. Flag verificati: `ALLOW_MODULE_DUMP=true` (default) e `ALLOW_MODULE_DUMP=false` per testare il troncamento dell'output.【F:reports/module_tests/Taverna_NPC.md†L3-L15】

## Esiti chiamate API
- `GET /health`: `200`, directory `modules` e `data` ok, nessun obbligatorio mancante.【F:reports/module_tests/Taverna_NPC.md†L7-L13】
- `GET /modules`: elenco include `Taverna_NPC.txt` (118875 byte, `.txt`).【F:reports/module_tests/Taverna_NPC.md†L7-L13】
- `GET /modules/Taverna_NPC.txt/meta`: `200`, dimensione 118875, suffisso `.txt`.【F:reports/module_tests/Taverna_NPC.md†L7-L13】
- `GET /modules/Taverna_NPC.txt` con dump abilitato: download completo con `content-length` 118875.【F:reports/module_tests/Taverna_NPC.md†L7-L13】
- `GET /modules/does_not_exist.txt`: `404` con `{"detail":"Module not found"}`.【F:reports/module_tests/Taverna_NPC.md†L11-L13】
- `GET /modules/taverna_saves`: `404`, directory non esposta (atteso).【F:reports/module_tests/Taverna_NPC.md†L11-L13】
- `GET /modules/Taverna_NPC.txt` con `ALLOW_MODULE_DUMP=false`: risposta `200` con contenuto troncato e suffisso `[contenuto troncato]`.【F:reports/module_tests/Taverna_NPC.md†L11-L15】

## Metadati e scopo del modulo Taverna
- Nome: "Taverna NPC", versione 3.5, ultima modifica 2025-09-04, tipo `module`.【F:src/modules/Taverna_NPC.txt†L1-L4】
- Descrizione/scopo: hub per PG/PNG, gestione taverna e Solo RPG; integra MinMax Builder, Ruling Expert, Explain, Archivist e Adventurer Ledger; export Markdown/PDF/Canvas.【F:src/modules/Taverna_NPC.txt†L6-L13】
- Principi/constraint: solo materiale Paizo PF1e, nomenclatura meccanica inglese, badge trasparenza RAW/RAI/PFS/HR, checklist QA obbligatoria, blocco Echo <8.5/10, salvataggi solo su conferma, nessuna immagine AI senza stile dichiarato.【F:src/modules/Taverna_NPC.txt†L31-L51】
- Trigger di ingresso: bacheca missioni, nuova missione, voci di taverna, taglie/fazioni/negozio, estrazione personaggi, quiz professionale/ruolo, Solo RPG.【F:src/modules/Taverna_NPC.txt†L14-L29】
- Policy di integrazione/handoff: badge e prompt per handoff con Archivist, suggerimenti per passaggi rapidi tra modalità.【F:src/modules/Taverna_NPC.txt†L310-L320】

## Modello dati e storage
- Entità principali: NPC, QUEST, RUMOR, BOUNTY, FACTION, SHOP, EVENT, LEDGER con campi esplicitati (id, ruoli/CR, ricompense, reputazione, ecc.).【F:src/modules/Taverna_NPC.txt†L331-L339】
- Stato `tavern_state`: liste per ogni entità, `map_ascii`, oggetto `quiz` (stage/picks/BKT/SJT/axes_scores/asked/suggested) con default definiti.【F:src/modules/Taverna_NPC.txt†L341-L363】
- Storage NPC: percorso `src/modules/taverna_saves/`, naming `{name}.json`, schema minimo (identity, statblock, feats/spells/equipment, notes), auto_name con pattern `NPC-YYYYMMDD-HHMM`, sanitize regex, limite 200 file con `delete_oldest`.【F:src/modules/Taverna_NPC.txt†L364-L380】
- Ledger storage: `src/modules/tavern_hub.json`, schema di riferimento `src/modules/adventurer_ledger.txt`, rate limit 8 ops/min (`E-RATE-LIMIT`).【F:src/modules/Taverna_NPC.txt†L382-L386】
- Directory `taverna_saves` contiene solo `README.md` che chiarisce creazione automatica dei backup JSON; nessuna fixture necessaria.【F:src/modules/taverna_saves/README.md†L1-L3】
- Directory `quarantine` e mirror `data/modules/quarantine` contengono solo i rispettivi README e richiedono revisione manuale dei file non validati; nessun caricamento automatico runtime.【F:src/modules/quarantine/README.md†L1-L4】【F:src/data/modules/quarantine/README.md†L1-L4】

## Comandi principali (parametri, effetti sullo stato, auto-invocazioni)
- `/status`: restituisce lo stato runtime/flag via `status.output`. Nessuna modifica allo state.【F:src/modules/Taverna_NPC.txt†L780-L784】
- `/self_check`: calcola QA rapido (canvas/minmax/ledger/hub) e abilita/disabilita feature flag di conseguenza; output sintetico QA/Canvas/MinMax/Ledger/Hub.【F:src/modules/Taverna_NPC.txt†L785-L793】
- `/echo <on|off>`: aggiorna `feature_flags.echo_gate`, controllando il gate di grading Echo.【F:src/modules/Taverna_NPC.txt†L794-L799】
- `/portrait_validate`: valida il prompt immagine tramite `Echo.portrait_validate`, aggiornando `current_npc.image_prompt` o segnalando errori.【F:src/modules/Taverna_NPC.txt†L800-L814】
- `/grade`: invoca `Echo.grade` sull'NPC corrente e ultimo testo, producendo quality report e fix rapidi.【F:src/modules/Taverna_NPC.txt†L815-L827】
- `/quiz_start` (alias `/npc_quiz_start`): inizializza quiz MaxDiff→Pairwise→SJT, prepara strutture `tavern_state.quiz` e mostra card UI.【F:src/modules/Taverna_NPC.txt†L828-L850】
- `/quiz_bestworst`: registra risposte MaxDiff, aggiorna `axes_scores` con `Quiz.maxdiff_score`, sceglie il prossimo set.【F:src/modules/Taverna_NPC.txt†L859-L873】
- `/quiz_pair`: aggiorna Bradley–Terry via `Quiz.btl_update`, traccia coppie chieste, decide passaggio a SJT.【F:src/modules/Taverna_NPC.txt†L888-L915】
- `/quiz_sjt`: applica mapping SJT, fonde assi, aggiorna suggerimenti e auto-invoca `/quiz_finalize` su early-stop.【F:src/modules/Taverna_NPC.txt†L916-L947】
- `/quiz_finalize`: sintetizza ruolo/classi suggerite, opzionale Echo grade, porta a stato SYNTHESIS.【F:src/modules/Taverna_NPC.txt†L953-L974】
- `/npc_auto <role> <level>`: genera PNG coerente via `Synthesis.build_npc_from_role`, applica Echo gate con micro-refine se score < soglia, aggiorna `current_npc` e stato READY.【F:src/modules/Taverna_NPC.txt†L975-L1001】
- `/generate_npc`, `/npc_quick`, `/npc_compact`, `/npc_review` e altri comandi di simulazione/bench/pacing/loot/QA/export/narrazione seguono lo stesso schema consolidato (validatori, chiamate helper, output card) nel blocco `commands`.【F:src/modules/Taverna_NPC.txt†L1003-L1038】【F:src/modules/Taverna_NPC.txt†L760-L771】

## Flow guidato, CTA e template UI/narrativi
- Header di conferma con speed/output/PFS/ABP/EitR per ogni attivazione.【F:src/modules/Taverna_NPC.txt†L282-L285】
- Onboarding guidato GameMode: sequenza lang → universe → gender/age → nome → ritratto → background/traits/items, con prompt/parse/guards e auto-comandi `/update_build` + `/bench`.【F:src/modules/Taverna_NPC.txt†L428-L518】
- Quiz UI: template `ui_templates_quiz_pro` per carte MaxDiff, Pairwise, SJT e status/result; CTA per avanzamento e early-stop.【F:src/modules/Taverna_NPC.txt†L828-L965】

## QA templates e helper
- Echo guard: punteggio minimo 8.5, auto_refine opzionale, blocco export/risposte se sotto soglia.【F:src/modules/Taverna_NPC.txt†L279-L305】【F:src/modules/Taverna_NPC.txt†L975-L999】
- Self-check QA su canvas/minmax/ledger/hub con output sintetico; disabilitazioni automatiche se asset mancanti.【F:src/modules/Taverna_NPC.txt†L785-L793】【F:src/modules/Taverna_NPC.txt†L66-L120】
- Gate immagini: `image_guardrails` con contenuti vietati, sanitizer e strategie di softening.【F:src/modules/Taverna_NPC.txt†L246-L263】
- Formule chiave: rate limit ledger 8 ops/min (`E-RATE-LIMIT`), cap 200 file su `taverna_saves`, pattern naming e sanitize per export JSON; badge RAW/RAI/PFS/HR richiesti nei risultati.【F:src/modules/Taverna_NPC.txt†L364-L380】【F:src/modules/Taverna_NPC.txt†L382-L386】【F:src/modules/Taverna_NPC.txt†L40-L45】
- Export filename/JSON: `taverna_saves` per NPC/quest/rumor/ledger con naming automatico; ledger export fa riferimento a `tavern_hub.json` e schema `adventurer_ledger.txt`.【F:src/modules/Taverna_NPC.txt†L364-L386】【F:src/modules/taverna_saves/README.md†L1-L3】

## Osservazioni, errori e miglioramenti
- ✅ API core rispondono correttamente; `taverna_saves` non esposto (scelta di sicurezza).【F:reports/module_tests/Taverna_NPC.md†L7-L13】
- ⚠️ Con `ALLOW_MODULE_DUMP=false` il contenuto è troncato senza indicare dimensione residua; suggerito header/note che l'output è parziale.【F:reports/module_tests/Taverna_NPC.md†L11-L15】
- ⚠️ `curl | head` con dump abilitato può fallire in locale per errore di scrittura ma il server fornisce `content-length`; nessuna azione lato server.【F:reports/module_tests/Taverna_NPC.md†L11-L13】
- 🔧 Esporre endpoint sui metadati di storage (quota residua, `max_files`) basato su `storage.auto_name_policy` aiuterebbe il monitoraggio della saturazione.【F:src/modules/Taverna_NPC.txt†L364-L380】
- 🔧 Aggiungere messaggi guida quando Echo gate blocca (<8.5) o quando il self-check segnala QA="CHECK" per chiarire i passi di remediation.【F:src/modules/Taverna_NPC.txt†L279-L305】【F:src/modules/Taverna_NPC.txt†L785-L793】

# Test e analisi del modulo Taverna_NPC

## Ambiente di test
- Server locale avviato con `uvicorn src.app:app --host 0.0.0.0 --port 8000`.
- API key: `testkey`. Flag testati: `ALLOW_MODULE_DUMP=true` (default) e `ALLOW_MODULE_DUMP=false` per verificare troncamento.

## Esiti chiamate API
- `GET /health`: `200`, directory `modules` e `data` ok, nessun obbligatorio mancante. 【671fb7†L1-L9】
- `GET /modules`: elenco include `Taverna_NPC.txt` (118875 byte, `.txt`). 【dbe5f4†L1-L12】
- `GET /modules/Taverna_NPC.txt/meta`: `200`, dimensione 118875, suffisso `.txt`. 【eb0cdb†L1-L8】
- `GET /modules/Taverna_NPC.txt` con dump abilitato: download completo (content-length 118875) e disposition di attachment. 【b21fe7†L3-L14】
- `GET /modules/does_not_exist.txt`: `404` con `{"detail":"Module not found"}`. 【7de665†L1-L8】
- `GET /modules/taverna_saves`: `404`, directory non esposta come modulo. 【e01c22†L1-L8】
- `GET /modules/Taverna_NPC.txt` con `ALLOW_MODULE_DUMP=false`: risposta `200` ma contenuto limitato con suffisso `[contenuto troncato]` e trasferimento chunked. 【f250d4†L1-L76】

## Metadati e scopo
- Nome: "Taverna NPC", versione 3.5, ultima modifica 2025-09-04, tipo `module`. 【F:src/modules/Taverna_NPC.txt†L1-L4】
- Descrizione: hub per PG/PNG, gestione taverna e Solo RPG, integra MinMax Builder, Ruling Expert, Explain e Adventurer Ledger; export Markdown/PDF/Canvas. 【F:src/modules/Taverna_NPC.txt†L6-L10】
- Trigger d’ingresso (esempi: bacheca missioni, nuova missione, voci di taverna, quiz professionale/ruolo). 【F:src/modules/Taverna_NPC.txt†L14-L28】
- Principi/constraint: solo materiale Paizo PF1e, nomi meccanici in inglese, badge trasparenza, checklist QA prima di export, blocco Echo <8.5/10, no export senza PASS, salvataggi su conferma, niente immagini AI senza stile. 【F:src/modules/Taverna_NPC.txt†L33-L51】
- Integrazioni dichiarate: MinMax Builder, Ruling Expert, Explain, Archivist, Adventurer Ledger. 【F:src/modules/Taverna_NPC.txt†L6-L13】

## Modello dati
- Entità principali: NPC, QUEST, RUMOR, BOUNTY, FACTION, SHOP, EVENT, LEDGER con campi specificati (id, ruoli, CR, rewards, reputazione, ecc.). 【F:src/modules/Taverna_NPC.txt†L331-L340】
- Stato taverna: liste per ogni entità, mappa ASCII, quiz object con stage/picks/BKT/SJT, default map e quiz. 【F:src/modules/Taverna_NPC.txt†L341-L363】
- Storage: percorso `src/modules/taverna_saves/`, naming `{name}.json`, schema minimo (identity, statblock, feats/spells/equipment, notes), policy di auto-name/limit 200 file con delete_oldest. 【F:src/modules/Taverna_NPC.txt†L364-L380】
- Ledger storage: `src/modules/tavern_hub.json`, schema di riferimento `src/modules/adventurer_ledger.txt`, rate limit 8 ops/min (E-RATE-LIMIT). 【F:src/modules/Taverna_NPC.txt†L382-L386】
- Directory `taverna_saves` contiene solo `README.md` e spiega che i backup JSON vengono creati automaticamente; nessuna fixture necessaria. 【F:src/modules/taverna_saves/README.md†L1-L3】

## Comandi principali (parametri, effetti, auto-invocazioni)
- `/status`: restituisce stato runtime/flag via output da `status.output`. 【F:src/modules/Taverna_NPC.txt†L780-L784】
- `/self_check`: verifica canvas/minmax/ledger/hub, calcola QA="OK"/"CHECK" con disabilitazioni condizionali. 【F:src/modules/Taverna_NPC.txt†L785-L793】
- `/echo <on|off>`: abilita/disabilita gate Echo aggiornando `feature_flags.echo_gate`. 【F:src/modules/Taverna_NPC.txt†L794-L799】
- `/portrait_validate`: valida prompt ritratto tramite `Echo.portrait_validate`, aggiorna `current_npc.image_prompt` o emette errore. 【F:src/modules/Taverna_NPC.txt†L800-L814】
- `/grade`: chiama `Echo.grade` su NPC e ultimo testo, produce report con score e fix rapidi. 【F:src/modules/Taverna_NPC.txt†L815-L827】
- `/quiz_start` e alias `/npc_quiz_start`: inizializzano quiz (MaxDiff→Pairwise→SJT), selezione item via `Quiz.select_next_cat_item`, output card UI. 【F:src/modules/Taverna_NPC.txt†L828-L850】
- `/quiz_bestworst`: registra risposte MaxDiff, aggiorna axes_scores con `Quiz.maxdiff_score`, avanza a pairwise quando supera soglia. 【F:src/modules/Taverna_NPC.txt†L859-L887】
- `/quiz_pair`: aggiorna Bradley–Terry con `Quiz.btl_update`, traccia coppie chieste, passa a SJT dopo round minimi. 【F:src/modules/Taverna_NPC.txt†L888-L915】
- `/quiz_sjt`: registra scelta vignetta, fonde mapping con `Mapping.apply_sjt` e `Mapping.suggest_role_classes`, trigger di early-stop/`/quiz_finalize`. 【F:src/modules/Taverna_NPC.txt†L916-L947】
- `/quiz_finalize`: sintetizza ruolo/classi suggerite, optional Echo grading, passa a stato SYNTHESIS. 【F:src/modules/Taverna_NPC.txt†L953-L974】
- `/npc_auto <role> <level>`: genera PNG via `Synthesis.build_npc_from_role`, valida ruolo/livello, passa Echo gate con micro-refine se score basso, mostra card compatta. 【F:src/modules/Taverna_NPC.txt†L975-L1000】
- Runtime/GameMode: onboarding con scelta lingua/universo/genere/ritratto, allocazione punti manuale/random con guard ≤18 e auto-comandi `/update_build` + `/bench`, diary append; loop Solo con prove d20/CTT, applicazione meccaniche, currency update. 【F:src/modules/Taverna_NPC.txt†L400-L772】

## Flow guidato, CTA e template
- Header di conferma include speed/output/PFS/ABP/EitR. 【F:src/modules/Taverna_NPC.txt†L282-L285】
- Onboarding CTA sequenziali (lang → universe → gender/age → nome → ritratto → background/traits → items) con prompt e azioni esplicite. 【F:src/modules/Taverna_NPC.txt†L428-L518】
- Quiz UI: usa template `ui_templates_quiz_pro` per carte MaxDiff, Pairwise, SJT e status/result. 【F:src/modules/Taverna_NPC.txt†L838-L965】

## QA templates, helper e formule
- Echo guard: punteggio minimo 8.5, auto_refine opzionale, blocco export/risposte se score < soglia, con remediation esplicita (/grade→fix→/refine_npc) prima di salvare o esportare in `taverna_saves`. 【F:src/modules/Taverna_NPC.txt†L279-L305】【F:src/modules/Taverna_NPC.txt†L996-L1008】
- Self-check QA su canvas/minmax/ledger/hub. 【F:src/modules/Taverna_NPC.txt†L785-L793】
- Export/outline e CTA di sblocco: se QA="CHECK" (Canvas/Ledger) o dump disabilitato, l’export viene bloccato con reminder di salvataggio/reallineamento e remediation tramite `/self_check` e rerun di Echo finché il gate non blocca più. 【F:src/modules/Taverna_NPC.txt†L1194-L1208】
- Gates su immagini: `image_guardrails` con disallowed content e sanitizer (reject/soften). 【F:src/modules/Taverna_NPC.txt†L246-L263】
- Rate limit ledger: 8 ops/min con errore `E-RATE-LIMIT`. 【F:src/modules/Taverna_NPC.txt†L382-L386】
- Tagging MDA/Badge trasparenza: badge RAW/RAI/PFS/HR richiesti. 【F:src/modules/Taverna_NPC.txt†L40-L45】
- Export/knowledge packs: disabilitazioni automatiche se asset mancanti; guidance per riattivare. 【F:src/modules/Taverna_NPC.txt†L66-L206】

## Osservazioni
- Il flusso guidato accompagna l’utente da onboarding lingua/universo/ritratto alle fasi di quiz e generazione PNG, con CTA e template UI dedicati per ogni step.【F:src/modules/Taverna_NPC.txt†L282-L518】【F:src/modules/Taverna_NPC.txt†L838-L974】

## Errori
- ✅ API core rispondono correttamente; `taverna_saves` non esposto (atteso per sicurezza). 【e01c22†L1-L8】
- ⚠️ `curl | head` con dump abilitato ritorna errore di write locale, ma il server fornisce `content-length`; nessuna azione necessaria lato server. 【b21fe7†L3-L16】

## Miglioramenti suggeriti
- Nessuno: lo storage espone `/storage_meta` con quota residua, pattern di auto-name e marker di troncamento quando `ALLOW_MODULE_DUMP=false`; i gate Echo/QA includono CTA di remediation (ripeti `/grade` o `/self_check` e disattiva Echo in sandbox) prima di sbloccare salvataggi/export.【F:src/modules/Taverna_NPC.txt†L364-L386】【F:src/modules/Taverna_NPC.txt†L996-L1008】【F:src/modules/Taverna_NPC.txt†L1194-L1208】

## Fix necessari
- Nessuno: lo storage espone già `/storage_meta` con quota/pattern di auto-name e, con `ALLOW_MODULE_DUMP=false`, i dump vengono tronchi a 4k con marker `[…TRUNCATED ALLOW_MODULE_DUMP=false…]` e risposta standard “⚠️ Output parziale” anche per export plain/markdown, in linea con le policy dichiarate.【F:src/modules/Taverna_NPC.txt†L364-L386】【F:src/modules/Taverna_NPC.txt†L273-L305】【F:src/modules/Taverna_NPC.txt†L1285-L1317】

## Esiti API
- Coperti gli endpoint principali con dump attivo/disattivo: health/modules/meta/download restituiscono i 200 attesi, gli asset inesistenti danno 404 e il troncamento applica marker espliciti quando `ALLOW_MODULE_DUMP=false`.【671fb7†L1-L9】【f250d4†L1-L76】
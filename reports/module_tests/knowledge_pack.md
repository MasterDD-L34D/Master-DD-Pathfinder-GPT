# Verifica API e analisi completa del modulo `knowledge_pack.md`

## Ambiente di test
- **Run 1 (dump completo):** `env ALLOW_ANONYMOUS=true uvicorn src.app:app --port 8000` su FastAPI locale, endpoint accessibili senza `x-api-key`.
- **Run 2 (dump disabilitato):** `env ALLOW_ANONYMOUS=true ALLOW_MODULE_DUMP=false uvicorn src.app:app --port 8000` per verificare troncamento e gestione errori.

## Esiti API
1. **Salute** — `GET /health` → `200 OK`; directory `src/modules` e `src/data` presenti e senza file richiesti mancanti.【9dc6d0†L1-L4】
2. **Elenco moduli** — `GET /modules` → `200 OK`; 14 asset, incluso `knowledge_pack.md` (12.306 B, `.md`).【d2aa3f†L1-L8】
3. **Metadati modulo** — `GET /modules/knowledge_pack.md/meta` → `200 OK`; payload `{name,size_bytes,suffix}` coerente con l’elenco.【741354†L1-L2】
4. **Download completo** — `GET /modules/knowledge_pack.md` (dump abilitato) → `200 OK`; intestazione `content-type: text/markdown` e corpo testuale completo (non troncato).【d4822a†L2-L7】
5. **Download troncato** — `GET /modules/knowledge_pack.md` con `ALLOW_MODULE_DUMP=false` → `200 OK`; contenuto monco con marker finale `[contenuto troncato]`.【7645d7†L1-L8】
6. **Errore nome errato** — `GET /modules/nonexistent.md` → `404 Not Found` con risposta JSON minima.【bd3d02†L1-L6】
7. **Visibilità knowledge base** — `GET /knowledge` → `200 OK`; 7 asset (4 PDF, 3 JSON) mostrati con dimensioni e suffissi.【81a2a8†L1-L5】
8. **Metadati asset knowledge** — `GET /knowledge/Items%20Master%20List.pdf/meta` → `200 OK`; 256.148 B, suffisso `.pdf`.【e6a24f†L1-L2】

## Metadati e scopo del modulo
- **Identità:** Knowledge Pack v2 (2025-09-04), compatibilità Core 3.3+, badge [RAW][RAI][PFS] 🧠 META [HR].【F:src/modules/knowledge_pack.md†L1-L6】
- **Scopo:** guida d’uso del kernel con flusso di recupero (`GET /modules/{name}` con `x-api-key`), prompt rapidi e indice delle modalità principali.【F:src/modules/knowledge_pack.md†L45-L66】
- **Trigger/ingaggio:** decide la modalità, poi richiama il modulo relativo via API prima di rispondere; mantenere i badge coerenti per ogni blocco.【F:src/modules/knowledge_pack.md†L45-L52】【F:src/modules/knowledge_pack.md†L126-L142】
- **Policy/integrazioni:** percorso unificato `.txt` post-migrazione; badge per separare RAW/RAI/PFS/HR e modalità META; riferimento a risorse locali in `src/data` per materiali di supporto.【F:src/modules/knowledge_pack.md†L3-L21】

## Modello dati / stato
- **Persistenza suggerita (tavern_hub.json):** `feature_flags` (pfs/abp/eitr), `quiz_runs`, `characters`, `builds`, `encounters`, `ledger` (currency, inventory, policies, wbl_target_level, audit), `vtt_exports`, `snapshots`, `id_counter`, `notes`; default `sell_rate` 0.5.【F:src/modules/knowledge_pack.md†L111-L113】

## Comandi principali e impatto sullo stato
- **Taverna NPC:** quiz 3×(7–10 domande) → scheda `.md` con psicologia/backstory/ruolo; CTA `/next_step` passa il contesto a MinMax.【F:src/modules/knowledge_pack.md†L69-L73】
- **MinMax Builder v5:** pipeline `/start_build → /set_player_style <Timmy|Johnny|Spike> → /toggle_pfs on/off → /next_step → /bench -q` più comandi di aggiornamento livelli/spell/export; muta flag PFS/ABP/EitR e arricchisce `builds`/`benchmark` nello stato.【F:src/modules/knowledge_pack.md†L74-L75】【F:src/modules/knowledge_pack.md†L96-L100】
- **Ruling Expert:** input domanda + PFS toggle → output strutturato TL;DR → RAW → RAI → PFS → Fonti (separa legalità e fonti).【F:src/modules/knowledge_pack.md†L77-L78】【F:src/modules/knowledge_pack.md†L96-L100】
- **Encounter Designer:** parametri APL, bioma, nemici, difficoltà, PFS, obiettivi → produce CR/XP, tattiche, morale, varianti ±1 CR, loot PFS-safe; CTA `/send_to_ledger` per sincronizzare ricompense con il ledger.【F:src/modules/knowledge_pack.md†L80-L83】【F:src/modules/knowledge_pack.md†L143-L147】
- **Libro Mastro:** gestisce cassa/inventario/parcels/WBL audit; comandi `/recalc_wbl`, `/shopping_hint <focus>`, `/export_ledger`; aggiorna `ledger` e controlla sell_rate default.【F:src/modules/knowledge_pack.md†L84-L86】【F:src/modules/knowledge_pack.md†L111-L113】【F:src/modules/knowledge_pack.md†L148-L151】
- **Archivist/Narrativa/Explain/Doc:** modalità di supporto per lore, scene narrative, spiegazioni didattiche (6 metodi) e documentazione; mantengono badge adeguati e non alterano lo stato salvo note/exports.【F:src/modules/knowledge_pack.md†L88-L92】【F:src/modules/knowledge_pack.md†L153-L155】

## Flow guidato / CTA e template UI
- Quick start suggerisce sequenze predefinite per creazione PG (quiz → scheda → `/next_step`) e ottimizzazione (MinMax → benchmark), con richiami espliciti a moduli e badge per ogni scena narrata nella demo end-to-end.【F:src/modules/knowledge_pack.md†L45-L52】【F:src/modules/knowledge_pack.md†L126-L156】
- Prompt “copia/incolla” per ogni modulo (Ruling, Archivist, Taverna, MinMax, Encounter, Ledger, Narrativa, Explain) forniscono template parametrizzati (input, badge, tono) e output atteso, utili per UI o CTA guidate.【F:src/modules/knowledge_pack.md†L159-L237】

## QA templates e helper
- Checklist generale e per modulo con gate espliciti su badge, fonti, struttura RAW/RAI/PFS, coerenza PFS, benchmark MinMax, tattiche e loot Encounter, audit WBL Ledger, completezza metodi Explain.【F:src/modules/knowledge_pack.md†L241-L279】
- Troubleshooting include correzioni rapide su nomi file, template scheda, toggle PFS e sigilli, evidenziando cause comuni di output errato.【F:src/modules/knowledge_pack.md†L117-L123】

## Osservazioni, errori e miglioramenti suggeriti
- **Troncamento chiaro:** con `ALLOW_MODULE_DUMP=false` il suffisso `[contenuto troncato]` rende evidente la risposta parziale; comportamento corretto e segnalato.【7645d7†L1-L8】
- **Allineamento estensioni:** il modulo ricorda la migrazione a `.txt` per tutti i percorsi; conviene verificare che eventuali client non referenzino più `.yaml`.【F:src/modules/knowledge_pack.md†L3-L4】
- **Miglioria potenziale:** includere nelle API di metadata un campo `version`/`compatibility` già presente nel testo per evitare parsing dal corpo del modulo.【F:src/modules/knowledge_pack.md†L1-L6】

# Guida di revisione report moduli

## Sequenza di lettura (copertura completa)
Procedi nell’ordine dell’indice moduli: Encounter_Designer → Taverna_NPC → adventurer_ledger → archivist → base_profile → explain_methods → knowledge_pack → meta_doc → minmax_builder → narrative_flow → ruling_expert → scheda_pg_markdown_template → sigilli_runner_module → tavern_hub, chiudendo con le cartelle di servizio. Questo assicura che tutti i 15 moduli del kernel e le directory di supporto siano coperti una sola volta.

Prima della revisione esegui `python tools/refresh_module_reports.py --write` per portare tutti i report in linea con la checklist: lo script legge la sequenza moduli direttamente da questa guida tramite `load_sequence_from_guide` (in `tools/generate_module_plan.py`), così l’ordine applicato ai file coincide con quello usato nella lettura.

## Metodo di analisi per ogni report
Apri il report corrispondente in `reports/module_tests/<nome>.md` e compila tutte le sottosezioni seguenti (il modello completo è già applicato al report di `base_profile` con riferimenti inline e la stessa sequenza di titoli):

- **Ambiente di test**: server, flag, variabili e qualsiasi setup speciale (es. ALLOW_MODULE_DUMP) attivo durante la prova.
- **Esiti API**: risultati per `/health`, `/modules`, `/modules/<file>/meta`, download completo, 404 su nome errato e comportamento con `ALLOW_MODULE_DUMP=false` (troncamento atteso).
- **Metadati/Scopo**: nome e versione del modulo, principi/trigger/policy, integrazioni previste.
- **Dipendenze esterne**: moduli/API/asset usati (es. MinMax, Taverna, storage), con indicazione della fonte e citazioni alle sezioni che li dichiarano.
- **Modello dati**: campi principali dello state e loro ruolo.
- **Comandi principali**: per setup, ambiente/obiettivi, nemici/bilanciamento, simulazione, pacing/loot, QA/export, narrazione/lifecycle. Indica parametri, effetti sullo stato, auto-invocazioni e output.
- **Flow guidato/CTA**: template UI e narrativi, con eventuali call-to-action per l’utente.
- **QA templates e helper**: gates, errori, resolution tips, formule chiave (XP/CR, rischi, badge/PFS), export filename/JSON, ondate, tagging MDA.
- **Osservazioni / Errori / Miglioramenti / Fix necessari**: elenca problemi e suggerimenti. Ogni item deve puntare alle linee di sorgente coinvolte usando citazioni `【F:percorso†Lx-Ly】` e indicare priorità (“P1” bug/ambiguità funzionali, “P2” QA/completezza, “P3” UX/copy). Converte subito gli errori e i fix in task con scope e file precisi.

### Controlli PF1e (CR/XP, PFS e stacking)
- Verifica per ogni comando e tabella: budget CR/XP coerente con il contesto del modulo, stacking dei bonus e prerequisiti delle scelte (feat/archetipi/incantesimi) confrontando con i check `sanity_check` e `rules_consistency` della `qa_pipeline` in `src/modules/base_profile.txt`. Riporta nel report le linee che citano CR/XP o vincoli di stacking, es. `【F:src/modules/encounter_designer.txt†L120-L134】`, e a fianco scrivi l’esito sintetico (“OK: CR 5 con XP 1.600, stacking limitato a morale”).
- Se PFS è ON, passa esplicitamente dal gate di legalità (fonti consentite, cronache, boons, obedience) come nel check `pfs_gate`; se OFF, segnala comunque deviazioni PFS indicando la fonte violata. Marca le violazioni in “Errori/Fix necessari” come P1 con testo chiaro, es. `P1 – PFS: fonte non consentita (Inner Sea Magic) usata in feat X, sostituire con Advanced Player’s Guide`.
- Cita nel report le tre tappe QA (`sanity_check`, `rules_consistency`, `pfs_gate`) con esito OK/violazione accanto alla citazione di linea. Esempi di annotazione nella sezione QA: `- sanity_check: OK (CR/XP coerenti)`, `- pfs_gate: violazione fonte【F:src/modules/<nome>.txt†L45-L52】`.

### Sicurezza e osservability AI
- Controlla protezioni anti prompt injection, rispetto delle policy fonti e applicazione delle policy Echo/Sigilli e `image_policy`. Verifica che i comandi che producono output usino `qa_logging` e receipt con hash SHA256 come da blocchi `qa_logging`, `output_contract` e `interaction_protocol` di `src/modules/base_profile.txt`.
- Nel report, accanto al comando o alla policy citata, annota l’esito: es. `OK: qa_logging + receipt SHA256 sul comando export` oppure `Violazione: export loot senza receipt e senza nota su Echo/Sigilli【F:src/modules/<nome>.txt†L88-L99】`.
- In “Errori/Fix necessari” marca le violazioni come P1/P2 con suggerimento concreto, es. `P1 – Security: aggiungere receipt con hash per export loot; applicare Echo/Sigilli`. Riporta sempre la citazione di linea che mostra la mancanza.
- Se trovi protezioni già presenti (sanitizzazione input, guardrail prompt injection), cita le linee per dimostrare copertura completa e differenzia tra controlli già conformi e lacune.

Mantieni la checklist ordinata come sopra per tutti i moduli, riutilizzando il formato già mostrato in `base_profile` e aggiornando le priorità nel momento in cui emergono dai report.

## Output di pianificazione per ogni modulo
Crea un elenco conciso di task (idealmente 1–5 per modulo), ciascuno con: titolo, file/section, sintesi della modifica, blocking/priority e dipendenze da altri moduli.

Chiudi la revisione del modulo con uno status: “Pronto per sviluppo” se tutti i task sono noti e scoped; “In attesa” se servono dati aggiuntivi (es. conferme da altri report o dalle cartelle di servizio).

## Cross-cutting e dipendenze
Dopo aver completato i report di builder/bilanciamento (Encounter_Designer, minmax_builder), verifica se i task si influenzano (es. export/QA condivisi). Se sì, crea una mini-epic di coordinamento e ordina i task per evitare regressioni.

Ripeti lo stesso per i moduli hub/persistenza (Taverna_NPC, tavern_hub, cartelle di servizio) per uniformare policy di salvataggio/quarantena.

## Chiusura
Quando tutti i report sono stati processati, compila un sommario unico (modulo → numero task, priorità massima, blocchi) per supportare la pianificazione sprint.

## Automazione di supporto
- Usa `python tools/generate_module_plan.py --output planning/module_work_plan.md` per generare una bozza di piano operativo dai report esistenti, seguendo la sequenza sopra. Il file risultante elenca, per ogni modulo, i fix (P1), i miglioramenti (P2/P3) e le note d'errore come materiale di lavoro iniziale.
- Integra nel piano i task derivati dalla checklist standard e aggiorna priorità/dependenze dopo la lettura manuale.
- Normalizza i report prima del piano (e comunque prima della revisione manuale) con `python tools/refresh_module_reports.py --write`: lo script legge la sequenza moduli dalla guida, crea eventuali report mancanti e inserisce le sezioni obbligatorie (Ambiente, Esiti API, Metadati, Comandi/Flow, QA, Osservazioni, Errori, Miglioramenti, Fix necessari) con bullet placeholder. Usa `--check` per validare la presenza di tutte le sezioni e di almeno un bullet (exit 1 in caso di heading mancante o vuoto) prima di lanciare `generate_module_plan`.

## Come usarla giorno per giorno
- **Mattina**: scegli il prossimo modulo in sequenza, apri il relativo report e applica la checklist includendo le lenti PF1e (CR/XP, PFS, stacking/prerequisiti/fonti) e sicurezza/observability AI (prompt injection, `qa_logging`+receipt, Echo/Sigilli/fonti); registra i task in `planning/roadmap.md` o in uno strumento di tracking.
- **Durante la lettura**: per ogni issue crea subito il task con priorità e stato; se servono chiarimenti, annota le domande nel report con un tag TODO. Segna sempre quali controlli specialistici (PF1e e sicurezza AI) hai applicato e con quali esiti espliciti (OK/violazione) vicino alle citazioni di linea.
- **Fine giornata**: aggiorna lo stato del modulo (Pronto/In attesa) e aggiungi al sommario finale le nuove evidenze; programma il modulo successivo, assicurandoti che ogni modulo già letto riporti chiaramente i risultati dei controlli PF1e e di sicurezza (inclusi eventuali Errori/Fix necessari con priorità P1/P2).

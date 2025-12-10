# Guida di revisione report moduli

## Sequenza di lettura (copertura completa)
Procedi nell’ordine dell’indice moduli: Encounter_Designer → Taverna_NPC → adventurer_ledger → archivist → base_profile → explain_methods → knowledge_pack → meta_doc → minmax_builder → narrative_flow → ruling_expert → scheda_pg_markdown_template → sigilli_runner_module → tavern_hub, chiudendo con le cartelle di servizio. Questo assicura che tutti i 15 moduli del kernel e le directory di supporto siano coperti una sola volta.

## Metodo di analisi per ogni report
Apri il report corrispondente in `reports/module_tests/<nome>.md`. Usa la struttura standard (Ambiente di test → Esiti API → Metadati → Comandi/Flow → QA → Errori → Miglioramenti → Fix necessari) come checklist; l’esempio di Encounter_Designer mostra tutte le sezioni attese.

Nel blocco Errori e Fix necessari, estrai ogni issue e converti immediatamente in uno o più task con scope e file precisi (seguendo il modello già usato per Encounter_Designer, che ora documenta l’helper CR unico clampato e l’estensione dei gate QA).

Se il report elenca Miglioramenti non bloccanti, valuta priorità: etichetta “P1” per bug/ambiguità funzionali, “P2” per QA/completezza, “P3” per UX/copy. Documenta la priorità accanto al task.

Collega ogni task alle linee del modulo sorgente citate nel report (es. helper CR e gate QA per Encounter_Designer) per facilitare l’implementazione.

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

## Come usarla giorno per giorno
- **Mattina**: scegli il prossimo modulo in sequenza, apri il relativo report e applica la checklist; registra i task in `planning/roadmap.md` o in uno strumento di tracking.
- **Durante la lettura**: per ogni issue crea subito il task con priorità e stato; se servono chiarimenti, annota le domande nel report con un tag TODO.
- **Fine giornata**: aggiorna lo stato del modulo (Pronto/In attesa) e aggiungi al sommario finale le nuove evidenze; programma il modulo successivo.

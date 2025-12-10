# Piano operativo generato dai report

Generato il 2025-12-10T11:02:53Z
Fonte sequenza: `planning/module_review_guide.md`

## Checklist seguita (dal documento di guida)
- Sequenza completa: Encounter_Designer → Taverna_NPC → adventurer_ledger → archivist → base_profile → explain_methods → knowledge_pack → meta_doc → minmax_builder → narrative_flow → ruling_expert → scheda_pg_markdown_template → sigilli_runner_module → tavern_hub → Cartelle di servizio.
- Per ogni report: checklist Ambiente di test → Esiti API → Metadati → Comandi/Flow → QA → Errori → Miglioramenti → Fix necessari.
- Task derivati da Errori/Fix/Miglioramenti con priorità P1 bug/ambiguità, P2 QA/completezza, P3 UX/copy; collegare a sezioni/linee citate nei report.
- Stato modulo: Pronto per sviluppo se i task sono completi e scoped; In attesa se servono dati aggiuntivi.
- Cross-cutting: coordinare builder/bilanciamento (Encounter_Designer, minmax_builder) e hub/persistenza (Taverna_NPC, tavern_hub, Cartelle di servizio).

## Encounter_Designer
- Report: `reports/module_tests/Encounter_Designer.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P1] Consolidare `compute_effective_cr_from_enemies` in una sola implementazione (mantenendo la versione clampata) e aggiornare `/auto_balance` per usare esplicitamente l’helper definitivo, così da rimuovere ambiguità di risultato e manutenzione duplicata.【F:src/modules/Encounter_Designer.txt†L293-L314】【F:src/modules/Encounter_Designer.txt†L780-L800】
- [P1] Ampliare `run_qagates` con gate aggiuntivi per pacing/loot e per la presenza di `balance_snapshot`, bloccando l’export se mancano ondate, loot o la simulazione di rischio/bilanciamento; aggiorna anche i messaggi di QA per guidare l’utente ai comandi `/set_pacing`, `/set_loot_policy`, `/auto_balance` o `/simulate_encounter`.【F:src/modules/Encounter_Designer.txt†L620-L637】【F:src/modules/Encounter_Designer.txt†L357-L398】
- [P2] Estendere i gate QA per coprire pacing/loot/export: oggi la checklist richiede solo nemici, CR stimato e badge/PFS, per cui export può passare anche con ondate vuote o loot mancante. Aggiungere controlli su `pacing`/`loot` eviterebbe snapshot incompleti.【F:src/modules/Encounter_Designer.txt†L620-L637】【F:src/modules/Encounter_Designer.txt†L357-L378】【F:src/modules/Encounter_Designer.txt†L379-L398】
- [P2] Allineare la validazione a `/simulate_encounter`: integrare un gate che verifichi la presenza di `balance_snapshot` (simulazione o auto-balance) garantirebbe export coerenti con i rischi stimati e ridurrebbe QA manuale.【F:src/modules/Encounter_Designer.txt†L316-L350】【F:src/modules/Encounter_Designer.txt†L379-L398】

### Note (Errori)
- Doppia definizione di `compute_effective_cr_from_enemies`: la prima variante calcola una media non clampata ed è richiamata da `/auto_balance`, mentre la seconda (con `_clampf`) sovrascrive la precedente, creando ambiguità su quale logica adottare e su quando applicare i limiti di quantità/CR.【F:src/modules/Encounter_Designer.txt†L293-L314】【F:src/modules/Encounter_Designer.txt†L698-L709】【F:src/modules/Encounter_Designer.txt†L780-L800】

## Taverna_NPC
- Report: `reports/module_tests/Taverna_NPC.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## adventurer_ledger
- Report: `reports/module_tests/adventurer_ledger.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## archivist
- Report: `reports/module_tests/archivist.md`
- Stato: Pronto per sviluppo

### Task (priorità e scope)
- [P2] Allineare il comportamento di `/modules/{name}` al README e ai profili (troncamento a 4000 caratteri o blocco) quando `ALLOW_MODULE_DUMP=false`, includendo un marcatore esplicito per i contenuti parziali.【1411c6†L1-L67】【2130a0†L10-L14】
- [P2] Considerare un header o campo JSON nei dump troncati per indicare size originale e percentuale servita, migliorando la UX rispetto all’attuale mancanza di segnali (vedi anche altri report sui moduli).【1411c6†L1-L67】

### Note (Errori)
- Nessuna nota aggiuntiva

## base_profile
- Report: `reports/module_tests/base_profile.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## explain_methods
- Report: `reports/module_tests/explain_methods.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## knowledge_pack
- Report: `reports/module_tests/knowledge_pack.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## meta_doc
- Report: `reports/module_tests/meta_doc.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## minmax_builder
- Report: `reports/module_tests/minmax_builder.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## narrative_flow
- Report: `reports/module_tests/narrative_flow.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## ruling_expert
- Report: `reports/module_tests/ruling_expert.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## scheda_pg_markdown_template
- Report: `reports/module_tests/scheda_pg_markdown_template.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## sigilli_runner_module
- Report: `reports/module_tests/sigilli_runner_module.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## tavern_hub
- Report: `reports/module_tests/tavern_hub.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## Cartelle di servizio
- Report: `reports/module_tests/service_dirs.md`
- Stato: In attesa (nessun task rilevato)

### Task (priorità e scope)
- Nessun task rilevato

### Note (Errori)
- Nessuna nota aggiuntiva

## Cross-cutting e dipendenze
- Builder/Bilanciamento (Encounter_Designer, minmax_builder): usare i task sopra per valutare epic condivise su export/QA o flow di bilanciamento; ordinare i fix P1 prima dei miglioramenti.
- Hub/Persistenza (Taverna_NPC, tavern_hub, Cartelle di servizio): verificare coerenza delle policy di salvataggio/quarantena e annotare eventuali blocchi prima di procedere con altri moduli dipendenti.

## Chiusura
- Compila il sommario sprint con numero task, priorità massima e blocchi per modulo usando la tabella seguente.

| Modulo | Task totali | Priorità massima | Stato |
| --- | --- | --- | --- |
| Encounter_Designer | 4 | P1 | Pronto per sviluppo |
| Taverna_NPC | 0 | N/A | In attesa (nessun task rilevato) |
| adventurer_ledger | 0 | N/A | In attesa (nessun task rilevato) |
| archivist | 2 | P2 | Pronto per sviluppo |
| base_profile | 0 | N/A | In attesa (nessun task rilevato) |
| explain_methods | 0 | N/A | In attesa (nessun task rilevato) |
| knowledge_pack | 0 | N/A | In attesa (nessun task rilevato) |
| meta_doc | 0 | N/A | In attesa (nessun task rilevato) |
| minmax_builder | 0 | N/A | In attesa (nessun task rilevato) |
| narrative_flow | 0 | N/A | In attesa (nessun task rilevato) |
| ruling_expert | 0 | N/A | In attesa (nessun task rilevato) |
| scheda_pg_markdown_template | 0 | N/A | In attesa (nessun task rilevato) |
| sigilli_runner_module | 0 | N/A | In attesa (nessun task rilevato) |
| tavern_hub | 0 | N/A | In attesa (nessun task rilevato) |
| Cartelle di servizio | 0 | N/A | In attesa (nessun task rilevato) |
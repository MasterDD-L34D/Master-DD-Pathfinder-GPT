# Indice Moduli Kernel

- `Encounter_Designer.txt`: designer completo per incontri PF1e con benchmark, bilanciamento e export VTT-ready.【F:src/modules/Encounter_Designer.txt†L1-L21】
- `Taverna_NPC.txt`: hub generatore PG/PNG e GameMode Solo RPG con quiz adattivo e integrazioni MinMax/Ruling.【F:src/modules/Taverna_NPC.txt†L1-L17】
- `adventurer_ledger.txt`: modulo economia/loot/crafting con ledger transazioni, WBL audit e supporto PFS.【F:src/modules/adventurer_ledger.txt†L1-L34】
- `archivist.txt`: archivio canone PF1e con QA citazioni, badge canone e generatore mappe VTT gridless.【F:src/modules/archivist.txt†L1-L19】
- `base_profile.txt`: kernel base interno che definisce tono, vincoli, router e identità dell’assistente PF1e.【F:src/modules/base_profile.txt†L1-L25】
- `preload_all_modules.txt`: endpoint di warmup protetto da API key che precarica i moduli core locali prima del routing.【F:src/modules/preload_all_modules.txt†L1-L15】
- `explain_methods.txt`: modalità Explain multi-metodo con rubriche didattiche, quiz e deleghe verso Ruling/Archivist/MinMax.【F:src/modules/explain_methods.txt†L1-L21】
- `knowledge_pack.md`: knowledge pack/guida d’uso con risorse ufficiali e istruzioni di recupero moduli via API protetta.【F:src/modules/knowledge_pack.md†L1-L16】
- `meta_doc.txt`: modulo Documenti per blueprint di spec/README/changelog, peer review e pacchetti ZIP finali dei moduli.【F:src/modules/meta_doc.txt†L1-L18】
- `minmax_builder.txt`: builder professionale per creazione e ottimizzazione PG/NPC con flow a step, benchmark DPR e export VTT/PDF.【F:src/modules/minmax_builder.txt†L1-L18】
- `narrative_flow.txt`: modalità Narrativa avanzata con Story Bible, outline/beats, tracker scene e ponte verso altri moduli.【F:src/modules/narrative_flow.txt†L1-L11】
- `ruling_expert.txt`: arbitro RAW/RAI/PFS con rulings referenziati, priorità fonti AoN/Paizo e anti-prompt-injection.【F:src/modules/ruling_expert.txt†L1-L23】
- `scheda_pg_markdown_template.md`: template Markdown parametrico per schede PG con macro per MinMax, VTT, QA ed economia.【F:src/modules/scheda_pg_markdown_template.md†L1-L13】
- `sigilli_runner_module.txt`: logica decorator Sigilli Runner per assegnare sigilli/badge dinamici e tracciare progressi memoria.【F:src/modules/sigilli_runner_module.txt†L1-L17】
- `tavern_hub.json`: stato persistente dell’Hub Taverna (router, run quiz, personaggi, build, incontri, ledger).【F:src/modules/tavern_hub.json†L1-L15】

## Cartelle di servizio

- `src/modules/quarantine/` e `src/data/modules/quarantine/`: cartelle di quarantena per i salvataggi Hub considerati non validi secondo le regole di `hub_storage.validation`, così da isolarli dalle esecuzioni standard.
- `src/modules/taverna_saves/`: directory in cui il modulo Taverna scrive i salvataggi JSON (NPC, quest, voci di taverna, ledger di gioco) applicando policy di naming automatico e controllo del numero massimo di file. La quota e i metadati (path, `max_files`, spazio libero) sono esposti dagli endpoint `GET /modules/taverna_saves/meta` e `GET /modules/taverna_saves/quota`, con una sezione `remediation` che spiega come sbloccare Echo gate <8.5 (ripetere /grade o /refine_npc, in sandbox è ammesso /echo off) o QA CHECK bloccanti (eseguire /self_check, completare Canvas+Ledger e verificare Echo ≥ soglia prima di salvare/esportare).

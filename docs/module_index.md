# Indice Moduli Kernel

- `Encounter_Designer.txt`
- `Taverna_NPC.txt`
- `adventurer_ledger.txt`
- `archivist.txt`
- `base_profile.txt`
- `explain_methods.txt`
- `knowledge_pack.md`
- `meta_doc.txt`
- `minmax_builder.txt`
- `narrative_flow.txt`
- `ruling_expert.txt`
- `scheda_pg_markdown_template.md`
- `sigilli_runner_module.txt`
- `tavern_hub.json`

## Cartelle di servizio

- `src/modules/quarantine/` e `src/data/modules/quarantine/`: cartelle di quarantena per i salvataggi Hub considerati non validi secondo le regole di `hub_storage.validation`, così da isolarli dalle esecuzioni standard.
- `src/modules/taverna_saves/`: directory in cui il modulo Taverna scrive i salvataggi JSON (NPC, quest, voci di taverna, ledger di gioco) applicando policy di naming automatico e controllo del numero massimo di file.

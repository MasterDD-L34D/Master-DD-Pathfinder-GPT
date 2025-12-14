# Release note (RC prep) — kernel base_profile e moduli core

## Chiusura gate
- **Preload base_profile**: warmup obbligatorio via `preload_all_modules` completa il gating `runtime.preload_done` prima del routing, con binding ai file locali di tutti i moduli core.
- **Dump policy**: `ALLOW_MODULE_DUMP=false` applica troncamento `[contenuto troncato]`/header `X-Content-*` ai `.txt` e blocca asset binari, allineato ai log di regression QA.
- **Naming export**: gli export MinMax/Encounter condividono la nomenclatura `MinMax_<nome>.*` e restano dietro i gate QA/CTA (`export_requires`, `/validate_encounter`).

## Stato moduli — tutti "Pronto per sviluppo"
- Encounter_Designer
- Taverna_NPC
- adventurer_ledger
- archivist
- base_profile
- explain_methods
- knowledge_pack
- meta_doc
- minmax_builder
- narrative_flow
- ruling_expert
- scheda_pg_markdown_template
- sigilli_runner_module
- tavern_hub
- Cartelle di servizio

## Circolazione per sign-off
- **Module owner** (da base_profile): Alice Bianchi (Encounter_Designer), Elisa Romano (Taverna_NPC), Luca Ferri (adventurer_ledger), Martina Gallo (archivist), Valentina Riva (ruling_expert), Marco Conti (minmax_builder), Davide Serra (narrative_flow), Francesca Vitale (explain_methods), Chiara Esposito (meta_doc).
- **Referenti QA**: QA Ops (regression/log review) e QA Automation (pytest sandbox) per conferma finale.

## Prossimi passi verso RC
1) Condividere questa nota con gli owner e i referenti QA, raccogliere i sign-off finali (preload/dump/naming export verificati).
2) Una volta ottenuti i sign-off: creare tag/branch `rc/<data>` (es. `rc/2025-12-21`) e annunciare sul canale di rilascio.
3) Messaggio canale: includere data prevista `2025-12-21`, link agli ultimi log QA (`reports/qa_log.md`) e stato "Pronto per sviluppo" per tutti i moduli.

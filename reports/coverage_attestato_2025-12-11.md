# Attestato di copertura QA — Job tracker 2025-12-11

## Input e ambito
- **Log importati (job tracker)**: run `pytest` del 2025-12-11 con **73/73 test passati**, importato da `data/pytest_logs/pytest_run_2025-12-11.json` e validato dal job tracker QA.【F:data/pytest_logs/pytest_run_2025-12-11.json†L1-L9】【F:reports/qa_log.md†L1-L7】
- **Storie coperte**: tutte le storie marcate **Done** nel piano di lavoro e riportate nel tracker sprint.【F:planning/module_work_plan.md†L282-L344】【F:planning/sprint_board.md†L35-L66】
- **Tracker sorgente**: planning/sprint_board.md.
- **Note**: Regression pass completo importato per attestato di copertura.
- **Warning**: jsonschema.RefResolver deprecato in generate_build_db.py.

## Copertura e stato moduli
- Il log di regressione certifica la copertura su API, flow CTA, metadati e policy di dump/troncamento per i moduli in scopo.
- Tutti i moduli risultano **Pronto per sviluppo** secondo la sprint board aggiornata; flag tracking **verde**.【F:planning/sprint_board.md†L35-L66】

## Allegati
- Fonte log: data/pytest_logs/pytest_run_2025-12-11.json.
- Tracker stato moduli: planning/sprint_board.md.

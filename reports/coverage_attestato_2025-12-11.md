# Attestato di copertura QA — Job tracker 2025-12-11

## Input e ambito
- **Log importati**: run pytest del 2025-12-11 con **73/73 test passati**.
- **Storie coperte**: tutte le storie marcate **Done** nel piano di lavoro.
- **Tracker sorgente**: planning/sprint_board.md.
- **Note**: Regression pass completo importato per attestato di copertura.
- **Warning**: jsonschema.RefResolver deprecato in generate_build_db.py.

## Copertura e stato moduli
- Il log di regressione certifica la copertura su API, flow CTA, metadati e policy di dump/troncamento per i moduli in scopo.
- Tutti i moduli risultano **Pronto per sviluppo** secondo la sprint board aggiornata; flag tracking **verde**.

## Allegati
- Fonte log: data/pytest_logs/pytest_run_2025-12-11.json.
- Tracker stato moduli: planning/sprint_board.md.

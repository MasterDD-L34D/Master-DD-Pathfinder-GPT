# Pipeline QA per le build generate

Lo script `tools/build_qa_pipeline.py` carica i payload già salvati da
`generate_build_db` e orchestra una catena di QA multi-servizio:

1. **Ruling Expert** — valida/tagga il `ruling_badge` del payload.
2. **MinMax Builder** — esegue benchmark e QA per confermare lo stato della build.
3. **Hook narrativi opzionali** — chiama `/export_arc_to_build` e/o `/ruling_check`
   (Taverna/Narrative) per arricchire l'export e verificare coerenza.

Ogni step scrive nel report l'esito `PASS/FAIL` con la motivazione; al primo
`FAIL` la build viene marcata `invalid` e il flusso si interrompe.

## Utilizzo

```bash
python tools/build_qa_pipeline.py \
  --ruling-expert-url https://ruling.example.com/validate \
  --minmax-builder-url https://builder.example.com/bench \
  --narrative-export-url https://taverna.example.com/export_arc_to_build \
  --narrative-ruling-check-url https://taverna.example.com/ruling_check \
  --enable-narrative \
  --api-key "$API_KEY" \
  --classes Fighter Wizard \
  --levels 1 5 \
  --max-items 10 --offset 0
```

Opzioni principali:

- `--index-path`/`--report-path`: file di input (default `src/data/build_index.json`) e
  report di output (default `reports/build_qa_report.json`).
- `--classes` e `--levels`: filtri di classe/livello applicati agli snapshot
  presenti nell'indice.
- `--max-items`/`--offset`: riutilizzano lo stesso batching di `generate_build_db`
  per processare finestre parziali di build.
- `--enable-narrative`: abilita gli hook Taverna/Narrative se gli endpoint sono
  configurati; senza endpoint gli step vengono marcati come PASS con motivo
  esplicito.
- `--api-key`: se valorizzato, viene inviato come header `x-api-key` verso tutti
  gli endpoint.

## Struttura del report

Il report (`reports/build_qa_report.json` di default) contiene una voce per ogni
snapshot processato:

```json
{
  "generated_at": "2025-12-10T12:00:00Z",
  "index_path": "src/data/build_index.json",
  "filters": {"classes": ["Fighter"], "levels": [1], "max_items": 5, "offset": 0},
  "entries": [
    {
      "build_file": "src/data/builds/fighter.json",
      "class": "Fighter",
      "level": 1,
      "status": "invalid",
      "steps": [
        {"name": "ruling_expert", "status": "PASS", "reason": "Badge validato", ...},
        {"name": "minmax_builder", "status": "FAIL", "reason": "HTTP 500: ..."}
      ]
    }
  ]
}
```

- `status` a livello di build è `invalid` se uno qualunque degli step fallisce.
- Ogni `step` riporta `reason` e gli eventuali `details` restituiti dagli
  endpoint (badge aggiornato, esito benchmark, ecc.).
- Gli hook narrativi sono aggregati nello step `narrative_hooks` che include il
  risultato di `/export_arc_to_build` e `/ruling_check` quando configurati.

Usa i filtri e il batching per riprendere rapidamente la QA su subset di classi
senza rifare l'intero export.

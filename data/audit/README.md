# Build audit log

Questo percorso ospita i log JSON/JSONL per le richieste di build generate o negate. Il file suggerito è `build_events.jsonl` (non versionato), con un esempio statico in `build_events.sample.jsonl`.

Ogni riga JSON registra:
- `timestamp` (ISO8601): istante della decisione.
- `client_fingerprint_hash`: hash (es. SHA-256) della chiave API o del client.
- `request_ip`: IP pubblico osservato.
- `payload_file`: path della build generata (se disponibile) o `null` se rifiutata prima del salvataggio.
- `outcome`: `accepted`, `denied` o `backoff`.
- `attempt_count`: tentativi consecutivi associati alla chiave/IP al momento della decisione.
- `backoff_reason`: motivo del backoff, `null` se non applicato.

Il backend dovrebbe appendere una riga per ogni richiesta di build (anche quelle respinte) per garantire auditabilità e correlare chiave/IP con lo stato di backoff.

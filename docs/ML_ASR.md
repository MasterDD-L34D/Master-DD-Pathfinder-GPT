# Servizio ASR (REF-09 v1)

Trascrizione audio → testo italiano con timestamp, come primo servizio ML di Taverna (decisione PRD 2026-07-25: servizi ML in Taverna, Python). Implementa il requisito REQ-003 di pathmaster ("Trascrizione IT con timestamp") lato produttore.

## Endpoint

| Metodo | Path | Funzione |
|---|---|---|
| GET | `/ml/health` | Stato del servizio e engine attivo |
| POST | `/ml/transcribe` | Upload audio (`multipart/form-data`, campo `file`) → transcript JSON |

L'app parte **senza dipendenze ML**: il router è registrato con guard e l'engine di default è `fake` (deterministico, per test/sviluppo). Con `ML_ASR_ENGINE=faster_whisper` richiesto ma non installato: **501 onesto** (mai un default silenzioso).

## Contratto output (identico a pathmaster ADR-C2)

L'output è **1:1** con `transcriptImportSchema` di pathmaster (`apps/server/src/lib/transcript-import.ts`): il loro import non richiede modifiche.

```json
{
  "language": "it",
  "segments": [
    {"start": 0.0, "end": 1.5, "text": "...", "confidence": 0.98}
  ]
}
```

- `start`/`end`: secondi (float), `end >= start`
- `confidence`: opzionale, [0,1]
- `speaker`: **omesso in v1** (predisposto per la diarizzazione futura, REQ-010)

## Configurazione (env)

| Variabile | Default | Note |
|---|---|---|
| `ML_ASR_ENGINE` | `fake` | `fake` (mock deterministico) \| `faster_whisper` |
| `ML_ASR_MODEL` | `small` | modello whisper (tiny/base/small/medium/large-v3) |
| `ML_ASR_DEVICE` | `auto` | `auto`/`cpu`/`cuda` |
| `ML_ASR_COMPUTE_TYPE` | `int8` | quantization (int8 = default onesto su CPU) |
| `ML_AUDIO_DIR` | `src/data/ml/audio` | storage WORM dell'audio originale |

## Engine reale (opt-in)

```bash
.venv/Scripts/python -m pip install -r requirements-ml.txt
ML_ASR_ENGINE=faster_whisper .venv/Scripts/uvicorn src.app:app --port 8000
# altro terminale:
curl -F "file=@clip-test.ogg" http://localhost:8000/ml/transcribe
```

Il primo uso scarica il modello (~500 MB per `small`).

## Privacy e vincoli

- **Audio originale immutabile (REQ-001)**: WORM in `ML_AUDIO_DIR/<sha16>_<nome>`, dedup per sha256, mai riscritto.
- **Consenso (REQ-002)**: gate lato pathmaster alla creazione sessione; questo servizio è un transcodificatore "dumb" e non gestisce consenso.
- **Upload max**: 200 MB (sessioni da ore restano fuori v1).
- **Fuori scope v1**: diarizzazione (REQ-010), voiceprint (REQ-012), purge (REQ-015), misura WER/CER (serve corpus audio reale).

## Test

`tests/test_ml_asr.py` (engine/factory/guard) e `tests/test_ml_router.py` (contratto endpoint, 501, WORM dedup) — tutti verdi senza faster-whisper installato.

Piano: `planning/2026-07-25-ref09-asr-service.md`.

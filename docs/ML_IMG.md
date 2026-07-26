# Servizio ML immagini (`/ml/imagine`) — F3

Generazione immagini per il tavolo PathMaster (sfondi mappa, ritratti
token), ratificata in PRD §9.2. Contratto completo:
`pathmaster-dd/docs/superpowers/specs/2026-07-26-img-gen-design.md`.

## Endpoint

```
POST /ml/imagine
{ "prompt": "dungeon di pietra umida", "width": 1024, "height": 768,
  "seed": 42, "engine": "fake" }
→ 200 { "imageId": "img_<sha16>", "sha256": "...", "mimeType": "image/png",
        "width": 1024, "height": 768, "engine": "fake" }
→ 422 input invalido (prompt vuoto/>2000 char, width/height fuori 64..1536)
→ 501 nessun engine configurato/disponibile (messaggio con istruzioni)

GET /ml/imagine/{imageId} → 200 bytes PNG · 404 · 400 (id malformato)
```

- `seed`, `width`, `height`, `engine` sono opzionali (default 1024×1024,
  engine da env). `engine` nella request forza un engine diverso dal
  default (utile per provare `flux` senza cambiare env).
- Le immagini sono **WORM content-addressed** in `data/ml/images/`
  (override env `ML_IMG_DIR`): stesso contenuto → stesso `imageId`.

## Engine (`ML_IMG_ENGINE`, default `off`)

| valore | cosa fa |
|---|---|
| `off` | 501 onesto con istruzioni. Default di sicurezza: niente chiamate/costi accidentali |
| `fake` | PNG deterministico da (prompt, seed, w, h), stdlib pura. Per test e sviluppo offline. Si dichiara `"engine": "fake"` |
| `flux` | FLUX.1-schnell locale via diffusers (Apache 2.0). Richiede `pip install diffusers torch transformers accelerate sentencepiece`; env `ML_IMG_MODEL`, `ML_IMG_DEVICE` (auto/cuda/cpu) |
| `api` | provider esterno: `ML_IMG_API_URL` (+ `ML_IMG_API_KEY` opzionale, header Bearer). La key vive solo in env, mai negli errori |

## Note

- Il fake combina sempre prompt+seed: seed uguale su prompt diversi NON dà
  immagini identiche; stesso (prompt, seed) → stesso sha256 (dedup WORM).
- `GET /ml/health` riporta anche `img_engine`.
- Niente moderazione prompt: tool GM-only locale (v. spec §5).

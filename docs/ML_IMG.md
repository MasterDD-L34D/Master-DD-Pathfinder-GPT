# Servizio ML immagini (`/ml/imagine`) — F3

Generazione immagini per il tavolo PathMaster (sfondi mappa, ritratti
token), ratificata in PRD §9.2. Contratto completo:
`pathmaster-dd/docs/superpowers/specs/2026-07-26-img-gen-design.md`.

## Endpoint

```
POST /ml/imagine
{ "prompt": "dungeon di pietra umida", "width": 1024, "height": 768,
  "seed": 42, "engine": "comfyui-sdxl", "lora": "fantasy-map" }
→ 200 { "imageId": "img_<sha16>", "sha256": "...", "mimeType": "image/png",
        "width": 1024, "height": 768, "engine": "comfyui-sdxl" }
→ 422 input invalido (prompt vuoto/>2000 char, width/height fuori 64..1536)
→ 501 nessun engine configurato/disponibile (messaggio con istruzioni)

GET /ml/imagine/{imageId} → 200 bytes PNG · 404 · 400 (id malformato)
```

- `seed`, `width`, `height`, `engine` sono opzionali (default 1024×1024,
  engine da env). `engine` nella request forza un engine diverso dal
  default (utile per provare `flux` senza cambiare env).
- Le immagini sono **WORM content-addressed** in `data/ml/images/`
  (override env `ML_IMG_DIR`): stesso contenuto → stesso `imageId`.
- Ogni PNG ha un **manifest sidecar** `img_<sha16>.json` (write-once come
  il PNG) con `prompt`, `seed`, `engine`, `width`, `height`, `sha256`,
  `lora` e `created_at` (UTC): la provenienza della generazione sopravvive
  al riavvio senza un DB.

## Engine (`ML_IMG_ENGINE`, default `off`)

| valore | cosa fa |
|---|---|
| `off` | 501 onesto con istruzioni. Default di sicurezza: niente chiamate/costi accidentali |
| `fake` | PNG deterministico da (prompt, seed, w, h), stdlib pura. Per test e sviluppo offline. Si dichiara `"engine": "fake"` |
| `flux` | FLUX.1-schnell locale via diffusers (Apache 2.0). Richiede `pip install diffusers torch transformers accelerate sentencepiece`; env `ML_IMG_MODEL`, `ML_IMG_DEVICE` (auto/cuda/cpu) |
| `api` | provider esterno: `ML_IMG_API_URL` (+ `ML_IMG_API_KEY` opzionale, header Bearer). La key vive solo in env, mai negli errori |
| `comfyui` | **server ComfyUI locale** via HTTP API (default `http://127.0.0.1:8188`, env `ML_IMG_COMFY_URL`). Modello: `ML_IMG_COMFY_MODEL` (default `sdxl`) o suffix engine `comfyui-flux` / `comfyui-sd35m` / `comfyui-qwen`. Se non risponde: 501 con istruzioni di avvio |

### Modelli via ComfyUI (workflow in `src/ml/comfy_workflows.py`)

| engine | file richiesti (in `ComfyUI/models/`) | note |
|---|---|---|
| `comfyui-sdxl` | `checkpoints/sd_xl_base_1.0.safetensors` | 25 step, ~13 s a 1024² su RTX 4070 SUPER |
| `comfyui-flux` | `diffusion_models/flux1-schnell-Q4_K_S.gguf`, `clip/clip_l.safetensors`, `text_encoders/t5xxl_fp8_e4m3fn.safetensors`, `vae/ae.safetensors` | 4 step, Apache 2.0 |
| `comfyui-sd35m` | `diffusion_models/sd3.5_medium-Q4_K_S.gguf`, `clip_l` + `text_encoders/clip_g` + `t5xxl_fp8`, `vae/sd35_vae.safetensors` (16ch, NO VAE SDXL) | Community License (<1M$); `EmptySD3LatentImage` |
| `comfyui-qwen` | `diffusion_models/Qwen_Image-Q4_K_S.gguf`, `text_encoders/Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf`, `vae/qwen_image_vae.safetensors` | 20B, Apache 2.0, text-in-image; encoder SOLO GGUF (no mix fp8_scaled). **BLOCKED su 12GB VRAM**: crash nativo in load unet (access violation, 2 riproduzioni) — riprovare con ≥16GB |

### LoRA (registry nominato)

```bash
ML_IMG_LORAS='{"fantasy-map": {"file": "fantasy_map_v2.safetensors", "strength": 0.8}}'
```

La request accetta `"lora": "fantasy-map"`: il workflow guadagna un nodo
`LoraLoader` (strength su model+clip). Solo engine `comfyui-*`: fake/api/
flux rifiutano `lora` con 501 onesto. Alias sconosciuto o env malformato →
501. Niente path arbitrari dalla API: i file LoRA si registrano solo da env.

### Avvio al bisogno (autostart)

Con `ML_IMG_ENGINE=comfyui`, se ComfyUI non risponde l'engine può avviarlo
da solo (verificato: boot + generazione in ~20 s):

```bash
ML_IMG_COMFY_START_CMD=cmd /c run_nvidia_gpu.bat
ML_IMG_COMFY_START_CWD=C:/AI/ferrospora-spike/ComfyUI_windows_portable
ML_IMG_COMFY_START_TIMEOUT_S=240
```

Senza `ML_IMG_COMFY_START_CMD` il comportamento resta il 501 onesto con
istruzioni di avvio manuale. Su questa macchina la configurazione è già in
`.env` (engine default `comfyui` + modello `sdxl`).

## Note

- Il fake combina sempre prompt+seed: seed uguale su prompt diversi NON dà
  immagini identiche; stesso (prompt, seed) → stesso sha256 (dedup WORM).
- `GET /ml/health` riporta anche `img_engine`.
- Niente moderazione prompt: tool GM-only locale (v. spec §5).

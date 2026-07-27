#!/usr/bin/env bash
# Download modelli img-gen per ComfyUI (F3, scelta 2026-07-26: subset SDXL
# subito, questi in background). Resumable (curl -C -) + verifica dimensione.
set -u
CU=/c/AI/ferrospora-spike/ComfyUI_windows_portable/ComfyUI/models
HF=https://huggingface.co

dl() { # url dest_dir fname expected_mb
  local url="$1" dir="$2" name="$3" exp="$4"
  mkdir -p "$dir"
  echo ">>> $name (~${exp}MB)"
  curl -sL -C - --retry 5 --retry-delay 10 -o "$dir/$name" "$url" || { echo "FAIL $name (curl)"; return 1; }
  local size=$(( $(stat -c%s "$dir/$name") / 1024 / 1024 ))
  if [ "$size" -lt $(( exp - 5 )) ]; then echo "FAIL $name: ${size}MB < ${exp}MB"; return 1; fi
  echo "OK  $name ${size}MB"
}

dl "$HF/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors" "$CU/clip" clip_l.safetensors 230
dl "$HF/Comfy-Org/Lumina_Image_2.0_Repackaged/resolve/main/split_files/vae/ae.safetensors" "$CU/vae" ae.safetensors 315
dl "$HF/Comfy-Org/stable-diffusion-3.5-fp8/resolve/main/text_encoders/clip_g.safetensors" "$CU/text_encoders" clip_g.safetensors 1320
dl "$HF/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors" "$CU/vae" qwen_image_vae.safetensors 240
dl "$HF/city96/FLUX.1-schnell-gguf/resolve/main/flux1-schnell-Q4_K_S.gguf" "$CU/diffusion_models" flux1-schnell-Q4_K_S.gguf 6460
dl "$HF/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors" "$CU/text_encoders" t5xxl_fp8_e4m3fn.safetensors 4660
dl "$HF/city96/stable-diffusion-3.5-medium-gguf/resolve/main/sd3.5_medium-Q4_K_S.gguf" "$CU/diffusion_models" sd3.5_medium-Q4_K_S.gguf 1660
# VAE 16ch di SD3.5 (la GGUF non la include; la VAE SDXL a 4ch NON va bene)
dl "$HF/Inect2/VAE_SD3.5/resolve/main/diffusion_pytorch_model_V2.safetensors" "$CU/vae" sd35_vae.safetensors 155
dl "$HF/QuantStack/Qwen-Image-GGUF/resolve/main/Qwen_Image-Q4_K_S.gguf" "$CU/diffusion_models" Qwen_Image-Q4_K_S.gguf 11570
# Encoder VL in GGUF (il fp8_scaled safetensors non si mixa con unet GGUF)
dl "$HF/ggml-org/Qwen2.5-VL-7B-Instruct-GGUF/resolve/main/Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf" "$CU/text_encoders" Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf 4680

echo "=== DOWNLOAD COMPLETATI ==="

"""Workflow ComfyUI per i modelli img-gen (F3).

Ogni workflow e' un dict nel formato API di ComfyUI (POST /prompt): nodi
con class_type + inputs. Parametrizzati da (prompt, width, height, seed).
Aggiungere un modello = aggiungere una entry in MODELS con il suo builder.
"""
from __future__ import annotations

from typing import Callable


def _sdxl(prompt: str, width: int, height: int, seed: int) -> dict:
    return {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}},
        "2": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode",
              "inputs": {"text": "", "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage",
              "inputs": {"width": width, "height": height, "batch_size": 1}},
        "5": {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": 25, "cfg": 7.0,
                         "sampler_name": "euler", "scheduler": "normal",
                         "denoise": 1.0,
                         "model": ["1", 0], "positive": ["2", 0],
                         "negative": ["3", 0], "latent_image": ["4", 0]}},
        "6": {"class_type": "VAEDecode",
              "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "taverna_img", "images": ["6", 0]}},
    }


def _flux(prompt: str, width: int, height: int, seed: int) -> dict:
    # FLUX.1-schnell GGUF: UnetLoaderGGUF + DualCLIPLoader + VAE dedicato
    return {
        "1": {"class_type": "UnetLoaderGGUF",
              "inputs": {"unet_name": "flux1-schnell-Q4_K_S.gguf"}},
        "2": {"class_type": "DualCLIPLoader",
              "inputs": {"clip_name1": "clip_l.safetensors",
                         "clip_name2": "t5xxl_fp8_e4m3fn.safetensors",
                         "type": "flux"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": 4, "cfg": 1.0,
                         "sampler_name": "euler", "scheduler": "simple",
                         "denoise": 1.0,
                         "model": ["1", 0], "positive": ["4", 0],
                         "negative": ["4", 0], "latent_image": ["5", 0]}},
        "7": {"class_type": "VAEDecode",
              "inputs": {"samples": ["6", 0], "vae": ["3", 0]}},
        "8": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "taverna_img", "images": ["7", 0]}},
    }


def _sd35m(prompt: str, width: int, height: int, seed: int) -> dict:
    # SD 3.5 Medium GGUF: UnetLoaderGGUF + TripleCLIPLoader
    return {
        "1": {"class_type": "UnetLoaderGGUF",
              "inputs": {"unet_name": "sd3.5_medium-Q4_K_S.gguf"}},
        "2": {"class_type": "TripleCLIPLoader",
              "inputs": {"clip_name1": "clip_l.safetensors",
                         "clip_name2": "clip_g.safetensors",
                         "clip_name3": "t5xxl_fp8_e4m3fn.safetensors"}},
        "3": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["2", 0]}},
        "4": {"class_type": "CLIPTextEncode",
              "inputs": {"text": "", "clip": ["2", 0]}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": 25, "cfg": 4.5,
                         "sampler_name": "euler", "scheduler": "sgm_uniform",
                         "denoise": 1.0,
                         "model": ["1", 0], "positive": ["3", 0],
                         "negative": ["4", 0], "latent_image": ["5", 0]}},
        # La GGUF di SD3.5 non include la VAE: la prendiamo dal checkpoint
        # SDXL gia' presente (stessa VAE, nessun download extra).
        "9": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}},
        "7": {"class_type": "VAEDecode",
              "inputs": {"samples": ["6", 0], "vae": ["9", 2]}},
        "8": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "taverna_img", "images": ["7", 0]}},
    }


def _qwen(prompt: str, width: int, height: int, seed: int) -> dict:
    # Qwen-Image GGUF: UnetLoaderGGUF + CLIPLoaderGGUF (VL 7B) + VAE dedicato
    return {
        "1": {"class_type": "UnetLoaderGGUF",
              "inputs": {"unet_name": "Qwen_Image-Q4_K_S.gguf"}},
        "2": {"class_type": "CLIPLoaderGGUF",
              "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors"}},
        "3": {"class_type": "VAELoader",
              "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode",
              "inputs": {"text": "", "clip": ["2", 0]}},
        "6": {"class_type": "EmptyLatentImage",
              "inputs": {"width": width, "height": height, "batch_size": 1}},
        "7": {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": 20, "cfg": 2.5,
                         "sampler_name": "euler", "scheduler": "simple",
                         "denoise": 1.0,
                         "model": ["1", 0], "positive": ["4", 0],
                         "negative": ["5", 0], "latent_image": ["6", 0]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "taverna_img", "images": ["8", 0]}},
    }


MODELS: dict[str, Callable[[str, int, int, int], dict]] = {
    "sdxl": _sdxl,
    "flux": _flux,
    "sd35m": _sd35m,
    "qwen": _qwen,
}


def build_workflow(model: str, prompt: str, width: int, height: int, seed: int) -> dict:
    from src.ml.imagine import ImagineUnavailable
    builder = MODELS.get(model)
    if not builder:
        raise ImagineUnavailable(
            f"workflow sconosciuto: {model!r} (attesi: {', '.join(MODELS)})")
    return builder(prompt, width, height, seed)

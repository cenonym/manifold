#!/usr/bin/env bash
set -euo pipefail

MODELS="${MODELS:-$HOME/ComfyUI-Shared/models}"

dl() {
    local dir="$1"
    local url="$2"
    local name
    name="$(basename "$url")"
    mkdir -p "$MODELS/$dir"
    local target="$MODELS/$dir/$name"
    if [ -f "$target" ]; then
        echo "have $name"
        return
    fi
    echo "fetching $name"
    if [ -n "${HF_TOKEN:-}" ]; then
        curl -L --fail --retry 5 --retry-delay 5 -C - -H "Authorization: Bearer $HF_TOKEN" -o "$target.part" "$url"
    else
        curl -L --fail --retry 5 --retry-delay 5 -C - -o "$target.part" "$url"
    fi
    mv "$target.part" "$target"
}

dl diffusion_models https://huggingface.co/Comfy-Org/Pixal3D/resolve/main/diffusion_models/pixal3d_int8_convrot.safetensors
dl diffusion_models https://huggingface.co/Comfy-Org/TRELLIS.2/resolve/main/diffusion_models/trellis_2_int8_convrot.safetensors
dl vae https://huggingface.co/Comfy-Org/Pixal3D/resolve/main/vae/trellis_2_shape_vae_bf16.safetensors
dl vae https://huggingface.co/Comfy-Org/Pixal3D/resolve/main/vae/trellis_2_texture_vae_bf16.safetensors
dl clip_vision https://huggingface.co/Comfy-Org/Pixal3D/resolve/main/clip_vision/dino_v3_L_naf_fp32.safetensors
dl geometry_estimation https://huggingface.co/Comfy-Org/MoGe/resolve/main/geometry_estimation/moge_2_vitl_normal_fp16.safetensors
dl background_removal https://huggingface.co/Comfy-Org/BiRefNet/resolve/main/background_removal/birefnet.safetensors

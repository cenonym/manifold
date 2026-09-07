# Manifold

ComfyUI nodes for clean, game-ready topology from image-to-3D meshes. Native Pixal3D and TRELLIS.2 generate, AutoRemesher and headless Blender retopologize, Save Asset writes versioned GLB, FBX, OBJ with a reproducibility sidecar.

## Setup

1. Comfy Desktop with core 0.34+, Blender 5.2+, AutoRemesher 1.2+.
2. `./scripts/link.sh` (symlinks into custom_nodes, copies manifold.toml.example to manifold.toml). Edit paths if needed.
3. `./scripts/download_weights.sh` on real bandwidth, about 14 GB into `~/ComfyUI-Shared/models`.
4. Open `workflows/manifold-pixal3d.json`. `workflows/retopo-only.json` runs without weights from any glb, fbx, obj or stl in `~/ComfyUI-Shared/input/3d/`.

## Nodes

Manifold From Mesh, Manifold From File, Free Models, Blender Clean, Quad Remesh, Blender Decimate, Blender Finish, Save Asset. Category `manifold`.

On Apple Silicon two shims patch ComfyUI at load (int8 weights to bf16, TRELLIS hashmap sort). Both are on by default in `manifold.toml` under `[compat]`.

## Test

`./scripts/test.sh`

# Manifold

ComfyUI nodes for clean, game-ready topology from image-to-3D meshes. Native Pixal3D or TRELLIS.2 generate a dense mesh, Blender and AutoRemesher clean and retopologize it, Save Asset writes a versioned GLB, FBX and OBJ with a reproducibility sidecar. Runs on Apple Silicon; about 3.5 minutes from image to asset on an M3 Pro.

## Setup

1. Comfy Desktop with core 0.34+, Blender 5.2+, AutoRemesher 1.2+.
2. `./scripts/link.sh` symlinks the repo into `custom_nodes/manifold` and copies `manifold.toml.example` to `manifold.toml`. Edit tool paths and `output_root` if they differ.
3. `./scripts/download_weights.sh` fetches the seven weight files, about 14 GB, resumable, into `~/ComfyUI-Shared/models` (Comfy Desktop's shared models folder).
4. Restart Comfy Desktop. Workflow, Open, `workflows/manifold.json`.

## Workflow

`workflows/manifold.json` is ten nodes: Load Image, two toggles, three subgraphs and four previews.

- Toggles: **Remove background** (default on) and **Use TRELLIS.2** (default off, Pixal3D). One Boolean switches the model, the crop pad factor and the Clean solidify setting; the unselected model never loads.
- **Source**: background removal, crop, MoGe depth, DINO, conditioning.
- **Generate**: seed, cfg, structure_steps, shape_steps. Shape decodes at 512; the upsample and texture stages are left out, retopo does not need them.
- **Retopo**: target_quads and name. Inside: From Mesh, Free Models (unloads the 10 GB model), Blender Clean (voxel remesh, closes the decoder's double shell), collapse to 50K, then Quad Remesh (AutoRemesher) and a planar Blender Decimate branch, each through Blender Finish, and Save Asset on the quad branch.
- Previews: voxel structure, cleaned mesh, quad result, planar result.

Output: `<output_root>/<name>/v<N>/` with `<name>.glb` (triangulated), `<name>.fbx` and `<name>.obj` (quads kept), `source.png`, and `manifold.json` (timestamp, tool versions, face and vertex counts, source image hash, the exact prompt that ran).

`workflows/retopo-only.json` runs without weights from any glb, fbx, obj or stl placed in `~/ComfyUI-Shared/input/3d/`.

Edit `workflows/manifold-flat.json`, then `scripts/subgraphify.py` regenerates `manifold.json`; `--check` validates the wiring. After any change to a node's inputs, reopen the workflow from disk; the frontend otherwise restores the previous graph from browser storage.

## Nodes

Category `manifold`: Manifold From Mesh, Manifold From File, Free Models, Blender Clean, Quad Remesh, Blender Decimate, Blender Finish, Save Asset. Every op node outputs its `MANIFOLD_MESH` (an OBJ path, quads preserved) plus a triangulated native Mesh preview.

## Apple Silicon

Two shims patch ComfyUI at load, both on by default under `[compat]` in `manifold.toml`:

- `mps_int8_bf16`: int8 quantized weights materialize to bf16, since the int8 matmul kernel is missing on MPS and the CPU fallback is 300x slower.
- `mps_hashmap_sort`: the TRELLIS decoder's voxel hashmap sorts int64 keys with argsort, since `torch.sort` on MPS rounds int64 values through float32.

Both fail loudly at startup if a ComfyUI upgrade moves the hooks. ComfyUI's native Remesh, Decimate and Fill Holes mesh nodes crash on MPS and are not used.

## Config

`manifold.toml`: `[tools]` blender and autoremesher paths, `[paths]` output_root, `[compat]` the two shims. Config is never taken from node inputs, so graphs stay machine independent.

## Test

`./scripts/test.sh`, pytest in the ComfyUI venv. Blender and AutoRemesher tests skip when the tools are missing. Select tests with `-k name`.

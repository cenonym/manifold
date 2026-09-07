from pathlib import Path

import torch
from comfy_api.latest import IO, Types

from ..core.mesh import read_obj, triangulate

ManifoldMesh = IO.Custom("MANIFOLD_MESH")


def preview_mesh(path: Path) -> Types.MESH:
    v, faces = read_obj(path)
    tris = triangulate(faces)
    return Types.MESH(vertices=torch.from_numpy(v).unsqueeze(0), faces=torch.from_numpy(tris).unsqueeze(0))

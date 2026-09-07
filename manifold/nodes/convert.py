from pathlib import Path

import numpy as np

from ..core.mesh import write_obj


def _np(x):
    return x.detach().cpu().numpy() if hasattr(x, "detach") else np.asarray(x)


def first_item(vertices, faces, vertex_counts, face_counts) -> tuple[np.ndarray, np.ndarray]:
    if isinstance(vertices, list):
        v, f = vertices[0], faces[0]
    elif vertices.ndim == 3:
        v, f = vertices[0], faces[0]
        if vertex_counts is not None:
            v, f = v[: int(vertex_counts[0])], f[: int(face_counts[0])]
    else:
        v, f = vertices, faces
    return _np(v).astype(np.float32), _np(f).astype(np.int64)


def mesh_to_obj(vertices: np.ndarray, faces: np.ndarray, path: Path) -> None:
    write_obj(path, vertices, faces.tolist())

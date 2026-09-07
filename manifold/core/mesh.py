from pathlib import Path

import numpy as np

Faces = list[list[int]]


def read_obj(path: Path) -> tuple[np.ndarray, Faces]:
    vertices: list[list[float]] = []
    faces: Faces = []
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "v":
            vertices.append([float(x) for x in parts[1:4]])
        elif parts[0] == "f":
            idx = [int(tok.split("/")[0]) for tok in parts[1:]]
            if any(i <= 0 for i in idx):
                raise ValueError(f"{path}: negative or zero OBJ indices unsupported")
            faces.append([i - 1 for i in idx])
    if not vertices or not faces:
        raise ValueError(f"{path}: no geometry")
    return np.asarray(vertices, dtype=np.float32), faces


def write_obj(path: Path, vertices: np.ndarray, faces: Faces) -> None:
    lines = [f"v {x:.6f} {y:.6f} {z:.6f}" for x, y, z in vertices]
    lines += ["f " + " ".join(str(i + 1) for i in face) for face in faces]
    Path(path).write_text("\n".join(lines) + "\n")


def triangulate(faces: Faces) -> np.ndarray:
    tris = [[f[0], f[i], f[i + 1]] for f in faces for i in range(1, len(f) - 1)]
    return np.asarray(tris, dtype=np.int64).reshape(-1, 3)


def face_stats(faces: Faces) -> dict[str, int]:
    sizes = [len(f) for f in faces]
    return {
        "faces": len(sizes),
        "tris": sizes.count(3),
        "quads": sizes.count(4),
        "ngons": sum(1 for s in sizes if s > 4),
    }

from pathlib import Path

import numpy as np
import pytest

from manifold.core.mesh import face_stats, read_obj, triangulate, write_obj

CUBE = Path(__file__).parent / "fixtures" / "cube.obj"


def test_read_cube_keeps_quads():
    v, f = read_obj(CUBE)
    assert v.shape == (8, 3) and v.dtype == np.float32
    assert len(f) == 6 and all(len(face) == 4 for face in f)
    assert f[0] == [0, 3, 2, 1]


def test_read_skips_slashes_and_other_lines(tmp_path):
    p = tmp_path / "m.obj"
    p.write_text("# c\nvn 0 0 1\nvt 0 0\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1/1/1 2/2/1 3/3/1\n")
    v, f = read_obj(p)
    assert len(v) == 3 and f == [[0, 1, 2]]


def test_read_rejects_negative_index(tmp_path):
    p = tmp_path / "m.obj"
    p.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf -1 -2 -3\n")
    with pytest.raises(ValueError, match="negative"):
        read_obj(p)


def test_read_rejects_empty(tmp_path):
    p = tmp_path / "m.obj"
    p.write_text("# nothing\n")
    with pytest.raises(ValueError, match="no geometry"):
        read_obj(p)


def test_write_round_trip(tmp_path):
    v, f = read_obj(CUBE)
    out = tmp_path / "out.obj"
    write_obj(out, v, f)
    v2, f2 = read_obj(out)
    assert np.allclose(v, v2) and f == f2


def test_triangulate_fan():
    tris = triangulate([[0, 1, 2, 3], [4, 5, 6]])
    assert tris.dtype == np.int64
    assert tris.tolist() == [[0, 1, 2], [0, 2, 3], [4, 5, 6]]


def test_triangulate_empty():
    assert triangulate([]).shape == (0, 3)


def test_face_stats():
    assert face_stats([[0, 1, 2], [0, 1, 2, 3], [0, 1, 2, 3, 4]]) == {"faces": 3, "tris": 1, "quads": 1, "ngons": 1}

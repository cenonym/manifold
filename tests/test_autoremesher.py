from pathlib import Path

import pytest

from manifold.core.autoremesher import RemeshParams, autoremesher_version, parse_report, quad_remesh
from manifold.core.config import Config
from manifold.core.mesh import face_stats, read_obj

EXE = Path("/Applications/autoremesher.app/Contents/MacOS/autoremesher")
CUBE = Path(__file__).parent / "fixtures" / "cube.obj"
needs_tool = pytest.mark.skipif(not EXE.exists(), reason="autoremesher not installed")


def test_parse_report():
    text = "Quads: 120\nNon-quads: 3\nVertices: 130\nTime: 1.2s\nnoise line\n"
    assert parse_report(text) == {"quads": "120", "non-quads": "3", "vertices": "130", "time": "1.2s"}


def test_params_defaults_match_cli():
    p = RemeshParams()
    assert (p.target_quads, p.edge_scaling, p.sharp_edge, p.smooth_normal, p.adaptivity, p.anisotropy) == (50000, 1.0, 90.0, 0.0, 1.0, 1.0)


@needs_tool
def test_version(tmp_path):
    cfg = Config(blender=Path("/nope"), autoremesher=EXE, output_root=tmp_path)
    assert autoremesher_version(cfg)


@needs_tool
def test_cube_remeshes_to_quads(tmp_path):
    cfg = Config(blender=Path("/nope"), autoremesher=EXE, output_root=tmp_path)
    out = tmp_path / "quad.obj"
    report = quad_remesh(cfg, CUBE, out, RemeshParams(target_quads=200))
    v, f = read_obj(out)
    stats = face_stats(f)
    assert stats["quads"] > stats["tris"] + stats["ngons"]
    assert isinstance(report, dict)

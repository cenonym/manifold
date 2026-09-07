import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from manifold.core.blender import SCRIPTS, blender_version, run_blender
from manifold.core.config import Config
from manifold.core.mesh import face_stats, read_obj

BLENDER = Path("/Applications/Blender.app/Contents/MacOS/Blender")
CUBE = Path(__file__).parent / "fixtures" / "cube.obj"
pytestmark = pytest.mark.skipif(not BLENDER.exists(), reason="blender not installed")


@pytest.fixture
def cfg(tmp_path):
    return Config(blender=BLENDER, autoremesher=Path("/nope"), output_root=tmp_path)


def test_scripts_exist():
    for s in ["decimate.py", "finish.py", "export.py", "convert.py"]:
        assert (SCRIPTS / s).is_file()


def test_version(cfg):
    assert blender_version(cfg).startswith("Blender 5.")


def test_decimate_collapse_reduces(cfg, tmp_path):
    out = tmp_path / "out.obj"
    run_blender(cfg, "decimate.py", [str(CUBE), str(out)], {"mode": "collapse", "ratio": 0.5}, expect=out)
    _, f = read_obj(out)
    assert 0 < len(f) < 12


def test_decimate_planar_keeps_cube(cfg, tmp_path):
    out = tmp_path / "out.obj"
    run_blender(cfg, "decimate.py", [str(CUBE), str(out)], {"mode": "planar", "angle": 5.0}, expect=out)
    assert face_stats(read_obj(out)[1])["faces"] == 6


def test_finish_scales_and_grounds(cfg, tmp_path):
    out = tmp_path / "out.obj"
    run_blender(cfg, "finish.py", [str(CUBE), str(out)], {"target_height": 2.0, "triangulate": True, "smart_uv": True}, expect=out)
    v, f = read_obj(out)
    assert np.isclose(v[:, 1].min(), 0.0, atol=1e-4) and np.isclose(v[:, 1].max(), 2.0, atol=1e-4)
    assert np.isclose(v[:, 0].mean(), 0.0, atol=1e-4) and np.isclose(v[:, 2].mean(), 0.0, atol=1e-4)
    assert face_stats(f) == {"faces": 12, "tris": 12, "quads": 0, "ngons": 0}
    assert any(line.startswith("vt ") for line in out.read_text().splitlines())


def test_finish_keeps_quads_without_triangulate(cfg, tmp_path):
    out = tmp_path / "out.obj"
    run_blender(cfg, "finish.py", [str(CUBE), str(out)], {"target_height": 0, "triangulate": False, "smart_uv": False}, expect=out)
    assert face_stats(read_obj(out)[1])["quads"] == 6


def test_export_writes_three_formats(cfg, tmp_path):
    out_dir = tmp_path / "v1"
    out_dir.mkdir()
    run_blender(cfg, "export.py", [str(CUBE), str(out_dir)], {"name": "cube"}, expect=out_dir / "cube.glb")
    for ext in ["obj", "fbx", "glb"]:
        assert (out_dir / f"cube.{ext}").stat().st_size > 0
    assert face_stats(read_obj(out_dir / "cube.obj")[1])["quads"] == 6


def test_script_error_surfaces(cfg, tmp_path):
    out = tmp_path / "out.obj"
    with pytest.raises(Exception) as e:
        run_blender(cfg, "decimate.py", [str(tmp_path / "missing.obj"), str(out)], {}, expect=out)
    assert "blender" in str(e.value)


def _make_glb(tmp_path):
    glb = tmp_path / "cube.glb"
    expr = (
        "import bpy; bpy.ops.wm.read_factory_settings(use_empty=True); "
        f"bpy.ops.wm.obj_import(filepath={str(CUBE)!r}); "
        f"bpy.ops.export_scene.gltf(filepath={str(glb)!r}, export_format='GLB')"
    )
    subprocess.run(
        [str(BLENDER), "--background", "--factory-startup", "--python-exit-code", "1", "--python-expr", expr],
        check=True, capture_output=True,
    )
    return glb


def test_convert_glb_roundtrip(cfg, tmp_path):
    out = tmp_path / "out.obj"
    run_blender(cfg, "convert.py", [str(_make_glb(tmp_path)), str(out)], {}, expect=out)
    v, f = read_obj(out)
    assert len(v) == 8
    assert face_stats(f) == {"faces": 12, "tris": 12, "quads": 0, "ngons": 0}
    assert np.allclose(v.min(axis=0), 0.0, atol=1e-4)
    assert np.allclose(v.max(axis=0), 1.0, atol=1e-4)


def test_convert_obj_keeps_quads(cfg, tmp_path):
    out = tmp_path / "out.obj"
    run_blender(cfg, "convert.py", [str(CUBE), str(out)], {}, expect=out)
    v, f = read_obj(out)
    assert len(v) == 8
    assert face_stats(f)["quads"] == 6


def test_convert_unknown_extension_errors(cfg, tmp_path):
    src = tmp_path / "thing.xyz"
    src.write_text("nope")
    out = tmp_path / "out.obj"
    with pytest.raises(Exception) as e:
        run_blender(cfg, "convert.py", [str(src), str(out)], {}, expect=out)
    assert "blender" in str(e.value)

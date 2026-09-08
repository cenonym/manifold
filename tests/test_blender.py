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


def _tris(faces):
    return sum(len(f) - 2 for f in faces)


def _subdivided_cube(cfg, tmp_path):
    out = tmp_path / "subcube.obj"
    expr = (
        "import bpy;"
        "bpy.ops.wm.read_factory_settings(use_empty=True);"
        "bpy.ops.mesh.primitive_cube_add(size=2);"
        "bpy.ops.object.mode_set(mode='EDIT');"
        "bpy.ops.mesh.select_all(action='SELECT');"
        "bpy.ops.mesh.subdivide(number_cuts=2);"
        "bpy.ops.object.mode_set(mode='OBJECT');"
        f"bpy.ops.wm.obj_export(filepath={str(out)!r}, export_materials=False, export_normals=False)"
    )
    subprocess.run([str(cfg.blender), "-b", "--python-expr", expr], check=True, capture_output=True)
    return out


def test_decimate_collapse_target_faces(cfg, tmp_path):
    out = tmp_path / "out.obj"
    run_blender(cfg, "decimate.py", [str(CUBE), str(out)], {"mode": "collapse", "ratio": 1.0, "target_faces": 6}, expect=out)
    _, f = read_obj(out)
    assert 0 < _tris(f) <= 8


def test_decimate_collapse_target_faces_subdivided(cfg, tmp_path):
    src = _subdivided_cube(cfg, tmp_path)
    out = tmp_path / "out.obj"
    run_blender(cfg, "decimate.py", [str(src), str(out)], {"mode": "collapse", "ratio": 1.0, "target_faces": 40}, expect=out)
    _, f = read_obj(out)
    assert 30 <= _tris(f) <= 50


def test_decimate_collapse_target_faces_zero_uses_ratio(cfg, tmp_path):
    out = tmp_path / "out.obj"
    run_blender(cfg, "decimate.py", [str(CUBE), str(out)], {"mode": "collapse", "ratio": 0.5, "target_faces": 0}, expect=out)
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


def _closed(faces):
    directed = set()
    for face in faces:
        for i in range(len(face)):
            directed.add((face[i], face[(i + 1) % len(face)]))
    return all((b, a) in directed for a, b in directed)


def test_clean_cube_is_closed(cfg, tmp_path):
    out = tmp_path / "out.obj"
    run_blender(cfg, "clean.py", [str(CUBE), str(out)], {"voxel_scale": 0.03, "solidify": 0, "min_component": 0.01, "smooth": 0}, expect=out)
    v, f = read_obj(out)
    assert _closed(f)
    size = v.max(axis=0) - v.min(axis=0)
    assert np.allclose(size, 1.0, rtol=0.1)


def _cube_plus_speck(cfg, tmp_path):
    out = tmp_path / "speck.obj"
    expr = (
        "import bpy;"
        "bpy.ops.wm.read_factory_settings(use_empty=True);"
        "bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0));"
        "bpy.ops.mesh.primitive_cube_add(size=0.05, location=(3,0,0));"
        f"bpy.ops.wm.obj_export(filepath={str(out)!r}, export_materials=False, export_normals=False)"
    )
    subprocess.run([str(cfg.blender), "-b", "--python-expr", expr], check=True, capture_output=True)
    return out


def test_clean_drops_small_component(cfg, tmp_path):
    src = _cube_plus_speck(cfg, tmp_path)
    out = tmp_path / "out.obj"
    run_blender(cfg, "clean.py", [str(src), str(out)], {"voxel_scale": 0.03, "solidify": 0, "min_component": 0.01, "smooth": 0}, expect=out)
    v, _ = read_obj(out)
    assert v[:, 0].max() < 1.0


def test_clean_min_component_zero_keeps_both(cfg, tmp_path):
    src = _cube_plus_speck(cfg, tmp_path)
    out = tmp_path / "out.obj"
    run_blender(cfg, "clean.py", [str(src), str(out)], {"voxel_scale": 0.03, "solidify": 0, "min_component": 0.0, "smooth": 0}, expect=out)
    v, _ = read_obj(out)
    assert v[:, 0].max() > 2.0


def test_clean_min_component_one_keeps_largest_only(cfg, tmp_path):
    src = _cube_plus_speck(cfg, tmp_path)
    out = tmp_path / "out.obj"
    run_blender(cfg, "clean.py", [str(src), str(out)], {"voxel_scale": 0.03, "solidify": 0, "min_component": 1.0, "smooth": 0}, expect=out)
    v, f = read_obj(out)
    assert v[:, 0].max() < 1.0
    assert _closed(f)


def _open_sheet(cfg, tmp_path):
    out = tmp_path / "sheet.obj"
    expr = (
        "import bpy;"
        "bpy.ops.wm.read_factory_settings(use_empty=True);"
        "bpy.ops.mesh.primitive_plane_add(size=1);"
        "bpy.ops.object.mode_set(mode='EDIT');"
        "bpy.ops.mesh.select_all(action='SELECT');"
        "bpy.ops.mesh.subdivide(number_cuts=9);"
        "bpy.ops.object.mode_set(mode='OBJECT');"
        f"bpy.ops.wm.obj_export(filepath={str(out)!r}, export_materials=False, export_normals=False)"
    )
    subprocess.run([str(cfg.blender), "-b", "--python-expr", expr], check=True, capture_output=True)
    return out


def _boundary_edges(faces):
    counts = {}
    for face in faces:
        for i in range(len(face)):
            a, b = face[i], face[(i + 1) % len(face)]
            key = (a, b) if a < b else (b, a)
            counts[key] = counts.get(key, 0) + 1
    return sum(1 for n in counts.values() if n == 1)


def test_clean_open_sheet_without_solidify_stays_open(cfg, tmp_path):
    src = _open_sheet(cfg, tmp_path)
    out = tmp_path / "out.obj"
    run_blender(cfg, "clean.py", [str(src), str(out)], {"voxel_scale": 2.5, "solidify": 0, "min_component": 0.01}, expect=out)
    v, f = read_obj(out)
    assert len(f) < 8 or _boundary_edges(f) > 0 or (v.max(axis=0) - v.min(axis=0))[1] < 1e-4


def test_clean_open_sheet_solidify_closes(cfg, tmp_path):
    src = _open_sheet(cfg, tmp_path)
    out = tmp_path / "out.obj"
    run_blender(cfg, "clean.py", [str(src), str(out)], {"voxel_scale": 2.5, "solidify": 1.5, "min_component": 0.01}, expect=out)
    v, f = read_obj(out)
    assert _boundary_edges(f) == 0
    assert _closed(f)
    thickness = (v.max(axis=0) - v.min(axis=0))[1]
    assert 0.05 < thickness < 0.4


def _doubled_cube(tmp_path):
    v, f = read_obj(CUBE)
    out = tmp_path / "doubled.obj"
    lines = []
    for _ in range(2):
        for x, y, z in v:
            lines.append(f"v {x} {y} {z}")
    n = len(v)
    for off in (0, n):
        for face in f:
            lines.append("f " + " ".join(str(i + 1 + off) for i in face))
    out.write_text("\n".join(lines) + "\n")
    return out


def test_clean_welds_duplicate_vertices(cfg, tmp_path):
    src = _doubled_cube(tmp_path)
    out = tmp_path / "out.obj"
    run_blender(cfg, "clean.py", [str(src), str(out)], {"voxel_scale": 0.03, "solidify": 0, "min_component": 0.01}, expect=out)
    _, f = read_obj(out)
    assert _closed(f)
    assert _boundary_edges(f) == 0


def test_clean_edgeless_mesh_errors(cfg, tmp_path):
    src = tmp_path / "points.obj"
    src.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\n")
    out = tmp_path / "out.obj"
    with pytest.raises(Exception) as e:
        run_blender(cfg, "clean.py", [str(src), str(out)], {"voxel_scale": 2.5, "solidify": 0, "min_component": 0.01}, expect=out)
    assert "blender" in str(e.value)

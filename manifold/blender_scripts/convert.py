import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy

from _common import args, clear_scene, export_obj, join_meshes, override

IMPORTERS = {
    ".obj": lambda p: bpy.ops.wm.obj_import(filepath=p),
    ".glb": lambda p: bpy.ops.import_scene.gltf(filepath=p, merge_vertices=True),
    ".gltf": lambda p: bpy.ops.import_scene.gltf(filepath=p, merge_vertices=True),
    ".fbx": lambda p: bpy.ops.import_scene.fbx(filepath=p),
    ".stl": lambda p: bpy.ops.wm.stl_import(filepath=p),
}

(src, dst), _ = args()
ext = os.path.splitext(src)[1].lower()
if ext not in IMPORTERS:
    raise RuntimeError(f"unsupported 3d format {ext or src}")
clear_scene()
IMPORTERS[ext](src)
obj = join_meshes(src)
with override(obj):
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=1e-5)
    bpy.ops.object.mode_set(mode="OBJECT")
export_obj(obj, dst)

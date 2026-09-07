import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
from _common import args, clear_scene, export_obj, import_obj, override

(src, out_dir), p = args()
name = p["name"]
clear_scene()
obj = import_obj(src)
export_obj(obj, os.path.join(out_dir, f"{name}.obj"))
with override(obj):
    bpy.ops.export_scene.fbx(filepath=os.path.join(out_dir, f"{name}.fbx"), use_selection=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, f"{name}.glb"), export_format="GLB", use_selection=True)

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
from _common import apply_modifier, args, clear_scene, export_obj, import_obj, override

(src, dst), p = args()
clear_scene()
obj = import_obj(src)
with override(obj):
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

me = obj.data
co = np.empty(len(me.vertices) * 3, dtype=np.float64)
me.vertices.foreach_get("co", co)
co = co.reshape(-1, 3)
lo, hi = co.min(axis=0), co.max(axis=0)
co -= np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
height = hi[2] - lo[2]
target = float(p.get("target_height", 0))
if target > 0 and height > 0:
    co *= target / height
me.vertices.foreach_set("co", co.ravel())
me.update()

if p.get("triangulate", False):
    apply_modifier(obj, obj.modifiers.new("triangulate", "TRIANGULATE"))

if p.get("smart_uv", False):
    with override(obj):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(
            angle_limit=math.radians(float(p.get("uv_angle", 66.0))),
            island_margin=float(p.get("uv_margin", 0.02)),
        )
        bpy.ops.object.mode_set(mode="OBJECT")

export_obj(obj, dst)

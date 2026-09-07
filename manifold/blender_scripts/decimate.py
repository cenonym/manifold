import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import apply_modifier, args, clear_scene, export_obj, import_obj

(src, dst), p = args()
clear_scene()
obj = import_obj(src)
mod = obj.modifiers.new("decimate", "DECIMATE")
if p.get("mode", "planar") == "planar":
    mod.decimate_type = "DISSOLVE"
    mod.angle_limit = math.radians(float(p.get("angle", 5.0)))
else:
    mod.decimate_type = "COLLAPSE"
    target = int(p.get("target_faces", 0))
    tris = sum(len(poly.vertices) - 2 for poly in obj.data.polygons)
    if target > 0 and tris > 0:
        mod.ratio = min(1.0, target / tris)
    else:
        mod.ratio = float(p.get("ratio", 0.5))
apply_modifier(obj, mod)
export_obj(obj, dst)

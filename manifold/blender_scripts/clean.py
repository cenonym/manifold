import os
import sys
from array import array

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import apply_modifier, args, clear_scene, export_obj, import_obj


def components(me):
    edge_faces = {}
    for poly in me.polygons:
        for key in poly.edge_keys:
            edge_faces.setdefault(key, []).append(poly.index)
    label = array("i", [-1]) * len(me.polygons)
    sizes = []
    for start in range(len(me.polygons)):
        if label[start] >= 0:
            continue
        cid = len(sizes)
        stack = [start]
        label[start] = cid
        count = 0
        while stack:
            fi = stack.pop()
            count += 1
            for key in me.polygons[fi].edge_keys:
                for nb in edge_faces[key]:
                    if label[nb] < 0:
                        label[nb] = cid
                        stack.append(nb)
        sizes.append(count)
    return label, sizes


def drop_small(obj, min_component):
    me = obj.data
    label, sizes = components(me)
    if len(sizes) < 2:
        return
    threshold = max(sizes) * min_component
    doomed = {i for i, n in enumerate(sizes) if n < threshold}
    if not doomed:
        return
    for poly in me.polygons:
        poly.select = label[poly.index] in doomed
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.select], context="FACES")
    bm.to_mesh(me)
    bm.free()
    me.update()


(src, dst), p = args()
clear_scene()
obj = import_obj(src)

dims = obj.dimensions
longest = max(dims[0], dims[1], dims[2])
divisions = max(1, int(p.get("voxel_divisions", 216)))
mod = obj.modifiers.new("voxel", "REMESH")
mod.mode = "VOXEL"
mod.voxel_size = longest / divisions
mod.use_remove_disconnected = False
apply_modifier(obj, mod)

min_component = float(p.get("min_component", 0.01))
if min_component > 0:
    drop_small(obj, min_component)

for _ in range(int(p.get("smooth", 0))):
    apply_modifier(obj, obj.modifiers.new("smooth", "SMOOTH"))

export_obj(obj, dst)

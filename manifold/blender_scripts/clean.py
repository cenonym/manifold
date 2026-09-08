import os
import sys
from array import array

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy

from _common import apply_modifier, args, clear_scene, export_obj, import_obj, override


def median_edge(me, src):
    if not len(me.edges):
        raise RuntimeError(f"{src}: no usable edges")
    idx = np.empty(len(me.edges) * 2, dtype=np.int32)
    me.edges.foreach_get("vertices", idx)
    co = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)[idx.reshape(-1, 2)]
    edge = float(np.median(np.linalg.norm(co[:, 0] - co[:, 1], axis=1)))
    if not np.isfinite(edge) or edge <= 0:
        raise RuntimeError(f"{src}: no usable edges")
    return edge


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

with override(obj):
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=1e-5)
    bpy.ops.object.mode_set(mode="OBJECT")

edge = median_edge(obj.data, src)

solidify = float(p.get("solidify", 0.0))
if solidify > 0:
    mod = obj.modifiers.new("solidify", "SOLIDIFY")
    mod.offset = 0
    mod.thickness = solidify * edge
    mod.use_even_offset = False
    apply_modifier(obj, mod)

voxel = float(p.get("voxel_scale", 5.5)) * edge
mod = obj.modifiers.new("voxel", "REMESH")
mod.mode = "VOXEL"
mod.voxel_size = voxel
mod.use_remove_disconnected = False
apply_modifier(obj, mod)
print(f"clean: edge {edge:.6f} voxel {voxel:.6f} faces {len(obj.data.polygons)}")

min_component = float(p.get("min_component", 0.01))
if min_component > 0:
    drop_small(obj, min_component)

for _ in range(int(p.get("smooth", 0))):
    apply_modifier(obj, obj.modifiers.new("smooth", "SMOOTH"))

export_obj(obj, dst)

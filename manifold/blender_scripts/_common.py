import json
import sys

import bpy


def args():
    argv = sys.argv[sys.argv.index("--") + 1:]
    return argv[:-1], json.loads(argv[-1])


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def override(obj):
    return bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj], selected_editable_objects=[obj])


def join_meshes(path):
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"no mesh in {path}")
    for o in bpy.context.scene.objects:
        o.select_set(o in meshes)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        with bpy.context.temp_override(active_object=meshes[0], selected_editable_objects=meshes):
            bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.select_set(True)
    return obj


def import_obj(path):
    bpy.ops.wm.obj_import(filepath=path)
    return join_meshes(path)


def apply_modifier(obj, mod):
    with override(obj):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def export_obj(obj, path, triangulate=False):
    with override(obj):
        bpy.ops.wm.obj_export(
            filepath=path, export_selected_objects=True, apply_modifiers=True,
            export_triangulated_mesh=triangulate, export_materials=False,
            export_normals=False, export_uv=True,
        )

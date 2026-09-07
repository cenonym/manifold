from comfy_api.latest import IO, Types

from ..core.blender import run_blender
from ..core.config import load_config
from ..core.workdir import new_workdir
from .types import ManifoldMesh, preview_mesh


class FromFile(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ManifoldFromFile",
            display_name="Manifold From File",
            category="manifold",
            description="3D file (glb, gltf, fbx, obj, stl) to a Manifold mesh file.",
            inputs=[
                IO.MultiType.Input(
                    IO.File3DAny.Input("model_3d"),
                    types=[IO.File3DGLB, IO.File3DGLTF, IO.File3DFBX, IO.File3DOBJ, IO.File3DSTL],
                ),
            ],
            outputs=[
                ManifoldMesh.Output(display_name="mesh"),
                IO.Mesh.Output(display_name="preview"),
            ],
        )

    @classmethod
    def execute(cls, model_3d: Types.File3D) -> IO.NodeOutput:
        work = new_workdir("file")
        fmt = (model_3d.format or "").lower()
        if model_3d.is_disk_backed:
            src = str(model_3d.get_source())
        else:
            src = model_3d.save_to(str(work / f"input.{fmt}"))
        out = work / "mesh.obj"
        run_blender(load_config(), "convert.py", [src, str(out)], {}, expect=out)
        return IO.NodeOutput(str(out), preview_mesh(out))

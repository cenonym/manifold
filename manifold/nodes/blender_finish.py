from comfy_api.latest import IO

from ..core.blender import run_blender
from ..core.config import load_config
from ..core.workdir import new_workdir
from .types import ManifoldMesh, preview_mesh


class BlenderFinish(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ManifoldBlenderFinish",
            display_name="Blender Finish",
            category="manifold",
            description="Apply transforms, origin to base, scale to height, optional triangulate and smart UV.",
            inputs=[
                ManifoldMesh.Input("mesh"),
                IO.Float.Input("target_height", default=0.0, min=0.0, max=1000.0, step=0.1, tooltip="0 keeps size"),
                IO.Boolean.Input("triangulate", default=False),
                IO.Boolean.Input("smart_uv", default=False),
                IO.Float.Input("uv_angle", default=66.0, min=1.0, max=89.0, step=1.0),
                IO.Float.Input("uv_margin", default=0.02, min=0.0, max=0.5, step=0.005),
            ],
            outputs=[ManifoldMesh.Output(display_name="mesh"), IO.Mesh.Output(display_name="preview")],
        )

    @classmethod
    def execute(cls, mesh, target_height, triangulate, smart_uv, uv_angle, uv_margin) -> IO.NodeOutput:
        out = new_workdir("finish") / "finish.obj"
        params = {"target_height": target_height, "triangulate": triangulate, "smart_uv": smart_uv, "uv_angle": uv_angle, "uv_margin": uv_margin}
        run_blender(load_config(), "finish.py", [mesh, str(out)], params, expect=out)
        return IO.NodeOutput(str(out), preview_mesh(out))

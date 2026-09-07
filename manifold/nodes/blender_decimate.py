from comfy_api.latest import IO

from ..core.blender import run_blender
from ..core.config import load_config
from ..core.workdir import new_workdir
from .types import ManifoldMesh, preview_mesh


class BlenderDecimate(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ManifoldBlenderDecimate",
            display_name="Blender Decimate",
            category="manifold",
            description="Planar (angle) or collapse (ratio) decimation in headless Blender.",
            inputs=[
                ManifoldMesh.Input("mesh"),
                IO.Combo.Input("mode", options=["planar", "collapse"], default="planar"),
                IO.Float.Input("angle", default=5.0, min=0.0, max=90.0, step=0.5, tooltip="planar: dissolve angle in degrees"),
                IO.Float.Input("ratio", default=0.5, min=0.01, max=1.0, step=0.01, tooltip="collapse: kept face ratio"),
                IO.Int.Input("target_faces", default=0, min=0, max=5_000_000, step=1000, tooltip="collapse: face count, 0 uses ratio"),
            ],
            outputs=[ManifoldMesh.Output(display_name="mesh"), IO.Mesh.Output(display_name="preview")],
        )

    @classmethod
    def execute(cls, mesh, mode, angle, ratio, target_faces) -> IO.NodeOutput:
        out = new_workdir("decimate") / "decimate.obj"
        run_blender(load_config(), "decimate.py", [mesh, str(out)], {"mode": mode, "angle": angle, "ratio": ratio, "target_faces": target_faces}, expect=out)
        return IO.NodeOutput(str(out), preview_mesh(out))

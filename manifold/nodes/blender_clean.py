from comfy_api.latest import IO

from ..core.blender import run_blender
from ..core.config import load_config
from ..core.workdir import new_workdir
from .types import ManifoldMesh, preview_mesh


class BlenderClean(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ManifoldBlenderClean",
            display_name="Blender Clean",
            category="manifold",
            description="Voxel remesh to a closed manifold surface, then drop loose parts and optionally smooth.",
            inputs=[
                ManifoldMesh.Input("mesh"),
                IO.Int.Input("voxel_divisions", default=216, min=32, max=1024, step=8, tooltip="voxel size = longest side / divisions; above ~236 the double shell fragments"),
                IO.Float.Input("min_component", default=0.01, min=0.0, max=1.0, step=0.005, tooltip="drop parts smaller than this fraction of the largest"),
                IO.Int.Input("smooth", default=0, min=0, max=20),
            ],
            outputs=[ManifoldMesh.Output(display_name="mesh"), IO.Mesh.Output(display_name="preview")],
        )

    @classmethod
    def execute(cls, mesh, voxel_divisions, min_component, smooth) -> IO.NodeOutput:
        out = new_workdir("clean") / "clean.obj"
        run_blender(
            load_config(), "clean.py", [mesh, str(out)],
            {"voxel_divisions": voxel_divisions, "min_component": min_component, "smooth": smooth},
            expect=out,
        )
        return IO.NodeOutput(str(out), preview_mesh(out))

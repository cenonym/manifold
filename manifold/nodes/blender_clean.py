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
                IO.Float.Input("voxel_scale", default=3.0, min=1.0, max=8.0, step=0.1, tooltip="voxel size as a multiple of the median edge length; the double shell splits below about 2.8, larger smooths"),
                IO.Float.Input("min_component", default=0.01, min=0.0, max=1.0, step=0.005, tooltip="drop parts smaller than this fraction of the largest"),
                IO.Int.Input("smooth", default=0, min=0, max=20),
                IO.Float.Input("solidify", default=1.5, min=0.0, max=4.0, step=0.1, tooltip="thickness as a multiple of the median edge length before remeshing, closes open sheets, 0 off"),
            ],
            outputs=[ManifoldMesh.Output(display_name="mesh"), IO.Mesh.Output(display_name="preview")],
        )

    @classmethod
    def execute(cls, mesh, voxel_scale, min_component, smooth, solidify) -> IO.NodeOutput:
        out = new_workdir("clean") / "clean.obj"
        run_blender(
            load_config(), "clean.py", [mesh, str(out)],
            {"voxel_scale": voxel_scale, "min_component": min_component, "smooth": smooth, "solidify": solidify},
            expect=out,
        )
        return IO.NodeOutput(str(out), preview_mesh(out))

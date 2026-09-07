from pathlib import Path

from comfy_api.latest import IO

from ..core.autoremesher import RemeshParams, quad_remesh
from ..core.config import load_config
from ..core.workdir import new_workdir
from .types import ManifoldMesh, preview_mesh

REPORT_KEYS = ["quads", "non-quads", "vertices", "total_time"]


class QuadRemesh(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ManifoldQuadRemesh",
            display_name="Quad Remesh",
            category="manifold",
            description="AutoRemesher quad retopology.",
            inputs=[
                ManifoldMesh.Input("mesh"),
                IO.Int.Input("target_quads", default=5000, min=100, max=1_000_000, step=100),
                IO.Float.Input("adaptivity", default=1.0, min=0.0, max=1.0, step=0.05),
                IO.Float.Input("anisotropy", default=1.0, min=0.0, max=1.0, step=0.05),
                IO.Float.Input("sharp_edge", default=90.0, min=30.0, max=180.0, step=1.0),
                IO.Float.Input("smooth_normal", default=0.0, min=0.0, max=180.0, step=1.0),
                IO.Float.Input("edge_scaling", default=1.0, min=1.0, max=4.0, step=0.1),
            ],
            outputs=[
                ManifoldMesh.Output(display_name="mesh"),
                IO.Mesh.Output(display_name="preview"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, mesh, target_quads, adaptivity, anisotropy, sharp_edge, smooth_normal, edge_scaling) -> IO.NodeOutput:
        out = new_workdir("quad") / "quad.obj"
        params = RemeshParams(
            target_quads=target_quads, edge_scaling=edge_scaling, sharp_edge=sharp_edge,
            smooth_normal=smooth_normal, adaptivity=adaptivity, anisotropy=anisotropy,
        )
        report = quad_remesh(load_config(), Path(mesh), out, params)
        shown = {k: report[k] for k in REPORT_KEYS if k in report} or report
        info = ", ".join(f"{k} {v}" for k, v in shown.items()) or "no report"
        return IO.NodeOutput(str(out), preview_mesh(out), info)

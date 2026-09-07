import gc

import comfy.model_management
from comfy_api.latest import IO

from .types import ManifoldMesh


class FreeModels(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ManifoldFreeModels",
            display_name="Free Models",
            category="manifold",
            description="Unload every model so the retopo stage runs with memory free.",
            inputs=[ManifoldMesh.Input("mesh")],
            outputs=[ManifoldMesh.Output(display_name="mesh")],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return float("nan")

    @classmethod
    def execute(cls, mesh) -> IO.NodeOutput:
        comfy.model_management.unload_all_models()
        comfy.model_management.soft_empty_cache()
        gc.collect()
        return IO.NodeOutput(mesh)

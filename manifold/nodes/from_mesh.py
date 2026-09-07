from comfy_api.latest import IO

from ..core.workdir import new_workdir
from .convert import first_item, mesh_to_obj
from .types import ManifoldMesh


class FromMesh(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ManifoldFromMesh",
            display_name="Manifold From Mesh",
            category="manifold",
            description="Native Mesh (first batch item) to a Manifold mesh file.",
            inputs=[IO.Mesh.Input("mesh")],
            outputs=[ManifoldMesh.Output(display_name="mesh")],
        )

    @classmethod
    def execute(cls, mesh) -> IO.NodeOutput:
        v, f = first_item(mesh.vertices, mesh.faces, mesh.vertex_counts, mesh.face_counts)
        path = new_workdir("from") / "mesh.obj"
        mesh_to_obj(v, f, path)
        return IO.NodeOutput(str(path))

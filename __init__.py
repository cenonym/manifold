from comfy_api.latest import IO, ComfyExtension
from typing_extensions import override

from .manifold.core.workdir import purge_workdirs
from .manifold.nodes import load_nodes


class ManifoldExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[IO.ComfyNode]]:
        return load_nodes()


async def comfy_entrypoint() -> ManifoldExtension:
    purge_workdirs()
    return ManifoldExtension()

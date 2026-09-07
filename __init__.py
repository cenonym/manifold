import logging

from comfy_api.latest import IO, ComfyExtension
from typing_extensions import override

from .manifold.core.config import ConfigError
from .manifold.core.workdir import purge_workdirs
from .manifold.nodes import load_nodes


class ManifoldExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[IO.ComfyNode]]:
        return load_nodes()


async def comfy_entrypoint() -> ManifoldExtension:
    purge_workdirs()
    try:
        from .manifold.compat.mps_hashmap import install as install_hashmap
        from .manifold.compat.mps_int8 import install as install_int8
        from .manifold.core.config import load_config

        cfg = load_config()
        if cfg.mps_int8_bf16:
            install_int8()
        if cfg.mps_hashmap_sort:
            install_hashmap()
    except ConfigError:
        pass
    except Exception:
        logging.exception("manifold: mps shims not installed")
    return ManifoldExtension()

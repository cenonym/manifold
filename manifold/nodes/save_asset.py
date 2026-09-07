from pathlib import Path

import numpy as np
from comfy_api.latest import IO
from PIL import Image

from ..core.asset import new_version_dir, sha256_file, write_sidecar
from ..core.autoremesher import autoremesher_version
from ..core.blender import blender_version, run_blender
from ..core.config import load_config
from ..core.mesh import face_stats, read_obj
from .types import ManifoldMesh

VERSION = "0.1.0"


class SaveAsset(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ManifoldSaveAsset",
            display_name="Save Asset",
            category="manifold",
            description="Write <output_root>/<name>/v<N>/ with glb, fbx, obj, source image and manifold.json.",
            inputs=[
                ManifoldMesh.Input("mesh"),
                IO.String.Input("name", default="asset", tooltip="[a-z0-9_]+"),
                IO.Image.Input("source", optional=True),
                IO.String.Input("note", default="", multiline=True, optional=True),
            ],
            outputs=[IO.String.Output(display_name="asset_dir")],
            hidden=[IO.Hidden.prompt],
            is_output_node=True,
        )

    @classmethod
    def execute(cls, mesh, name, source=None, note="") -> IO.NodeOutput:
        config = load_config()
        version_dir = new_version_dir(config.output_root, name)
        v, f = read_obj(Path(mesh))
        run_blender(config, "export.py", [mesh, str(version_dir)], {"name": name}, expect=version_dir / f"{name}.glb")
        fields = {
            "name": name,
            "note": note,
            "manifold": VERSION,
            "tools": {"blender": blender_version(config), "autoremesher": autoremesher_version(config)},
            "counts": {"vertices": len(v), **face_stats(f)},
            "prompt": cls.hidden.prompt,
        }
        if source is not None:
            img = (source[0].detach().cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
            Image.fromarray(img).save(version_dir / "source.png")
            fields["source_sha256"] = sha256_file(version_dir / "source.png")
        write_sidecar(version_dir, **fields)
        return IO.NodeOutput(str(version_dir))

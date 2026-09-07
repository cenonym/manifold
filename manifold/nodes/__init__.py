def load_nodes() -> list:
    from .blender_clean import BlenderClean
    from .blender_decimate import BlenderDecimate
    from .blender_finish import BlenderFinish
    from .free_models import FreeModels
    from .from_file import FromFile
    from .from_mesh import FromMesh
    from .quad_remesh import QuadRemesh
    from .save_asset import SaveAsset

    return [FromMesh, FromFile, FreeModels, BlenderClean, QuadRemesh, BlenderDecimate, BlenderFinish, SaveAsset]

import inspect
import logging

_FLAG = "_manifold_hashmap_mps_patched"


def _require(cond: bool, what: str) -> None:
    if not cond:
        raise RuntimeError(f"manifold mps hashmap shim: comfyui changed, {what}")


def install() -> bool:
    import torch

    import comfy.ldm.trellis2.flexgemm as flexgemm
    import comfy.model_management

    if getattr(flexgemm, _FLAG, False):
        return True
    if not comfy.model_management.is_device_mps(comfy.model_management.get_torch_device()):
        return False

    cls = getattr(flexgemm, "TorchHashMap", None)
    _require(cls is not None, "flexgemm.TorchHashMap is missing")
    original = getattr(cls, "__init__", None)
    _require(callable(original), "TorchHashMap.__init__ is missing")
    src = inspect.getsource(original)
    _require("torch.sort" in src, "TorchHashMap.__init__ no longer calls torch.sort")
    for attr in ("sorted_keys", "sorted_vals", "_n"):
        _require(attr in src, f"TorchHashMap.__init__ no longer sets {attr}")
    _require(callable(getattr(cls, "lookup_flat", None)), "TorchHashMap.lookup_flat is missing")

    def patched(self, keys: torch.Tensor, values: torch.Tensor):
        keys = keys.to(torch.long)
        order = torch.argsort(keys)
        self.sorted_keys = keys[order]
        self.sorted_vals = values.to(torch.long)[order]
        self._n = self.sorted_keys.numel()

    cls.__init__ = patched
    setattr(flexgemm, _FLAG, True)
    logging.info("manifold: trellis hashmap keys sorted via argsort on mps")
    return True

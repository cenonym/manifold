import logging

INT8_FORMATS = ("int8_tensorwise", "convrot_w4a4", "asym_w4a8_int8")
_FLAG = "_manifold_int8_mps_patched"


def _require(cond: bool, what: str) -> None:
    if not cond:
        raise RuntimeError(f"manifold mps int8 shim: comfyui changed, {what}")


def install() -> bool:
    import torch

    import comfy.model_management
    import comfy.ops
    from comfy.quant_ops import QUANT_ALGOS, QuantizedTensor

    if getattr(comfy.ops, _FLAG, False):
        return True
    if not comfy.model_management.is_device_mps(comfy.model_management.get_torch_device()):
        return False

    _require(callable(getattr(comfy.ops, "mixed_precision_ops", None)), "comfy.ops.mixed_precision_ops is missing")
    _require(callable(getattr(comfy.ops, "pick_operations", None)), "comfy.ops.pick_operations is missing")
    missing = [f for f in INT8_FORMATS if f not in QUANT_ALGOS]
    _require(not missing, f"QUANT_ALGOS lacks {', '.join(missing)}")

    original = comfy.ops.mixed_precision_ops
    probe = original({}, torch.bfloat16, False, [])
    _require(hasattr(probe, "Linear"), "mixed_precision_ops result has no Linear")
    _require(callable(getattr(probe.Linear, "_load_from_state_dict", None)), "Linear._load_from_state_dict is missing")
    _require("layout_type" in probe.Linear.forward.__code__.co_names, "Linear.forward no longer reads layout_type")

    def patched(quant_config={}, compute_dtype=torch.bfloat16, full_precision_mm=False, disabled=[]):
        ops = original(quant_config, compute_dtype, full_precision_mm, set(disabled) | set(INT8_FORMATS))
        inner = ops.Linear._load_from_state_dict

        def load(self, *args, **kwargs):
            inner(self, *args, **kwargs)
            weight = getattr(self, "weight", None)
            data = weight.data if isinstance(weight, torch.nn.Parameter) else weight
            if isinstance(data, QuantizedTensor) and getattr(self, "quant_format", None) in INT8_FORMATS:
                plain = data.dequantize().to(dtype=compute_dtype).contiguous()
                self.weight = torch.nn.Parameter(plain, requires_grad=False)
                self.layout_type = None
                self.quant_format = None
                self._full_precision_mm = True

        ops.Linear._load_from_state_dict = load
        return ops

    comfy.ops.mixed_precision_ops = patched
    setattr(comfy.ops, _FLAG, True)
    logging.info("manifold: int8 weights materialize to bf16 on mps")
    return True

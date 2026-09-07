import json
import os
import sys
from pathlib import Path

import pytest

COMFY = Path.home() / "ComfyUI-Installs/ComfyUI/ComfyUI"
pytestmark = pytest.mark.skipif(not COMFY.is_dir(), reason="ComfyUI tree not present")


@pytest.fixture(scope="module")
def comfy():
    cwd = os.getcwd()
    sys.path.insert(0, str(COMFY))
    os.chdir(COMFY)
    try:
        import comfy.model_management
        import comfy.ops

        yield comfy
    finally:
        os.chdir(cwd)
        sys.path.remove(str(COMFY))


@pytest.fixture(scope="module")
def installed(comfy):
    from manifold.compat.mps_int8 import install

    return install, install()


def test_install_returns_true_on_mps(comfy, installed):
    import torch

    install, ok = installed
    if not torch.backends.mps.is_available():
        pytest.skip("no mps")
    assert ok is True
    assert install() is True


def test_int8_linear_materializes_to_bf16(comfy, installed):
    import torch

    if not torch.backends.mps.is_available():
        pytest.skip("no mps")
    assert "PYTORCH_ENABLE_MPS_FALLBACK" not in os.environ

    import numpy as np
    from comfy.quant_ops import QuantizedTensor

    torch.manual_seed(0)
    out_f, in_f = 256, 128
    ref = torch.randn(out_f, in_f, dtype=torch.bfloat16)
    scale = (ref.abs().max().to(torch.float32) / 127.0).reshape(1)
    qdata = (ref.to(torch.float32) / scale).round().clamp(-127, 127).to(torch.int8)

    conf = json.dumps({"format": "int8_tensorwise"}).encode()
    state = {
        "weight": qdata,
        "weight_scale": scale,
        "comfy_quant": torch.from_numpy(np.frombuffer(conf, dtype=np.uint8).copy()),
    }

    class ModelConfig:
        quant_config = {"layers": {"lin": {"format": "int8_tensorwise"}}}

    ops = comfy.ops.pick_operations(torch.bfloat16, torch.bfloat16, model_config=ModelConfig())
    device = torch.device("mps")
    lin = ops.Linear(in_f, out_f, bias=False, device=device, dtype=torch.bfloat16)
    lin._load_from_state_dict(state, "", {}, True, [], [], [])

    assert not isinstance(lin.weight.data, QuantizedTensor)
    assert lin.weight.dtype == torch.bfloat16

    x = torch.randn(64, in_f, dtype=torch.bfloat16, device=device)
    got = lin(x).float()
    want = torch.nn.functional.linear(x, ref.to(device)).float()
    err = ((got - want).abs().max() / want.abs().max()).item()
    print(f"relative max error vs bf16 reference: {err:.6f}")
    assert 0.0 < err < 0.02

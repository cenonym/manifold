import os
import sys
from pathlib import Path

import pytest

COMFY = Path.home() / "ComfyUI-Installs/ComfyUI/ComfyUI"
pytestmark = pytest.mark.skipif(not COMFY.is_dir(), reason="ComfyUI tree not present")

N_KEYS = 100_000
KEY_MAX = 200_000_000


@pytest.fixture(scope="module")
def comfy():
    cwd = os.getcwd()
    sys.path.insert(0, str(COMFY))
    os.chdir(COMFY)
    try:
        import comfy.ldm.trellis2.flexgemm
        import comfy.model_management

        yield comfy
    finally:
        os.chdir(cwd)
        sys.path.remove(str(COMFY))


def random_keys(torch, device):
    torch.manual_seed(0)
    keys = torch.randperm(KEY_MAX, dtype=torch.int64)[:N_KEYS]
    return keys.to(device)


def hit_rate(hashmap, keys):
    return (hashmap.lookup_flat(keys) >= 0).float().mean().item()


def sphere_voxels(torch, res, device):
    r = torch.arange(res, dtype=torch.float32)
    g = torch.stack(torch.meshgrid(r, r, r, indexing="ij"), dim=-1)
    c = (res - 1) / 2.0
    d = (g - c).pow(2).sum(-1).sqrt()
    mask = (d > res * 0.30) & (d < res * 0.36)
    coords = mask.nonzero().to(torch.int32)
    n = coords.shape[0]
    torch.manual_seed(1)
    dual = torch.rand(n, 3) * 0.5 + 0.25
    flag = torch.rand(n, 3) < 0.5
    return coords.to(device), dual.to(device), flag.to(device)


@pytest.fixture(scope="module")
def before_rate(comfy):
    import torch

    if not torch.backends.mps.is_available():
        return None
    from comfy.ldm.trellis2.flexgemm import TorchHashMap

    keys = random_keys(torch, torch.device("mps"))
    vals = torch.arange(N_KEYS, dtype=torch.int32, device="mps")
    return hit_rate(TorchHashMap(keys, vals), keys)


@pytest.fixture(scope="module")
def installed(comfy, before_rate):
    from manifold.compat.mps_hashmap import install

    return install, install()


def test_install_returns_true_on_mps(comfy, installed):
    import torch

    install, ok = installed
    if not torch.backends.mps.is_available():
        pytest.skip("no mps")
    assert ok is True
    assert install() is True


def test_bug_present_before_install(comfy, before_rate):
    import torch

    if not torch.backends.mps.is_available():
        pytest.skip("no mps")
    print(f"hit rate before install: {before_rate:.4f}")
    if before_rate == 1.0:
        pytest.skip("torch.sort on mps no longer corrupts int64 values")
    assert before_rate < 0.9


def test_lookup_after_install(comfy, installed):
    import torch

    if not torch.backends.mps.is_available():
        pytest.skip("no mps")
    from comfy.ldm.trellis2.flexgemm import TorchHashMap

    keys = random_keys(torch, torch.device("mps"))
    vals = torch.arange(N_KEYS, dtype=torch.int32, device="mps")
    hm = TorchHashMap(keys, vals)
    rate = hit_rate(hm, keys)
    print(f"hit rate after install: {rate:.4f}")
    assert rate == 1.0
    assert torch.equal(hm.lookup_flat(keys).long(), vals.long())

    absent = torch.arange(KEY_MAX + 1, KEY_MAX + 1001, dtype=torch.int64, device="mps")
    got = hm.lookup_flat(absent)

    cpu_hm = TorchHashMap(keys.cpu(), vals.cpu())
    want = cpu_hm.lookup_flat(absent.cpu())
    assert torch.equal(got.cpu(), want)
    assert int(got.max().item()) == -1


def test_mesh_extraction_matches_cpu(comfy, installed):
    import torch

    if not torch.backends.mps.is_available():
        pytest.skip("no mps")
    from comfy.ldm.trellis2.vae import flexible_dual_grid_to_mesh

    res = 256
    aabb = [[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]]
    counts = {}
    for device in ("cpu", "mps"):
        coords, dual, flag = sphere_voxels(torch, res, torch.device(device))
        verts, tris = flexible_dual_grid_to_mesh(coords, dual, flag, None, aabb, grid_size=res)
        counts[device] = (verts.shape[0], tris.shape[0])
    print(f"mesh cpu={counts['cpu']} mps={counts['mps']}")
    assert counts["mps"] == counts["cpu"]

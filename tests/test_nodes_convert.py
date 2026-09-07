import numpy as np
import pytest

torch = pytest.importorskip("torch")

from manifold.core.mesh import read_obj
from manifold.nodes.convert import first_item, mesh_to_obj


def test_first_item_batched_tensor():
    v = torch.zeros(2, 4, 3)
    f = torch.tensor([[[0, 1, 2], [0, 2, 3]], [[0, 1, 2], [0, 2, 3]]])
    vv, ff = first_item(v, f, None, None)
    assert vv.shape == (4, 3) and ff.shape == (2, 3) and ff.dtype == np.int64


def test_first_item_padded_counts():
    v = torch.zeros(1, 5, 3)
    f = torch.zeros(1, 3, 3, dtype=torch.int64)
    vv, ff = first_item(v, f, torch.tensor([4]), torch.tensor([2]))
    assert vv.shape == (4, 3) and ff.shape == (2, 3)


def test_first_item_list():
    vv, ff = first_item([torch.zeros(3, 3)], [torch.tensor([[0, 1, 2]])], None, None)
    assert vv.shape == (3, 3) and ff.shape == (1, 3)


def test_first_item_unbatched():
    vv, ff = first_item(torch.zeros(3, 3), torch.tensor([[0, 1, 2]]), None, None)
    assert vv.shape == (3, 3) and ff.shape == (1, 3)


def test_mesh_to_obj_round_trip(tmp_path):
    p = tmp_path / "m.obj"
    mesh_to_obj(np.eye(3, dtype=np.float32), np.array([[0, 1, 2]]), p)
    v, f = read_obj(p)
    assert v.shape == (3, 3) and f == [[0, 1, 2]]

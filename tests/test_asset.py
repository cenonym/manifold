import json

import pytest

from manifold.core.asset import AssetError, new_version_dir, next_version, sha256_file, validate_slug, write_sidecar


@pytest.mark.parametrize("name", ["oak", "oak_tree_01", "a1"])
def test_valid_slugs(name):
    assert validate_slug(name) == name


@pytest.mark.parametrize("name", ["", "Oak", "oak tree", "oak-tree", "../x", "oak/1"])
def test_invalid_slugs(name):
    with pytest.raises(AssetError, match="a-z0-9_"):
        validate_slug(name)


def test_next_version_empty(tmp_path):
    assert next_version(tmp_path / "oak") == 1


def test_next_version_skips_noise(tmp_path):
    d = tmp_path / "oak"
    for n in ["v1", "v3", "vx", "notes"]:
        (d / n).mkdir(parents=True)
    (d / "v9").write_text("file, not dir")
    assert next_version(d) == 4


def test_new_version_dir_increments(tmp_path):
    a = new_version_dir(tmp_path, "oak")
    b = new_version_dir(tmp_path, "oak")
    assert a == tmp_path / "oak" / "v1" and b == tmp_path / "oak" / "v2"
    assert a.is_dir() and b.is_dir()


def test_new_version_dir_validates(tmp_path):
    with pytest.raises(AssetError):
        new_version_dir(tmp_path, "Bad Name")


def test_sha256(tmp_path):
    p = tmp_path / "f"
    p.write_bytes(b"abc")
    assert sha256_file(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_sidecar(tmp_path):
    p = write_sidecar(tmp_path, name="oak", counts={"faces": 6}, note="")
    data = json.loads(p.read_text())
    assert p.name == "manifold.json"
    assert data["name"] == "oak" and data["counts"] == {"faces": 6}
    assert data["created"].endswith("+00:00")

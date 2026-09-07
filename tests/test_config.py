import os
from pathlib import Path

import pytest

from manifold.core.config import Config, ConfigError, load_config, require_tool


def write(tmp_path, body):
    p = tmp_path / "manifold.toml"
    p.write_text(body)
    return p


GOOD = """
[tools]
blender = "/bin/ls"
autoremesher = "~/nope/autoremesher"

[paths]
output_root = "~/Assets/manifold"
"""


def test_loads_and_expands_home(tmp_path):
    cfg = load_config(write(tmp_path, GOOD))
    assert cfg.blender == Path("/bin/ls")
    assert cfg.autoremesher == Path.home() / "nope/autoremesher"
    assert cfg.output_root == Path.home() / "Assets/manifold"


def test_missing_file_names_path(tmp_path):
    with pytest.raises(ConfigError, match="manifold.toml"):
        load_config(tmp_path / "manifold.toml")


def test_missing_key_names_key(tmp_path):
    with pytest.raises(ConfigError, match="autoremesher"):
        load_config(write(tmp_path, '[tools]\nblender = "/bin/ls"\n[paths]\noutput_root = "x"\n'))


def test_env_override(tmp_path, monkeypatch):
    p = write(tmp_path, GOOD)
    monkeypatch.setenv("MANIFOLD_CONFIG", str(p))
    assert load_config().blender == Path("/bin/ls")


def test_require_tool(tmp_path):
    cfg = load_config(write(tmp_path, GOOD))
    assert require_tool(cfg, "blender") == Path("/bin/ls")
    with pytest.raises(ConfigError, match="tools.autoremesher"):
        require_tool(cfg, "autoremesher")


def test_mps_int8_bf16_defaults_true(tmp_path):
    assert load_config(write(tmp_path, GOOD)).mps_int8_bf16 is True


def test_mps_int8_bf16_reads_false(tmp_path):
    body = GOOD + "\n[compat]\nmps_int8_bf16 = false\n"
    assert load_config(write(tmp_path, body)).mps_int8_bf16 is False

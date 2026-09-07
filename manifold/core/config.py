import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    blender: Path
    autoremesher: Path
    output_root: Path
    mps_int8_bf16: bool = True
    mps_hashmap_sort: bool = True


def config_path() -> Path:
    env = os.environ.get("MANIFOLD_CONFIG")
    return Path(env).expanduser() if env else REPO_ROOT / "manifold.toml"


def load_config(path: Path | None = None) -> Config:
    path = path or config_path()
    if not path.is_file():
        raise ConfigError(f"missing {path}, copy manifold.toml.example")
    data = tomllib.loads(path.read_text())
    try:
        return Config(
            blender=Path(data["tools"]["blender"]).expanduser(),
            autoremesher=Path(data["tools"]["autoremesher"]).expanduser(),
            output_root=Path(data["paths"]["output_root"]).expanduser(),
            mps_int8_bf16=bool(data.get("compat", {}).get("mps_int8_bf16", True)),
            mps_hashmap_sort=bool(data.get("compat", {}).get("mps_hashmap_sort", True)),
        )
    except KeyError as e:
        raise ConfigError(f"{path}: missing key {e.args[0]}") from e


def require_tool(config: Config, name: str) -> Path:
    path = getattr(config, name)
    if not (path.is_file() and os.access(path, os.X_OK)):
        raise ConfigError(f"tools.{name} is not executable: {path}")
    return path

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

SLUG = re.compile(r"^[a-z0-9_]+$")


class AssetError(Exception):
    pass


def validate_slug(name: str) -> str:
    if not SLUG.match(name or ""):
        raise AssetError(f"asset name must match [a-z0-9_]+, got {name!r}")
    return name


def next_version(asset_dir: Path) -> int:
    if not asset_dir.is_dir():
        return 1
    versions = [int(p.name[1:]) for p in asset_dir.iterdir() if p.is_dir() and p.name[1:].isdigit() and p.name[0] == "v"]
    return max(versions, default=0) + 1


def new_version_dir(output_root: Path, name: str) -> Path:
    asset_dir = output_root / validate_slug(name)
    version_dir = asset_dir / f"v{next_version(asset_dir)}"
    version_dir.mkdir(parents=True, exist_ok=False)
    return version_dir


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_sidecar(version_dir: Path, **fields) -> Path:
    data = {"created": datetime.now(timezone.utc).isoformat(timespec="seconds"), **fields}
    path = version_dir / "manifold.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=str))
    return path

import os
from dataclasses import dataclass
from pathlib import Path

from .config import Config, require_tool
from .tools import ToolError, run_tool


@dataclass(frozen=True)
class RemeshParams:
    target_quads: int = 50000
    edge_scaling: float = 1.0
    sharp_edge: float = 90.0
    smooth_normal: float = 0.0
    adaptivity: float = 1.0
    anisotropy: float = 1.0


def parse_report(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip().lower().replace(" ", "_")] = value.strip()
    return out


def quad_remesh(config: Config, in_path: Path, out_path: Path, params: RemeshParams, timeout: int = 1800) -> dict[str, str]:
    exe = require_tool(config, "autoremesher")
    report = Path(out_path).with_suffix(".report.txt")
    cmd = [
        str(exe), "-i", str(in_path), "-o", str(out_path), "--report", str(report),
        "--target-quads", str(params.target_quads),
        "--edge-scaling", str(params.edge_scaling),
        "--sharp-edge", str(params.sharp_edge),
        "--smooth-normal", str(params.smooth_normal),
        "--adaptivity", str(params.adaptivity),
        "--anisotropy", str(params.anisotropy),
    ]
    out = run_tool("autoremesher", cmd, timeout, env=os.environ.copy())
    if not Path(out_path).exists():
        raise ToolError(f"autoremesher produced no {out_path}\n{out[-2000:]}")
    return parse_report(report.read_text()) if report.exists() else {}


def autoremesher_version(config: Config) -> str:
    return run_tool("autoremesher", [str(require_tool(config, "autoremesher")), "-v"]).strip()

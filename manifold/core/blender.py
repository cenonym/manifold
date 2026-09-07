import json
from pathlib import Path

from .config import Config, require_tool
from .tools import ToolError, run_tool

SCRIPTS = Path(__file__).resolve().parents[1] / "blender_scripts"


def run_blender(config: Config, script: str, args: list[str], params: dict, expect: Path, timeout: int = 900) -> str:
    blender = require_tool(config, "blender")
    cmd = [
        str(blender), "--background", "--factory-startup", "--python-exit-code", "1",
        "--python", str(SCRIPTS / script), "--", *args, json.dumps(params),
    ]
    out = run_tool("blender", cmd, timeout)
    if not Path(expect).exists():
        raise ToolError(f"blender {script} produced no {expect}\n{out[-2000:]}")
    return out


def blender_version(config: Config) -> str:
    return run_tool("blender", [str(require_tool(config, "blender")), "--version"]).splitlines()[0].strip()

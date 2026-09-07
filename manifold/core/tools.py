import subprocess


class ToolError(Exception):
    pass


def run_tool(name: str, cmd: list[str], timeout: int = 900, env: dict | None = None) -> str:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired as e:
        raise ToolError(f"{name} timed out after {timeout}s") from e
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or proc.stdout).splitlines()[-20:])
        raise ToolError(f"{name} exited {proc.returncode}\n{tail}")
    return proc.stdout

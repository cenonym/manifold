import sys

import pytest

from manifold.core.tools import ToolError, run_tool


def test_returns_stdout():
    assert run_tool("py", [sys.executable, "-c", "print('hi')"]).strip() == "hi"


def test_failure_carries_name_code_and_stderr_tail():
    lines = "\n".join(f"line{i}" for i in range(30))
    code = f"import sys; sys.stderr.write({lines!r}); sys.exit(3)"
    with pytest.raises(ToolError) as e:
        run_tool("py", [sys.executable, "-c", code])
    msg = str(e.value)
    assert "py exited 3" in msg and "line29" in msg and "line5" not in msg


def test_timeout():
    with pytest.raises(ToolError, match="timed out"):
        run_tool("py", [sys.executable, "-c", "import time; time.sleep(5)"], timeout=1)

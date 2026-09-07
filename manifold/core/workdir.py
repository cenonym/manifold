import shutil
import tempfile
import time
from pathlib import Path

WORK_ROOT = Path(tempfile.gettempdir()) / "manifold"


def new_workdir(label: str) -> Path:
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f"{label}-", dir=WORK_ROOT))


def purge_workdirs(max_age_hours: float = 24) -> int:
    if not WORK_ROOT.is_dir():
        return 0
    cutoff = time.time() - max_age_hours * 3600
    removed = 0
    for d in WORK_ROOT.iterdir():
        if d.is_dir() and d.stat().st_mtime < cutoff:
            shutil.rmtree(d, ignore_errors=True)
            removed += 1
    return removed

import os
import time

from manifold.core import workdir


def test_new_workdir_is_unique_under_root(tmp_path, monkeypatch):
    monkeypatch.setattr(workdir, "WORK_ROOT", tmp_path / "manifold")
    a, b = workdir.new_workdir("quad"), workdir.new_workdir("quad")
    assert a != b and a.parent == tmp_path / "manifold" and a.name.startswith("quad-")


def test_purge_removes_only_old(tmp_path, monkeypatch):
    monkeypatch.setattr(workdir, "WORK_ROOT", tmp_path / "manifold")
    old, fresh = workdir.new_workdir("a"), workdir.new_workdir("b")
    stale = time.time() - 48 * 3600
    os.utime(old, (stale, stale))
    assert workdir.purge_workdirs(max_age_hours=24) == 1
    assert not old.exists() and fresh.exists()


def test_purge_without_root(tmp_path, monkeypatch):
    monkeypatch.setattr(workdir, "WORK_ROOT", tmp_path / "missing")
    assert workdir.purge_workdirs() == 0

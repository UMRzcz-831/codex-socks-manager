from __future__ import annotations

from types import SimpleNamespace

import pytest

from codex_socks_manager import operations, recovery
from codex_socks_manager.appserver import AppServerProcess
from codex_socks_manager.operations import Manager, switch
from codex_socks_manager.profiles import ProfileStore
from codex_socks_manager.storage import Settings, atomic_write


@pytest.mark.parametrize("failure", [None, "validation", "start", "rollback"])
def test_switch_outcomes_and_stages(manager_paths, monkeypatch, failure):
    store = ProfileStore(manager_paths)
    store.add("old", "http://proxy.example:8080")
    store.add("new", "socks5://proxy.example:1080")
    store.set_active("old")
    roles = [AppServerProcess(101, ("/fake/codex", "app-server"))]
    monkeypatch.setattr(operations, "discover_appservers", lambda paths: roles)
    monkeypatch.setattr(operations, "stop_processes", lambda roles: None)
    starts = []

    def start(paths, roles):
        starts.append(1)
        failed = failure == "start" and len(starts) == 1 or failure == "rollback" and len(starts) == 2
        return [SimpleNamespace(poll=lambda: 1 if failed else None)]

    monkeypatch.setattr(operations, "start_processes", start)
    monkeypatch.setattr(operations, "check", lambda paths: SimpleNamespace(ok=failure is None, category="proxy_transport"))
    stages = []
    if failure:
        with pytest.raises(RuntimeError):
            switch(manager_paths, "new", progress=stages.append)
        assert Settings.load(manager_paths.settings).active == "old"
        assert stages[-1] == ("rollback_failed" if failure == "rollback" else "rolled_back")
    else:
        switch(manager_paths, "new", progress=stages.append)
        assert Settings.load(manager_paths.settings).active == "new"
        assert stages == ["selecting", "restarting", "validating"]


def test_force_delete_keeps_profile_on_failed_switch(manager_paths, monkeypatch):
    manager = Manager(manager_paths)
    manager.store.add("office", "http://proxy.example:8080")
    manager.store.set_active("office")

    def fail(*args, **kwargs):
        raise RuntimeError("validation failed")

    monkeypatch.setattr(operations, "switch", fail)
    with pytest.raises(RuntimeError):
        manager.execute("del", name="office", force=True)
    assert manager.store.get("office")
    assert manager.active == "office"


@pytest.mark.parametrize("rollback_fails", [False, True])
def test_safe_update_reports_actual_recovery(manager_paths, monkeypatch, rollback_fails):
    manager = Manager(manager_paths)
    settings = Settings.load(manager_paths.settings)
    settings.real_codex = "/fake/codex"
    atomic_write(manager_paths.settings, settings.dump())
    monkeypatch.setattr(recovery, "backup", lambda *args: SimpleNamespace(path=manager_paths.backups / "fake"))
    monkeypatch.setattr(recovery.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1))

    def restore(*args, **kwargs):
        if rollback_fails:
            raise RuntimeError("recovery failed")

    monkeypatch.setattr(recovery, "restore", restore)
    stages = []
    with pytest.raises(RuntimeError):
        recovery.safe_update(manager_paths, progress=stages.append)
    assert stages[-1] == ("rollback_failed" if rollback_fails else "rolled_back")


def test_editor_save_and_legacy_defaults_use_injected_home(manager_paths, monkeypatch):
    manager = Manager(manager_paths)
    home = manager_paths.launcher.parents[2]
    inputs = []
    monkeypatch.setattr(operations, "migrate_legacy", lambda paths, sources: inputs.append(sources) or [])
    manager.execute("migrate-legacy")
    assert inputs == [{"jp": home / ".config/openai-proxy/jp.env", "us": home / ".config/openai-proxy/us.env"}]
    manager.store.add("office", "http://proxy.example:8080")
    with pytest.raises(ValueError):
        manager.execute("edit", name="office", url="ftp://proxy.example:21")
    assert manager.store.get("office") == "http://proxy.example:8080"

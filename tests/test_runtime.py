from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from codex_socks_manager.appserver import discover_appservers
from codex_socks_manager.appserver import AppServerProcess
from codex_socks_manager.cli import _switch
from codex_socks_manager.doctor import evaluate_doctor
from codex_socks_manager.runtime import CodexInstall, discover_codex, install_launcher, merge_no_proxy, proxy_environment
from codex_socks_manager.storage import Settings, atomic_write, initialize
from codex_socks_manager.profiles import ProfileStore


def executable(path: Path, content: str = "#!/bin/sh\nexit 0\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.mark.parametrize("layout,source", [
    (".codex/packages/standalone/current/bin/codex", "standalone"),
    (".local/lib/node_modules/@openai/codex/bin/codex", "npm"),
    (".local/share/pnpm/codex", "pnpm"),
])
def test_discover_install_sources(manager_paths, tmp_path, layout, source):
    home = manager_paths.launcher.parents[2]
    candidate = executable(home / layout)
    env = {"HOME": str(home), "PATH": str(candidate.parent)}
    found = discover_codex(manager_paths, env)
    assert found.executable == candidate.resolve()
    assert found.source == source


def test_launcher_is_non_recursive_and_forwards_arguments(manager_paths, tmp_path):
    real = executable(tmp_path / "standalone/bin/codex")
    settings = install_launcher(manager_paths, CodexInstall(real, "standalone"))
    launcher = manager_paths.launcher.read_text(encoding="utf-8")
    assert settings.real_codex == str(real)
    assert "exec " in launcher and '"$@"' in launcher
    assert "PYTHONPATH=" in launcher
    assert str(manager_paths.launcher) not in settings.real_codex
    manager_paths.launcher.unlink()
    manager_paths.launcher.symlink_to(tmp_path / "overwritten")
    install_launcher(manager_paths)
    assert not manager_paths.launcher.is_symlink()


def test_launcher_rediscovers_updated_standalone_target(manager_paths, tmp_path):
    home = manager_paths.launcher.parents[2]
    version_one = executable(tmp_path / "v1/codex")
    current = home / ".codex/packages/standalone/current/bin/codex"
    current.parent.mkdir(parents=True)
    current.symlink_to(version_one)
    install_launcher(manager_paths)
    version_two = executable(tmp_path / "v2/codex")
    current.unlink()
    current.symlink_to(version_two)
    settings = install_launcher(manager_paths)
    assert settings.real_codex == str(version_two)


def test_proxy_environment_and_no_proxy():
    source = {"NO_PROXY": "metadata.internal,localhost", "HTTP_PROXY": "old"}
    env = proxy_environment(source, "socks5h://proxy.test:1080")
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        assert env[key] == "socks5h://proxy.test:1080"
    assert merge_no_proxy("localhost,metadata.internal") == "localhost,127.0.0.1,::1,metadata.internal"
    off = proxy_environment(env, None)
    assert not any(key in off for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"))


def doctor_payload(https="ok", wss=101, app="ok", env="ok", detail=""):
    return {"checks": [
        {"name": "provider_reachability", "status": https, "detail": detail},
        {"name": "websocket_reachability", "status": "ok" if wss == 101 else "failed", "http_status": wss},
        {"name": "app_server.status", "status": app},
        {"name": "network.env", "status": env},
    ]}


def test_doctor_success_and_failures():
    assert evaluate_doctor(doctor_payload()).ok
    result = evaluate_doctor(doctor_payload(wss=200))
    assert not result.ok and result.wss != "101"
    transport = evaluate_doctor(doctor_payload(https="failed", detail="HTTP 403 from proxy"))
    assert transport.category == "proxy_transport"
    auth = evaluate_doctor(doctor_payload(https="failed", detail="HTTP 403 workspace permission denied"))
    assert auth.category == "authorization"


def test_appserver_discovery_matches_uid_real_binary_only(manager_paths, tmp_path):
    initialize(manager_paths)
    real = executable(tmp_path / "real-codex")
    settings = Settings(real_codex=str(real))
    atomic_write(manager_paths.settings, settings.dump())
    proc = tmp_path / "proc"
    own = proc / "101"
    unrelated = proc / "102"
    own.mkdir(parents=True)
    unrelated.mkdir(parents=True)
    (own / "cmdline").write_bytes(str(real).encode() + b"\0app-server\0proxy\0")
    (unrelated / "cmdline").write_bytes(b"/usr/bin/python\0app-server\0")
    found = discover_appservers(manager_paths, proc_root=proc, uid=os.getuid())
    assert [process.pid for process in found] == [101]


def test_switch_failure_rolls_back_profile_and_roles(manager_paths, monkeypatch):
    store = ProfileStore(manager_paths)
    store.add("jp", "http://proxy.test:8080")
    role = AppServerProcess(101, ("/fake/codex", "app-server", "proxy"))
    discoveries = iter([[role], []])
    started = []

    class Process:
        def poll(self):
            return None

    monkeypatch.setattr("codex_socks_manager.operations.discover_appservers", lambda paths: next(discoveries))
    monkeypatch.setattr("codex_socks_manager.operations.stop_processes", lambda roles: None)
    monkeypatch.setattr("codex_socks_manager.operations.start_processes", lambda paths, roles: started.append(roles) or [Process()])
    monkeypatch.setattr(
        "codex_socks_manager.operations.check",
        lambda paths: type("Result", (), {"ok": False, "category": "proxy_transport"})(),
    )
    with pytest.raises(RuntimeError):
        _switch(manager_paths, "jp", True)
    assert Settings.load(manager_paths.settings).active == "off"
    assert started == [[role], [role]]

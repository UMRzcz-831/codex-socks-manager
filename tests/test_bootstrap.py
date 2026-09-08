from __future__ import annotations

import os
import subprocess
import sys
import json
from pathlib import Path

import pytest

from codex_socks_manager import bootstrap
from codex_socks_manager.storage import Settings, atomic_write


@pytest.fixture
def bootstrap_env(manager_paths, tmp_path, monkeypatch):
    home = manager_paths.launcher.parents[2]
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(manager_paths.config.parent))
    monkeypatch.setenv("XDG_STATE_HOME", str(manager_paths.state.parent))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    return home, tmp_path / "data/codex-socks-manager"


@pytest.mark.parametrize("failure", ["venv", "pip", "preflight", "publish", None])
@pytest.mark.parametrize("with_tui", [False, True])
def test_upgrade_preserves_old_install_on_failure(manager_paths, bootstrap_env, monkeypatch, failure, with_tui):
    home, root = bootstrap_env
    manager = home / ".local/bin/codex-socks"
    guard = home / ".local/bin/codex-proxy-guard"
    for target in (manager, guard, manager_paths.launcher, manager_paths.settings):
        atomic_write(target, "previous\n", 0o700 if target != manager_paths.settings else 0o600)
    calls = []

    def run(argv, **kwargs):
        stage = "venv" if argv[1:3] == ["-m", "venv"] else (
            "pip" if argv[1:3] == ["-m", "pip"] else "preflight" if argv[1] == "-c" else "publish")
        calls.append(stage)
        assert "PYTHONPATH" not in kwargs["env"]
        if stage == "pip":
            assert argv[-1].endswith("[tui]") == with_tui
        if stage == "preflight":
            assert ("ManagerApp" in argv[-1]) == with_tui
        if stage == "publish":
            atomic_write(manager_paths.launcher, "new launcher\n", 0o700)
            atomic_write(manager_paths.settings, "new settings\n")
        if stage == failure:
            raise subprocess.CalledProcessError(1, argv)
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(bootstrap.subprocess, "run", run)
    if failure:
        with pytest.raises((RuntimeError, subprocess.CalledProcessError)):
            bootstrap.install(Path("/fake/project"), with_tui=with_tui)
        for target in (manager, guard, manager_paths.launcher, manager_paths.settings):
            assert target.read_text() == "previous\n"
        assert manager.stat().st_mode & 0o777 == 0o700
    else:
        environment = bootstrap.install(Path("/fake/project"), with_tui=with_tui)
        assert str(environment / "bin/python") in manager.read_text()
        assert environment.parent == root / "venvs"
        assert "codex-socks" in guard.read_text()
        assert list(manager_paths.state.glob("bootstrap-backups/install-*"))
    assert calls[0] == "venv"
    assert list((root / "venvs").iterdir())


def test_first_install_and_successive_versioned_environments(manager_paths, bootstrap_env, monkeypatch):
    home, root = bootstrap_env
    monkeypatch.setattr(bootstrap.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0))
    first = bootstrap.install(Path("/fake/project"))
    second = bootstrap.install(Path("/fake/project"))
    assert first != second and first.exists() and second.exists()
    assert str(second) in (home / ".local/bin/codex-socks").read_text()


def test_failed_publish_restores_launcher_symlink(manager_paths, bootstrap_env, tmp_path, monkeypatch):
    home, _ = bootstrap_env
    real = tmp_path / "fake-codex"
    real.write_bytes(b"\x00binary")
    manager_paths.launcher.parent.mkdir(parents=True)
    manager_paths.launcher.symlink_to(real)

    def run(argv, **kwargs):
        if argv[1:3] == ["-m", "codex_socks_manager.cli"]:
            atomic_write(manager_paths.launcher, "new\n")
            raise subprocess.CalledProcessError(1, argv)
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(bootstrap.subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        bootstrap.install(Path("/fake/project"))
    assert manager_paths.launcher.is_symlink()
    assert manager_paths.launcher.resolve() == real
    assert real.read_bytes() == b"\x00binary"
    assert not (home / ".local/bin/codex-socks").exists()


def test_real_installer_with_offline_wheels(manager_paths, bootstrap_env, tmp_path):
    wheelhouse = os.environ.get("CODEX_SOCKS_TEST_WHEELHOUSE")
    if not wheelhouse:
        pytest.skip("Set CODEX_SOCKS_TEST_WHEELHOUSE to a pip wheel directory for the offline installation test")
    home, root = bootstrap_env
    real = home / ".codex/packages/standalone/current/bin/codex"
    real.parent.mkdir(parents=True)
    real.write_text("#!/bin/sh\nexit 0\n")
    real.chmod(0o700)
    project = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHON=sys.executable, PIP_NO_INDEX="1", PIP_FIND_LINKS=wheelhouse)
    env.pop("PYTHONPATH", None)

    def run(argv):
        result = subprocess.run(argv, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    run(["/bin/sh", str(project / "scripts/install.sh")])
    manager = str(home / ".local/bin/codex-socks")
    first = next((root / "venvs").iterdir())
    run([str(first / "bin/python"), "-c", "from importlib.util import find_spec; "
         "assert find_spec('rich') is None; assert find_spec('textual') is None"])
    assert "Command" in run([manager, "-h", "--lang", "en"])
    run([manager, "add", "office", "socks5://proxy.example:1080"])
    run(["/bin/sh", str(project / "scripts/install.sh"), "--with-tui"])
    assert len(list((root / "venvs").iterdir())) == 2 and first.exists()
    payload = json.loads(run([manager, "list", "--json"]))
    assert payload["profiles"][0]["name"] == "office"
    installed_python = Settings.load(manager_paths.settings).manager_python
    output = run([installed_python, "-c", """
import asyncio
from importlib.resources import files
from codex_socks_manager.paths import Paths
from codex_socks_manager.tui import ManagerApp
assert files('codex_socks_manager').joinpath('manager.tcss').is_file()
print(files('codex_socks_manager'))
async def test():
    app = ManagerApp(Paths.discover())
    async with app.run_test() as pilot:
        await pilot.pause()
asyncio.run(test())
"""])
    assert "site-packages" in output
    run(["/bin/sh", str(project / "scripts/install.sh")])
    assert len(list((root / "venvs").iterdir())) == 3
    assert json.loads(run([manager, "list", "--json"])) == payload
    installed_python = Settings.load(manager_paths.settings).manager_python
    run([installed_python, "-c", "from importlib.util import find_spec; "
         "assert find_spec('rich') is None; assert find_spec('textual') is None"])


@pytest.mark.parametrize("args,code", [(["--help"], 0), (["--invalid"], 2)])
def test_installer_arguments_no_side_effects(manager_paths, bootstrap_env, args, code):
    home, root = bootstrap_env
    project = Path(__file__).resolve().parents[1]
    result = subprocess.run(["/bin/sh", str(project / "scripts/install.sh"), *args],
                            env=dict(os.environ, PYTHON=sys.executable), capture_output=True, text=True)
    assert result.returncode == code
    assert "--with-tui" in result.stdout + result.stderr
    assert not root.exists() and not manager_paths.config.exists()

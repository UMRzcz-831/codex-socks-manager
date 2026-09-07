from __future__ import annotations

import json
from pathlib import Path

import pytest

from codex_socks_manager.migration import migrate_legacy
from codex_socks_manager.profiles import ProfileStore
from codex_socks_manager.doctor import CheckResult
from codex_socks_manager.recovery import backup, restore, safe_update, verify_snapshot
from codex_socks_manager.runtime import CodexInstall, install_launcher
from codex_socks_manager.storage import Settings


def make_codex(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_backup_restore_preserves_new_binary_and_profiles(manager_paths, tmp_path):
    old_binary = make_codex(tmp_path / "codex-old")
    new_binary = make_codex(tmp_path / "codex-new")
    install_launcher(manager_paths, CodexInstall(old_binary, "standalone"))
    store = ProfileStore(manager_paths)
    store.add("jp", "http://proxy.test:8080")
    store.set_active("jp")
    snapshot = backup(manager_paths, "known-good")
    settings = Settings.load(manager_paths.settings)
    settings.real_codex = str(new_binary)
    manager_paths.settings.write_text(settings.dump(), encoding="utf-8")
    store.add("us", "socks5h://proxy.test:1080")
    manager_paths.launcher.unlink()
    restore(manager_paths, snapshot.path, restart=False)
    restored = Settings.load(manager_paths.settings)
    assert restored.real_codex == str(new_binary)
    assert restored.active == "jp"
    assert store.get("jp")
    with pytest.raises(FileNotFoundError):
        store.get("us")
    assert manager_paths.launcher.exists()


def test_snapshot_checksum_failure(manager_paths, tmp_path):
    binary = make_codex(tmp_path / "codex")
    install_launcher(manager_paths, CodexInstall(binary, "standalone"))
    snapshot = backup(manager_paths, "known-good")
    (snapshot.path / "manager/config.toml").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError):
        verify_snapshot(snapshot.path)


def test_restore_overwrites_launcher_symlink(manager_paths, tmp_path):
    binary = make_codex(tmp_path / "codex")
    install_launcher(manager_paths, CodexInstall(binary, "standalone"))
    snapshot = backup(manager_paths, "known-good")
    manager_paths.launcher.unlink()
    manager_paths.launcher.symlink_to(binary)
    restore(manager_paths, snapshot.path, restart=False)
    assert manager_paths.launcher.is_file()
    assert not manager_paths.launcher.is_symlink()


def test_legacy_migration_is_idempotent_and_masked(manager_paths, tmp_path):
    legacy = tmp_path / "jp.env"
    legacy.write_text(
        "PROXY_USER=sample-user\nPROXY_" "PASSWORD=sample-password\n"
        "PROXY_HOST=proxy.test\nPROXY_PORT=8080\n",
        encoding="utf-8",
    )
    assert migrate_legacy(manager_paths, {"jp": legacy}) == ["jp"]
    assert migrate_legacy(manager_paths, {"jp": legacy}) == []
    listing = ProfileStore(manager_paths).list()[0]
    assert listing["url"] == "http://***:***@proxy.test:8080"


def test_safe_update_reinstalls_overwritten_launcher(manager_paths, tmp_path, monkeypatch):
    binary = make_codex(tmp_path / "codex")
    install_launcher(manager_paths, CodexInstall(binary, "standalone"))

    class Completed:
        returncode = 0

    def fake_run(*args, **kwargs):
        manager_paths.launcher.unlink()
        manager_paths.launcher.symlink_to(binary)
        return Completed()

    monkeypatch.setattr("codex_socks_manager.recovery.subprocess.run", fake_run)
    monkeypatch.setattr("codex_socks_manager.recovery.check", lambda paths: CheckResult(True, "ok", "ok", "101", "ok", "ok"))
    safe_update(manager_paths, restart=False)
    assert not manager_paths.launcher.is_symlink()


def test_safe_update_validation_failure_restores_proxy_not_binary(manager_paths, tmp_path, monkeypatch):
    binary = make_codex(tmp_path / "codex")
    install_launcher(manager_paths, CodexInstall(binary, "standalone"))
    store = ProfileStore(manager_paths)
    store.add("jp", "http://proxy.test:8080")
    store.set_active("jp")

    class Completed:
        returncode = 0

    monkeypatch.setattr("codex_socks_manager.recovery.subprocess.run", lambda *args, **kwargs: Completed())
    monkeypatch.setattr("codex_socks_manager.recovery.check", lambda paths: CheckResult(False, "proxy_transport", "failed", "failed", "ok", "ok"))
    with pytest.raises(RuntimeError):
        safe_update(manager_paths, restart=False)
    settings = Settings.load(manager_paths.settings)
    assert settings.real_codex == str(binary)
    assert settings.active == "jp"
    assert list(manager_paths.backups.glob("pre-restore-*"))

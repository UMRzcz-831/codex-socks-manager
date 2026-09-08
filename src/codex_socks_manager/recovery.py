from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .appserver import restart_appservers
from .doctor import check
from .paths import Paths
from .progress import Progress, emit
from .runtime import install_launcher
from .storage import Settings, atomic_write, exclusive_lock, secure_dir


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(131072), b""):
            digest.update(block)
    return digest.hexdigest()


def _copy_file(source: Path, target: Path) -> None:
    secure_dir(target.parent)
    resolved = source.resolve() if source.is_symlink() else source
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as output, resolved.open("rb") as input_file:
            shutil.copyfileobj(input_file, output)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
        target.chmod(0o600)
    finally:
        temporary.unlink(missing_ok=True)


@dataclass(frozen=True)
class Snapshot:
    path: Path
    manifest: dict[str, object]


def backup(paths: Paths, label: str = "snapshot", codex_config: Path | None = None) -> Snapshot:
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    target = paths.backups / f"{label}-{timestamp}"
    with exclusive_lock(paths.lock):
        secure_dir(target)
        files: dict[str, str] = {}
        sources = [(paths.settings, "manager/config.toml"), (paths.launcher, "launcher/codex")]
        for profile in sorted(paths.profiles.glob("*.conf")):
            sources.append((profile, f"manager/profiles/{profile.name}"))
        if codex_config and codex_config.exists():
            sources.append((codex_config, "codex/config.toml"))
        for source, relative in sources:
            if source.exists() or source.is_symlink():
                destination = target / relative
                _copy_file(source, destination)
                files[relative] = _sha256(destination)
        manifest = {
            "schema_version": 1,
            "created_at": timestamp,
            "active": Settings.load(paths.settings).active,
            "files": files,
        }
        atomic_write(target / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return Snapshot(target, manifest)


def verify_snapshot(path: Path) -> dict[str, object]:
    manifest_path = path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("snapshot manifest has no files map")
    for relative, expected in files.items():
        candidate = path / relative
        if not candidate.is_file() or _sha256(candidate) != expected:
            raise ValueError(f"snapshot checksum failed: {relative}")
    return manifest


def latest_snapshot(paths: Paths, label: str | None = None) -> Path:
    pattern = f"{label}-*" if label else "*-*"
    candidates = sorted((path for path in paths.backups.glob(pattern) if (path / "manifest.json").exists()), reverse=True)
    if not candidates:
        raise FileNotFoundError("no backup snapshot found")
    return candidates[0]


def restore(paths: Paths, snapshot: Path | None = None, restart: bool = True, progress: Progress | None = None) -> Path:
    selected = snapshot or latest_snapshot(paths, "known-good")
    manifest = verify_snapshot(selected)
    emit(progress, "snapshot")
    backup(paths, "pre-restore")
    emit(progress, "restoring")
    current = Settings.load(paths.settings)
    with exclusive_lock(paths.lock):
        source_settings = selected / "manager/config.toml"
        restored = Settings.load(source_settings) if source_settings.exists() else Settings()
        # Preserve the currently installed binary. Snapshots only restore the proxy layer.
        if current.real_codex:
            restored.real_codex = current.real_codex
            restored.install_source = current.install_source
        if current.manager_python:
            restored.manager_python = current.manager_python
        atomic_write(paths.settings, restored.dump())
        existing = {path.name for path in paths.profiles.glob("*.conf")}
        snapshot_profiles = selected / "manager/profiles"
        wanted = {path.name for path in snapshot_profiles.glob("*.conf")} if snapshot_profiles.exists() else set()
        for name in existing - wanted:
            (paths.profiles / name).unlink()
        for source in snapshot_profiles.glob("*.conf") if snapshot_profiles.exists() else []:
            _copy_file(source, paths.profiles / source.name)
        launcher = selected / "launcher/codex"
        if launcher.exists():
            _copy_file(launcher, paths.launcher)
            paths.launcher.chmod(0o700)
        else:
            install_launcher(paths)
    if restart:
        emit(progress, "restarting")
        restart_appservers(paths)
    return selected


def safe_update(paths: Paths, restart: bool = True, progress: Progress | None = None) -> None:
    emit(progress, "snapshot")
    snapshot = backup(paths, "known-good")
    settings = Settings.load(paths.settings)
    if not settings.real_codex:
        raise RuntimeError("Codex executable is not configured")
    try:
        emit(progress, "updating")
        completed = subprocess.run([settings.real_codex, "update"], text=True, capture_output=True, timeout=600, check=False)
        if completed.returncode != 0:
            raise RuntimeError("official codex update failed")
        emit(progress, "launcher")
        install_launcher(paths)
        if restart:
            emit(progress, "restarting")
            restart_appservers(paths)
        emit(progress, "validating")
        result = check(paths)
        if not result.ok:
            raise RuntimeError(f"post-update validation failed: {result.category}")
    except Exception as error:
        emit(progress, "rollback")
        try:
            restore(paths, snapshot.path, restart=restart, progress=progress)
        except Exception as recovery_error:
            emit(progress, "rollback_failed")
            raise RuntimeError(f"{error}; rollback failed: {recovery_error}") from error
        emit(progress, "rolled_back")
        raise

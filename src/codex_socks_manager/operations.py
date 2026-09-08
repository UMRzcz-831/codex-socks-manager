"""Shared operations for both frontends. No UI imports or stdout output."""
from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from pathlib import Path

from .appserver import discover_appservers, start_processes, stop_processes
from .doctor import check
from .migration import migrate_legacy
from .paths import Paths
from .profiles import ProfileStore, validate_url
from .progress import Progress, emit
from .recovery import backup, restore, safe_update
from .runtime import install_launcher
from .storage import Settings


def switch(paths: Paths, name: str, restart: bool = True, progress: Progress | None = None) -> None:
    store = ProfileStore(paths)
    previous = Settings.load(paths.settings).active
    roles = discover_appservers(paths) if restart else []
    if restart and not roles:
        raise RuntimeError("no matching current-user Codex app-server process found")
    try:
        emit(progress, "selecting")
        store.set_active(name)
        if restart:
            emit(progress, "restarting")
            stop_processes(roles)
            started = start_processes(paths, roles)
            if any(process.poll() is not None for process in started):
                raise RuntimeError("one or more Codex app-server roles failed to start")
            emit(progress, "validating")
            result = check(paths)
            if not result.ok:
                raise RuntimeError(f"validation failed: {result.category}")
    except Exception as error:
        emit(progress, "rollback")
        try:
            store.set_active(previous)
            if restart and roles:
                current = discover_appservers(paths)
                if current:
                    stop_processes(current)
                recovered = start_processes(paths, roles)
                if any(process.poll() is not None for process in recovered):
                    raise RuntimeError("one or more recovered app-server roles failed to start")
        except Exception as recovery_error:
            emit(progress, "rollback_failed")
            raise RuntimeError(f"{error}; rollback failed: {recovery_error}") from error
        emit(progress, "rolled_back")
        raise


def edit_in_editor(paths: Paths, name: str) -> None:
    store = ProfileStore(paths)
    current = store.get(name)
    editor = os.environ.get("EDITOR")
    if not editor:
        raise RuntimeError("EDITOR is not set")
    descriptor, filename = tempfile.mkstemp(prefix=f"codex-socks-{name}-")
    temporary = Path(filename)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(current + "\n")
        completed = subprocess.run([*shlex.split(editor), str(temporary)], check=False)
        if completed.returncode != 0:
            raise RuntimeError("editor exited unsuccessfully")
        replacement = validate_url(temporary.read_text(encoding="utf-8").strip())
        store.add(name, replacement, replace=True)
    finally:
        temporary.unlink(missing_ok=True)


class Manager:
    def __init__(self, paths: Paths):
        self.paths = paths
        self.store = ProfileStore(paths)

    @property
    def active(self) -> str:
        return Settings.load(self.paths.settings).active

    def snapshots(self) -> list[Path]:
        return sorted((path.parent for path in self.paths.backups.glob("*/manifest.json")), reverse=True)

    def execute(self, command: str, *, name: str = "", url: str | None = None,
                force: bool = False, restart: bool = True, snapshot: Path | None = None,
                jp: Path | None = None, us: Path | None = None, progress: Progress | None = None):
        emit(progress, "working")
        result = None
        if command == "add":
            if url is None:
                raise ValueError("proxy URL is required")
            self.store.add(name, url)
        elif command == "edit":
            if url is None:
                edit_in_editor(self.paths, name)
            else:
                self.store.get(name)
                self.store.add(name, validate_url(url), replace=True)
        elif command in {"use", "off"}:
            switch(self.paths, name if command == "use" else "off", restart, progress)
        elif command == "del":
            if self.active == name and force:
                switch(self.paths, "off", True, progress)
            self.store.delete(name)
        elif command == "check":
            emit(progress, "validating")
            result = check(self.paths)
        elif command == "install":
            emit(progress, "launcher")
            result = install_launcher(self.paths)
        elif command == "backup":
            emit(progress, "snapshot")
            result = backup(self.paths, "known-good", self.paths.launcher.parents[2] / ".codex/config.toml").path
        elif command == "restore":
            result = restore(self.paths, snapshot, progress=progress)
        elif command == "safe-update":
            safe_update(self.paths, progress=progress)
        elif command == "migrate-legacy":
            sources = {key: value for key, value in (("jp", jp), ("us", us)) if value is not None}
            if not sources:
                base = self.paths.launcher.parents[2] / ".config/openai-proxy"
                sources = {"jp": base / "jp.env", "us": base / "us.env"}
            result = migrate_legacy(self.paths, sources)
        else:
            raise ValueError(f"unknown operation: {command}")
        emit(progress, "complete")
        return result

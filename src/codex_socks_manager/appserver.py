from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .paths import Paths
from .runtime import build_codex_env
from .storage import Settings, secure_dir


@dataclass(frozen=True)
class AppServerProcess:
    pid: int
    argv: tuple[str, ...]


def discover_appservers(paths: Paths, proc_root: Path = Path("/proc"), uid: int | None = None) -> list[AppServerProcess]:
    expected_uid = os.getuid() if uid is None else uid
    settings = Settings.load(paths.settings)
    real = Path(settings.real_codex).resolve(strict=False) if settings.real_codex else None
    result: list[AppServerProcess] = []
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != expected_uid:
                continue
            raw = (entry / "cmdline").read_bytes()
            argv = tuple(part.decode("utf-8", "replace") for part in raw.split(b"\0") if part)
            if not argv or "app-server" not in argv:
                continue
            executable = Path(argv[0]).resolve(strict=False)
            if real is not None and executable != real and executable != paths.launcher.resolve(strict=False):
                continue
            result.append(AppServerProcess(int(entry.name), argv))
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            continue
    return sorted(result, key=lambda item: item.pid)


def stop_processes(processes: list[AppServerProcess], timeout: float = 5.0) -> None:
    for process in processes:
        os.kill(process.pid, signal.SIGTERM)
    deadline = time.monotonic() + timeout
    remaining = {process.pid for process in processes}
    while remaining and time.monotonic() < deadline:
        remaining = {pid for pid in remaining if Path(f"/proc/{pid}").exists()}
        if remaining:
            time.sleep(0.05)
    for pid in remaining:
        os.kill(pid, signal.SIGKILL)


def start_processes(paths: Paths, roles: list[AppServerProcess]) -> list[subprocess.Popen[bytes]]:
    secure_dir(paths.state / "logs")
    log = open(paths.state / "logs/app-server.log", "ab", buffering=0)
    started = []
    for role in roles:
        started.append(
            subprocess.Popen(
                list(role.argv),
                env=build_codex_env(paths),
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
        )
    return started


def restart_appservers(paths: Paths, timeout: float = 5.0) -> list[AppServerProcess]:
    roles = discover_appservers(paths)
    if not roles:
        raise RuntimeError("no matching current-user Codex app-server process found")
    stop_processes(roles, timeout)
    started = start_processes(paths, roles)
    time.sleep(0.25)
    failed = [process for process in started if process.poll() is not None]
    if failed:
        raise RuntimeError("one or more Codex app-server roles failed to start")
    return roles


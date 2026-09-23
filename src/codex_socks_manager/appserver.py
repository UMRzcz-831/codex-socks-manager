from __future__ import annotations

import os
import shutil
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


def release_root(executable: Path) -> Path | None:
    """Standalone releases root shared by every installed Codex version."""
    parents = executable.parents
    if executable.parent.name != "bin" or len(parents) < 3:
        return None
    root = parents[2]
    return root if root.name == "releases" else None


def same_install(candidate: Path, expected: set[Path]) -> bool:
    """Match the configured Codex, the launcher, or another version of the same install."""
    if candidate in expected:
        return True
    root = release_root(candidate)
    return root is not None and any(root == release_root(item) for item in expected)


def process_search_path(entry: Path) -> str | None:
    try:
        environ = (entry / "environ").read_bytes()
    except OSError:
        return os.environ.get("PATH")
    for item in environ.split(b"\0"):
        name, separator, value = item.decode("utf-8", "replace").partition("=")
        if separator and name == "PATH":
            return value
    return os.environ.get("PATH")


def process_identities(entry: Path, argv: tuple[str, ...]) -> list[Path]:
    """Paths identifying a live process, preferring /proc/<pid>/exe over argv[0].

    Codex re-execs itself with a bare ``codex`` argv[0], so argv alone cannot be
    resolved against the filesystem.
    """
    likely: list[Path] = []
    try:
        target = os.readlink(entry / "exe").removesuffix(" (deleted)")
    except OSError:
        target = ""
    if target:
        likely.append(Path(target))
    search_path = process_search_path(entry)
    for argument in argv[:2]:
        if not argument or argument.startswith("-"):
            continue
        if os.sep in argument:
            likely.append(Path(argument))
            continue
        found = shutil.which(argument, path=search_path)
        if found:
            likely.append(Path(found))
    return [candidate.resolve(strict=False) for candidate in likely]


def discover_appservers(paths: Paths, proc_root: Path = Path("/proc"), uid: int | None = None) -> list[AppServerProcess]:
    expected_uid = os.getuid() if uid is None else uid
    settings = Settings.load(paths.settings)
    real = Path(settings.real_codex).resolve(strict=False) if settings.real_codex else None
    expected = {real, paths.launcher.resolve(strict=False)} if real is not None else set()
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
            if expected and not any(same_install(candidate, expected) for candidate in process_identities(entry, argv)):
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


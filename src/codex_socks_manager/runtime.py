from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .paths import Paths
from .profiles import ProfileStore
from .storage import Settings, atomic_write, initialize

LOCAL_BYPASS = ["localhost", "127.0.0.1", "::1"]


def merge_no_proxy(existing: str = "") -> str:
    items: list[str] = []
    for item in [*LOCAL_BYPASS, *existing.split(",")]:
        clean = item.strip()
        if clean and clean not in items:
            items.append(clean)
    return ",".join(items)


def proxy_environment(base: dict[str, str], proxy_url: str | None) -> dict[str, str]:
    env = dict(base)
    keys = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
    if proxy_url:
        for key in keys:
            env[key] = proxy_url
    else:
        for key in keys:
            env.pop(key, None)
    no_proxy = merge_no_proxy(env.get("NO_PROXY", env.get("no_proxy", "")))
    env["NO_PROXY"] = no_proxy
    env["no_proxy"] = no_proxy
    return env


@dataclass(frozen=True)
class CodexInstall:
    executable: Path
    source: str


def _source_for(path: Path) -> str:
    value = str(path)
    if "/pnpm/" in value or "/.pnpm/" in value:
        return "pnpm"
    if "/node_modules/" in value or "/npm/" in value:
        return "npm"
    return "standalone"


def discover_codex(paths: Paths, env: dict[str, str] | None = None) -> CodexInstall:
    values = dict(os.environ) if env is None else env
    if env is None:
        values["HOME"] = str(paths.launcher.parents[2])
    home = Path(values.get("HOME", str(Path.home())))
    candidates = [
        home / ".codex/packages/standalone/current/bin/codex",
        home / ".local/share/codex/bin/codex",
    ]
    found = shutil.which("codex", path=values.get("PATH"))
    if found:
        candidates.append(Path(found))
    launcher = paths.launcher.absolute()
    for candidate in candidates:
        if not candidate.exists() or not os.access(candidate, os.X_OK):
            continue
        if candidate.absolute() == launcher:
            continue
        return CodexInstall(candidate.resolve(), _source_for(candidate.resolve()))
    raise FileNotFoundError("unable to find a non-managed Codex executable")


def install_launcher(paths: Paths, install: CodexInstall | None = None) -> Settings:
    initialize(paths)
    current = Settings.load(paths.settings)
    selected = install
    if selected is None:
        standalone = paths.launcher.parents[2] / ".codex/packages/standalone/current/bin/codex"
        if standalone.exists() and os.access(standalone, os.X_OK):
            selected = CodexInstall(standalone.resolve(), "standalone")
    if selected is None and current.real_codex:
        candidate = Path(current.real_codex)
        if candidate.exists() and candidate.absolute() != paths.launcher.absolute():
            selected = CodexInstall(candidate.resolve(), current.install_source or _source_for(candidate))
    if selected is None:
        selected = discover_codex(paths)
    current.real_codex = str(selected.executable)
    current.install_source = selected.source
    current.manager_python = sys.executable
    atomic_write(paths.settings, current.dump())
    package_root = Path(__file__).resolve().parents[1]
    script = "\n".join(
        [
            "#!/bin/sh",
            "# Managed by codex-socks-manager. Do not edit.",
            f"PYTHONPATH={shell_quote(str(package_root))}${{PYTHONPATH:+:\":$PYTHONPATH\"}}",
            "export PYTHONPATH",
            f'exec {shell_quote(sys.executable)} -m codex_socks_manager.exec_codex "$@"',
            "",
        ]
    )
    atomic_write(paths.launcher, script, 0o700)
    return current


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def build_codex_env(paths: Paths, base: dict[str, str] | None = None) -> dict[str, str]:
    settings = Settings.load(paths.settings)
    proxy = None if settings.active == "off" else ProfileStore(paths).get(settings.active)
    return proxy_environment(dict(os.environ if base is None else base), proxy)


def exec_real_codex(paths: Paths, argv: list[str]) -> None:
    settings = Settings.load(paths.settings)
    if not settings.real_codex:
        raise RuntimeError("Codex executable is not configured; run codex-socks install")
    executable = Path(settings.real_codex)
    if executable.resolve(strict=False) == paths.launcher.resolve(strict=False):
        raise RuntimeError("refusing recursive managed launcher")
    os.execve(executable, [str(executable), *argv], build_codex_env(paths))


def run_codex(paths: Paths, args: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    settings = Settings.load(paths.settings)
    if not settings.real_codex:
        raise RuntimeError("Codex executable is not configured")
    return subprocess.run(
        [settings.real_codex, *args],
        env=build_codex_env(paths),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )

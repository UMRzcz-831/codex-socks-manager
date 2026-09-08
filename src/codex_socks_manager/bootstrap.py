"""Standard-library bootstrap for versioned user-local installations."""
from __future__ import annotations

import os
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .paths import Paths
from .runtime import shell_quote
from .storage import atomic_write, secure_dir


def preflight(with_tui: bool) -> str:
    core = (
        "from codex_socks_manager.cli import parser; "
        "from codex_socks_manager.runtime import select_install; "
        "from codex_socks_manager.paths import Paths; "
        "parser(); select_install(Paths.discover()); "
    )
    if with_tui:
        core += (
            "from importlib.resources import files; "
            "from codex_socks_manager.tui import ManagerApp; "
            "assert files('codex_socks_manager').joinpath('manager.tcss').is_file(); "
        )
    return core


def install(project: Path, *, with_tui: bool = False) -> Path:
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10 or later is required")
    paths = Paths.discover()
    home = paths.launcher.parents[2]
    root = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share")) / "codex-socks-manager"
    secure_dir(root / "venvs")
    environment = Path(tempfile.mkdtemp(prefix="install-", dir=root / "venvs"))
    python = environment / "bin/python"
    child_env = dict(os.environ)
    child_env.pop("PYTHONPATH", None)
    child_env.pop("PYTHONHOME", None)
    try:
        subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True, env=child_env)
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Cannot create a venv. Install Python's venv/ensurepip support and retry; existing commands were not changed.") from error
    try:
        target = str(project) + ("[tui]" if with_tui else "")
        subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", target],
                       check=True, env=child_env)
        subprocess.run([str(python), "-c", preflight(with_tui)], check=True, env=child_env)
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Package installation or preflight failed; existing commands and configuration were not changed.") from error

    manager = home / ".local/bin/codex-socks"
    guard = home / ".local/bin/codex-proxy-guard"
    targets = (manager, guard, paths.launcher, paths.settings)
    for target in targets:
        if target.exists() and not target.is_file():
            raise RuntimeError(f"Refusing to replace a non-file: {target}")
    secure_dir(paths.state / "bootstrap-backups")
    saved = Path(tempfile.mkdtemp(prefix="install-", dir=paths.state / "bootstrap-backups"))
    originals: dict[Path, Path | None] = {}
    for number, target in enumerate(targets):
        if target.exists() or target.is_symlink():
            destination = saved / str(number)
            shutil.copy2(target, destination, follow_symlinks=False)
            if not destination.is_symlink():
                destination.chmod(0o600)
            originals[target] = destination
        else:
            originals[target] = None
    # Keep original executable modes separately from private backup permissions.
    modes = {target: target.stat().st_mode & 0o777 for target in targets if target.exists() and not target.is_symlink()}
    try:
        subprocess.run([str(python), "-m", "codex_socks_manager.cli", "install"], check=True, env=child_env)
        wrapper = f'#!/bin/sh\nexec {shell_quote(str(python))} -m codex_socks_manager.cli "$@"\n'
        atomic_write(manager, wrapper, 0o700)
        atomic_write(guard, f'#!/bin/sh\nexec {shell_quote(str(manager))} "$@"\n', 0o700)
    except Exception:
        for target, source in originals.items():
            if source is None:
                if target.is_file() or target.is_symlink():
                    target.unlink()
            elif source.is_symlink():
                temporary = target.with_name(target.name + ".bootstrap-restore")
                temporary.unlink(missing_ok=True)
                temporary.symlink_to(os.readlink(source))
                os.replace(temporary, target)
            else:
                descriptor, filename = tempfile.mkstemp(prefix=".bootstrap-restore-", dir=target.parent)
                temporary = Path(filename)
                try:
                    with os.fdopen(descriptor, "wb") as handle:
                        handle.write(source.read_bytes())
                        handle.flush()
                        os.fsync(handle.fileno())
                    temporary.chmod(modes.get(target, 0o600))
                    os.replace(temporary, target)
                finally:
                    temporary.unlink(missing_ok=True)
        raise
    return environment


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="install.sh", allow_abbrev=False,
        description="Install the zero-runtime-dependency CLI (default), or CLI + TUI. "
                    "默认安装零运行依赖 CLI；使用 --with-tui 选装界面。",
        epilog="Each run selects a new environment; old environments and profiles are retained. "
               "每次按选项创建新环境，保留旧环境和代理配置。")
    parser.add_argument("project", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--with-tui", action="store_true", help="Install Textual / Rich UI · 安装交互界面")
    args = parser.parse_args()
    try:
        environment = install(args.project.resolve(), with_tui=args.with_tui)
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"Installation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(f"Installed in {environment}.")
    if args.with_tui:
        print("CLI + TUI installed / 已安装完整界面。Run codex-socks tui; keep --with-tui when upgrading.")
    else:
        print("CLI installed / 已安装轻量 CLI。Run codex-socks --help. "
              "To add TUI / 补装界面: ./scripts/install.sh --with-tui (from the project directory / 在项目目录执行).")


if __name__ == "__main__":
    main()

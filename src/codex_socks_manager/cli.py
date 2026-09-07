from __future__ import annotations

import argparse
import getpass
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

from .appserver import discover_appservers, start_processes, stop_processes
from .doctor import check
from .migration import migrate_legacy
from .paths import Paths
from .profiles import ProfileStore, validate_url
from .recovery import backup, restore, safe_update
from .runtime import install_launcher
from .storage import Settings


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="codex-socks", description="Manage Codex CLI proxy profiles safely")
    commands = root.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add")
    add.add_argument("name")
    add.add_argument("url", nargs="?")
    use = commands.add_parser("use")
    use.add_argument("name")
    use.add_argument("--no-restart", action="store_true", help=argparse.SUPPRESS)
    listing = commands.add_parser("list")
    listing.add_argument("--json", action="store_true")
    edit = commands.add_parser("edit")
    edit.add_argument("name")
    delete = commands.add_parser("del")
    delete.add_argument("name")
    delete.add_argument("--force", action="store_true")
    off = commands.add_parser("off")
    off.add_argument("--no-restart", action="store_true", help=argparse.SUPPRESS)
    commands.add_parser("check")
    commands.add_parser("install")
    commands.add_parser("backup")
    restore_parser = commands.add_parser("restore")
    restore_parser.add_argument("snapshot", nargs="?", type=Path)
    commands.add_parser("safe-update")
    migration = commands.add_parser("migrate-legacy")
    migration.add_argument("--jp", type=Path)
    migration.add_argument("--us", type=Path)
    return root


def _switch(paths: Paths, name: str, restart: bool) -> None:
    store = ProfileStore(paths)
    previous = Settings.load(paths.settings).active
    roles = discover_appservers(paths) if restart else []
    if restart and not roles:
        raise RuntimeError("no matching current-user Codex app-server process found")
    try:
        store.set_active(name)
        if restart:
            stop_processes(roles)
            started = start_processes(paths, roles)
            if any(process.poll() is not None for process in started):
                raise RuntimeError("one or more Codex app-server roles failed to start")
            result = check(paths)
            if not result.ok:
                raise RuntimeError(f"validation failed: {result.category}")
    except Exception:
        store.set_active(previous)
        if restart and roles:
            current = discover_appservers(paths)
            if current:
                stop_processes(current)
            start_processes(paths, roles)
        raise


def _edit(paths: Paths, name: str) -> None:
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


def run(argv: list[str] | None = None, paths: Paths | None = None) -> int:
    args = parser().parse_args(argv)
    paths = paths or Paths.discover()
    store = ProfileStore(paths)
    if args.command == "add":
        url = args.url or getpass.getpass("Proxy URL: ")
        store.add(args.name, url)
        print(f"added profile {args.name}")
    elif args.command == "list":
        profiles = store.list()
        if args.json:
            print(json.dumps({"active": Settings.load(paths.settings).active, "profiles": profiles}, indent=2))
        elif not profiles:
            print("no profiles")
        else:
            for item in profiles:
                marker = "*" if item["active"] else " "
                print(f"{marker} {item['name']:<16} {item['scheme']:<8} {item['url']}")
    elif args.command in {"use", "off"}:
        name = args.name if args.command == "use" else "off"
        _switch(paths, name, not args.no_restart)
        print(f"active profile: {name}")
    elif args.command == "edit":
        _edit(paths, args.name)
        print(f"updated profile {args.name}")
    elif args.command == "del":
        active = Settings.load(paths.settings).active
        if active == args.name and args.force:
            _switch(paths, "off", True)
            store.delete(args.name)
            print("active profile switched to off")
        else:
            store.delete(args.name, False)
        print(f"deleted profile {args.name}")
    elif args.command == "install":
        settings = install_launcher(paths)
        print(f"installed launcher for {settings.install_source} Codex")
    elif args.command == "check":
        result = check(paths)
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.ok else 1
    elif args.command == "backup":
        snapshot = backup(paths, "known-good", Path.home() / ".codex/config.toml")
        print(snapshot.path)
    elif args.command == "restore":
        print(restore(paths, args.snapshot))
    elif args.command == "safe-update":
        safe_update(paths)
        print("Codex update and proxy validation completed")
    elif args.command == "migrate-legacy":
        sources = {}
        if args.jp:
            sources["jp"] = args.jp
        if args.us:
            sources["us"] = args.us
        if not sources:
            base = Path.home() / ".config/openai-proxy"
            sources = {"jp": base / "jp.env", "us": base / "us.env"}
        migrated = migrate_legacy(paths, sources)
        print("migrated: " + (", ".join(migrated) if migrated else "none (already current or absent)"))
    return 0


def main() -> None:
    try:
        raise SystemExit(run())
    except (ValueError, FileNotFoundError, FileExistsError, PermissionError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error


def guard_main() -> None:
    main()


if __name__ == "__main__":
    main()

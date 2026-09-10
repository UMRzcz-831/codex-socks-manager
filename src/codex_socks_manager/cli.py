from __future__ import annotations

import argparse
import getpass
import io
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from .catalog import COMMANDS, language, translated
from .operations import Manager, edit_in_editor as _edit, switch as _switch
from .paths import Paths
from .presentation import print_help, print_profiles, safe_error


class HelpParser(argparse.ArgumentParser):
    def __init__(self, *args, lang: str = "en", command: str | None = None, **kwargs):
        self.lang = lang
        self.command_name = command
        super().__init__(*args, **kwargs)

    def print_help(self, file=None) -> None:
        print_help(self.lang, self.command_name, file)

    def format_help(self) -> str:
        output = io.StringIO()
        self.print_help(output)
        return output.getvalue()


def parser(lang: str | None = None) -> argparse.ArgumentParser:
    lang = language(lang)
    root = HelpParser(prog="codex-socks", lang=lang, allow_abbrev=False)
    root.add_argument("--lang", choices=("zh-CN", "en"), default=argparse.SUPPRESS)
    commands = root.add_subparsers(dest="command")
    for entry in COMMANDS:
        sub = commands.add_parser(entry.name, lang=lang, command=entry.name, allow_abbrev=False,
                                  help=entry.text("summary", lang))
        sub.add_argument("--lang", choices=("zh-CN", "en"), default=argparse.SUPPRESS)
        for name, en, zh in entry.parameters:
            kwargs: dict = {"help": translated(lang, en, zh)}
            if name in {"--json", "--force"}:
                kwargs["action"] = "store_true"
            elif name in {"--jp", "--us", "snapshot"}:
                kwargs["type"] = Path
            if name in {"url", "snapshot"}:
                kwargs["nargs"] = "?"
            sub.add_argument(name, **kwargs)
        if entry.name in {"use", "off"}:
            sub.add_argument("--no-restart", action="store_true", help=argparse.SUPPRESS)
    return root


def interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty() and os.environ.get("TERM") != "dumb"


def tui_available() -> bool:
    return all(importlib.util.find_spec(name) is not None for name in ("textual", "rich"))


def load_tui():
    from .tui import ManagerApp
    return ManagerApp


def argument_language(argv: list[str]) -> str:
    probe = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    probe.add_argument("--lang", choices=("zh-CN", "en"))
    selected, _ = probe.parse_known_args(argv)
    return language(selected.lang)


def run(argv: list[str] | None = None, paths: Paths | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    lang = argument_language(argv)
    root = parser(lang)
    args = root.parse_args(argv)
    t = lambda en, zh: translated(lang, en, zh)
    if args.command is None and not interactive():
        root.print_help()
        return 0
    if args.command in {None, "tui"}:
        if not interactive():
            print(t("error: tui requires an interactive terminal; use --help or list --json.",
                    "错误：tui 需要交互终端；请使用 --help 或 list --json。"), file=sys.stderr)
            return 2
        if not tui_available():
            if args.command is None:
                root.print_help()
                return 0
            print(t("error: TUI is optional. Rerun the GitHub or source installer with --with-tui, "
                    "or reinstall codex-socks-manager[tui] in the same Python environment.",
                    "错误：TUI 为选装功能。请用 --with-tui 重新运行 GitHub 或源码安装器，"
                    "或在同一 Python 环境重装 codex-socks-manager[tui]。"), file=sys.stderr)
            return 2
        try:
            ManagerApp = load_tui()
        except ImportError as error:
            print(t("error: TUI installation is damaged; reinstall with --with-tui. ",
                    "错误：TUI 安装损坏，请用 --with-tui 重新安装。") + safe_error(error), file=sys.stderr)
            return 2
        ManagerApp(paths or Paths.discover(), lang=lang).run()
        return 0
    manager = Manager(paths or Paths.discover())
    if args.command == "list":
        profiles = manager.store.list()
        if args.json:
            print(json.dumps({"active": manager.active, "profiles": profiles}, indent=2))
        else:
            print_profiles(profiles, lang)
        return 0
    kwargs = {key: value for key, value in vars(args).items()
              if key in {"name", "url", "force", "snapshot", "jp", "us"}}
    if args.command == "add":
        kwargs["url"] = args.url or getpass.getpass(t("Proxy URL: ", "代理 URL："))
    kwargs["restart"] = not getattr(args, "no_restart", False)
    deleted_active = args.command == "del" and manager.active == args.name
    result = manager.execute(args.command, **kwargs)
    if args.command == "check":
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.ok else 1
    if args.command in {"backup", "restore"}:
        print(result)
    elif args.command == "migrate-legacy":
        print(t("migrated: ", "已导入：") + (", ".join(result) if result else t("none (already current or absent)", "无（已存在或源文件缺失）")))
    elif args.command == "install":
        print(t(f"installed launcher for {result.install_source} Codex", f"已为 {result.install_source} Codex 安装 launcher"))
    elif args.command in {"use", "off"}:
        print(t("active profile: ", "活动配置：") + manager.active)
    elif args.command == "safe-update":
        print(t("Codex update and proxy validation completed", "Codex 更新及代理验收完成"))
    else:
        if deleted_active:
            print(t("active profile switched to off", "活动配置已切换为 off"))
        label = {"add": ("added profile ", "已新增配置："), "edit": ("updated profile ", "已更新配置："),
                 "del": ("deleted profile ", "已删除配置：")}[args.command]
        print(t(*label) + args.name)
    return 0


def main() -> None:
    try:
        raise SystemExit(run())
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        prefix = translated(argument_language(sys.argv[1:]), "error", "错误")
        print(f"{prefix}: {safe_error(error)}", file=sys.stderr)
        raise SystemExit(2) from error


def guard_main() -> None:
    main()


if __name__ == "__main__":
    main()

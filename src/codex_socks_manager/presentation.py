"""Dependency-free CLI tables and safe plain-text errors."""
from __future__ import annotations

import re
import shutil
import sys
import unicodedata
from itertools import zip_longest
from typing import TextIO

from .catalog import BY_NAME, COMMANDS, translated
from .profiles import mask_url


def display_width(text: str) -> int:
    return sum(0 if unicodedata.category(char) in {"Mn", "Me", "Cf"} else
               2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1 for char in text)


def plain(text: object) -> str:
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "?", str(text).expandtabs(4))


def fold(text: str, width: int) -> list[str]:
    lines = []
    for paragraph in plain(text).split("\n"):
        line, used = "", 0
        for char in paragraph:
            size = display_width(char)
            if line and used + size > width:
                lines.append(line)
                line, used = "", 0
            line += char
            used += size
        lines.append(line)
    return lines


def plain_table(headers: tuple[str, ...], rows: list[tuple[str, ...]], width: int | None = None) -> str:
    width = width if width is not None else shutil.get_terminal_size((100, 24)).columns
    data = [headers, *rows]
    widths = [max(2, *(display_width(part) for row in data
                       for part in plain(row[index]).split("\n")))
              for index in range(len(headers))]
    available = max(2 * len(headers), width - 3 * len(headers) - 1)
    while sum(widths) > available:
        index = max(range(len(widths)), key=widths.__getitem__)
        widths[index] -= 1
    border = "+" + "+".join("-" * (size + 2) for size in widths) + "+"
    output = [border]
    for number, row in enumerate(data):
        cells = [fold(value, size) for value, size in zip(row, widths)]
        for line in zip_longest(*cells, fillvalue=""):
            output.append("| " + " | ".join(value + " " * (size - display_width(value))
                                            for value, size in zip(line, widths)) + " |")
        if number == 0:
            output.append(border)
    if rows:
        output.append(border)
    return "\n".join(output)


def print_help(lang: str, command: str | None = None, file: TextIO | None = None) -> None:
    output = file or sys.stdout
    t = lambda en, zh: translated(lang, en, zh)
    selected = BY_NAME.get(command or "")
    print("codex-socks" + (f" {selected.usage}" if selected else " [--lang {zh-CN,en}] COMMAND"), file=output)
    if selected:
        print(selected.text("summary", lang), file=output)
        print(selected.text("detail", lang), file=output)
    else:
        print(t("Manage Codex proxy profiles, diagnostics and recovery.", "管理 Codex 代理配置、诊断与恢复。"), file=output)
        print(plain_table((t("Command", "命令"), t("Description", "功能"), t("Example", "示例")),
                          [(entry.usage, entry.text("summary", lang), entry.examples[0])
                           for entry in COMMANDS]), file=output)
    options = [(name, t(en, zh)) for name, en, zh in selected.parameters] if selected else []
    options.extend([("-h, --help", t("Show help and exit.", "显示帮助并退出。")),
                    ("--lang {zh-CN,en}", t("Language, before or after the command.", "界面语言，可放在子命令前后。"))])
    print(plain_table((t("Argument / option", "参数 / 选项"), t("Description", "说明")), options), file=output)
    if selected:
        print(plain_table((t("Examples", "示例"),), [(example,) for example in selected.examples]), file=output)


def print_profiles(profiles: list[dict[str, object]], lang: str) -> None:
    t = lambda en, zh: translated(lang, en, zh)
    headers = tuple(t(en, zh) for en, zh in (
        ("State", "状态"), ("Name", "名称"), ("Protocol", "协议"), ("Proxy address", "代理地址")))
    rows = [("* " + t("Active", "当前") if item["active"] else "—",
             str(item["name"]), str(item["scheme"]), str(item["url"])) for item in profiles]
    print(plain_table(headers, rows))
    if not profiles:
        print(t("No profiles. Add one with: codex-socks add office", "暂无配置。可执行：codex-socks add office"))


def safe_error(error: object) -> str:
    """Treat diagnostics as plain text and redact URL userinfo, even for invalid URLs."""
    message = str(error)
    def clean(match: re.Match[str]) -> str:
        try:
            return mask_url(match.group())
        except ValueError:
            return "<redacted proxy URL>"
    message = re.sub(r"(?:socks5h?|https?)://[^\s<>\"']+", clean, message, flags=re.IGNORECASE)
    return re.sub(r"[\x00-\x1f\x7f]", " ", message)

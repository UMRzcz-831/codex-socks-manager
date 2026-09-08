"""Rich renderables loaded only by the optional TUI."""
from rich import box
from rich.console import Group
from rich.table import Table
from rich.text import Text
from .catalog import BY_NAME, COMMANDS, translated
from .ui_theme import COLORS


def table(headers: tuple[str, ...], plain: bool = False) -> Table:
    result = Table(box=box.ASCII if plain else box.SQUARE, header_style="bold",
                   show_lines=False, padding=(0, 1), expand=True)
    for heading in headers:
        result.add_column(heading, overflow="fold")
    return result


def help_view(lang: str, command: str | None = None, plain: bool = False) -> Group:
    t = lambda en, zh: translated(lang, en, zh)
    selected = BY_NAME.get(command or "")
    heading = "codex-socks" + (f" {selected.usage}" if selected else " [--lang {zh-CN,en}] COMMAND")
    items: list = [Text(heading, style="bold " + COLORS["accent"])]
    if selected:
        items.extend((Text(selected.text("summary", lang)), Text(selected.text("detail", lang))))
    else:
        items.append(Text(t("Manage Codex proxy profiles, diagnostics and recovery.", "管理 Codex 代理配置、诊断与恢复。")))
        listing = table((t("Command", "命令"), t("Description", "功能"), t("Example", "示例")), plain)
        for entry in COMMANDS:
            listing.add_row(Text(entry.usage), Text(entry.text("summary", lang)), Text(entry.examples[0]))
        items.append(listing)
    options = table((t("Argument / option", "参数 / 选项"), t("Description", "说明")), plain)
    if selected:
        for name, en, zh in selected.parameters:
            options.add_row(name, Text(t(en, zh)))
    options.add_row("-h, --help", t("Show help and exit.", "显示帮助并退出。"))
    options.add_row("--lang {zh-CN,en}", t("Interface language (before or after the command).", "界面语言（可放在子命令前后）。"))
    items.append(options)
    if selected:
        examples = table((t("Examples", "示例"),), plain)
        for example in selected.examples:
            examples.add_row(Text(example))
        items.append(examples)
    return Group(*items)

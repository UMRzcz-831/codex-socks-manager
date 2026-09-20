"""Offline Textual design prototype. Never reads real profiles or starts clients."""
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from urllib.parse import urlsplit

from rich.text import Text
from textual import events, on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Checkbox, DataTable, Input, Label, Select, Static

from codex_socks_manager.ui_theme import graphite_theme


CLIENTS = {"claude": "Claude Code CLI", "codex": "Codex CLI"}
SCENES = [
    ("受管启动 · HTTP 配置", "managed"),
    ("直接启动 · 继承父环境", "inherit"),
    ("受管启动 · 客户端配置冲突", "conflict"),
    ("受管启动 · 清除代理变量", "off"),
    ("受管启动 · SOCKS 配置", "socks"),
]
KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")
DEMO_HOST = "api.deepseek.example"


@dataclass(frozen=True)
class Variable:
    key: str
    inherited: str
    launch: str
    adoption: str
    detail: str


def variables(client: str, scene: str, bypass: bool) -> list[Variable]:
    """Labels for synthetic scenarios, not a production environment resolver."""
    result = []
    for key in KEYS:
        if key == "NO_PROXY":
            active = bypass and scene not in {"inherit", "off"}
            result.append(Variable(
                key, "本地 3 项", "本地 + 示例主机" if active else "本地 3 项",
                "逐目标匹配",
                "NO_PROXY / no_proxy：演示中同值。来源：本地规则"
                + (f" + {CLIENTS[client]} 专属规则。\n规则：{DEMO_HOST}（虚构地址，精确匹配）。"
                   if active else "。\n未包含示例 DeepSeek 主机；不等于关闭整个客户端代理。"),
            ))
            continue
        inherited = "父环境 A" if key != "ALL_PROXY" else "父环境 B"
        launch = "office / HTTP"
        adoption = "采用待检查"
        detail = f"{key} / {key.lower()}：演示中同值。父环境的原始设置位置未知。"
        if scene == "inherit":
            launch = "原样继承"
            detail += "\n直接启动：管理器不写入变量；可能仍有代理。"
        elif scene == "off":
            launch = "已清除（计划）"
            detail += "\n大小写均从启动环境移除；不保证客户端文件不会重新设置。"
        else:
            launch = "office / SOCKS" if scene == "socks" else launch
            detail += "\n来源：当前客户端选定的演示 profile；仅影响新受管进程。"
        if key == "ALL_PROXY" and client == "claude":
            adoption = "官方未列支持"
            if scene != "inherit":
                launch = "已清除（计划）"
                detail += "\nClaude 适配计划清除 ALL_PROXY，避免旧值进入子工具。"
            else:
                detail += "\n保留不等于 Claude 采用；子工具可能采用此值。"
        elif client == "claude" and scene == "socks":
            adoption = "不兼容 · 阻止"
        elif scene == "conflict":
            adoption = "文件可能覆盖"
        result.append(Variable(key, inherited, launch, adoption, detail))
    return result


def route(client: str, scene: str, bypass: bool, target: str) -> tuple[str, str]:
    """Demonstrate exact-host matching only, with no I/O or network requests."""
    try:
        parsed = urlsplit(target)
        host = parsed.hostname
        if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
            raise ValueError
        parsed.port
    except ValueError:
        return "输入无效", "请输入 HTTP/HTTPS 目标 URL，不含认证信息。"
    if scene == "socks" and client == "claude":
        return "阻止受管启动 · SOCKS 不兼容", "选择 HTTP/HTTPS profile；绕过项不能解除协议预检失败。"
    if scene == "conflict":
        return "无法确定 · 客户端配置可能覆盖", "发现冲突候选；需确认客户端采用的值，不能承诺本计划获胜。"
    if scene == "off":
        return "启动环境无代理变量", "已计划清除六项变量；客户端文件与实际网络仍待核实。"
    if bypass and scene != "inherit" and host == DEMO_HOST:
        return "预计绕过代理 · 命中 NO_PROXY", f"命中精确规则 {DEMO_HOST}；来源：当前客户端规则。"
    if host in {"localhost", "127.0.0.1", "::1"}:
        return "预计绕过代理 · 本地地址", "命中演示本地绕过规则；客户端采用情况待检查。"
    if scene == "socks":
        return "已计划注入 SOCKS · 采用待检查", "管理器接受该协议；客户端实际支持需按版本和诊断确认。"
    if client == "claude":
        return "预计使用代理 · 未命中绕过", "演示 https_proxy 优先；ALL_PROXY 不作为模型请求的判断依据。"
    return "预计使用代理 · 未命中绕过", "按所选 HTTP 配置预览；客户端采用情况待检查。"


class Detail(Static):
    can_focus = True


class ScopePrototype(App):
    TITLE = "Proxy scope — offline design preview"
    BINDINGS = [
        ("ctrl+q", "quit", "退出"),
        ("f2", "detail", "变量详情"),
        ("f6", "client", "切换客户端"),
        ("f7", "bypass", "示例绕过"),
    ]
    CSS = """
    Screen { background: $g-background; color: $g-text; }
    #heading { height: 2; padding: 0 1; text-style: bold; color: $g-accent; }
    #controls { height: 4; padding: 0 1; }
    .field { width: 1fr; height: 4; }
    #scene-field { margin-left: 1; }
    Label { height: 1; color: $g-muted; }
    Select { width: 1fr; }
    Select > SelectCurrent, Select > SelectOverlay {
        border: solid $g-border; background: $g-surface; color: $g-text;
    }
    Select:focus > SelectCurrent { border: solid $g-accent; }
    #context { height: 2; padding: 0 1; }
    #body { height: 1fr; padding: 0 1; }
    #layout { height: auto; }
    .panel { border: solid $g-border; padding: 0 1; background: $g-surface; height: auto; }
    .panel:focus-within { border: solid $g-accent; }
    #main { width: 65%; min-width: 48; }
    #side { width: 1fr; min-width: 28; margin-left: 1; }
    .section { height: 1; text-style: bold; color: $g-text; }
    #vars { height: 6; background: $g-surface; }
    DataTable > .datatable--header { background: $g-surface; color: $g-text; text-style: bold; }
    DataTable > .datatable--cursor { background: $g-selection; color: $g-text; text-style: bold; }
    #selected { height: auto; min-height: 3; margin-bottom: 1; color: $g-muted; }
    Input { height: 3; border: solid $g-border; background: $g-background; color: $g-text; }
    Input:focus { border: solid $g-accent; }
    Checkbox { height: 1; border: none; background: $g-surface; padding: 0; margin: 0 0 1 0; }
    Checkbox:focus { text-style: reverse; }
    Checkbox:disabled { opacity: 1; color: $g-muted; }
    #route { height: auto; min-height: 4; color: $g-accent; }
    #scope, #sources { height: auto; margin-bottom: 1; }
    #sources { color: $g-muted; }
    #status, #keys { height: 1; padding: 0 1; }
    #status { background: $g-surface; }
    #keys { color: $g-muted; }
    .compact #layout { layout: vertical; }
    .compact #heading, .compact #context { height: 1; }
    .compact #vars { height: 5; }
    .compact Checkbox { margin-bottom: 0; }
    .compact #route { min-height: 3; }
    .compact #main, .compact #side { width: 1fr; min-width: 0; }
    .compact #side { margin: 1 0 0 0; }
    """

    def __init__(self, *, no_color: bool | None = None):
        if no_color is not None:
            if no_color:
                os.environ["NO_COLOR"] = "1"
            else:
                os.environ.pop("NO_COLOR", None)
        super().__init__()
        self.register_theme(graphite_theme())
        self.theme = "graphite"
        self.bypasses = {"claude": True, "codex": False}
        self.selected_key = "NO_PROXY"
        self.rows: list[Variable] = []

    @property
    def client(self) -> str:
        return str(self.query_one("#client", Select).value)

    @property
    def scene(self) -> str:
        return str(self.query_one("#scene", Select).value)

    def compose(self) -> ComposeResult:
        yield Static("CODEX SOCKS MANAGER  /  作用域\n离线设计原型 · 固定演示数据", id="heading")
        with Horizontal(id="controls"):
            with Vertical(classes="field"):
                yield Label("客户端")
                yield Select([(v, k) for k, v in CLIENTS.items()], value="claude", allow_blank=False, id="client")
            with Vertical(classes="field", id="scene-field"):
                yield Label("演示场景 / 启动入口")
                yield Select(SCENES, value="managed", allow_blank=False, id="scene")
        yield Static("", id="context")
        with VerticalScroll(id="body"):
            with Horizontal(id="layout"):
                with Vertical(id="main", classes="panel"):
                    yield Static("变量：父环境 → 新进程启动值", classes="section")
                    yield DataTable(id="vars", cursor_type="row")
                    yield Label("目标请求 URL（虚构 DeepSeek 主机）")
                    yield Input(f"https://{DEMO_HOST}/v1/messages", id="target")
                    yield Checkbox("本客户端绕过示例 DeepSeek 主机", value=True, id="bypass")
                    yield Static("", id="route", markup=False)
                    yield Detail("", id="selected", markup=False)
                with Vertical(id="side", classes="panel"):
                    yield Static("影响范围", classes="section")
                    yield Static("", id="scope", markup=False)
                    yield Static("来源与证据", classes="section")
                    yield Static("", id="sources", markup=False)
        yield Static("演示模式 · 未读取真实配置 · 未联网", id="status")
        yield Static("Tab 焦点  F2 详情  F6 客户端  F7 绕过  Ctrl+Q 退出", id="keys")

    def on_mount(self) -> None:
        self.set_class(self.size.width < 100, "compact")
        self.refresh_preview()
        self.query_one("#vars", DataTable).focus()

    def on_resize(self, event: events.Resize) -> None:
        self.set_class(event.size.width < 100, "compact")
        if self.is_mounted:
            self.call_after_refresh(self.refresh_preview)

    def refresh_preview(self) -> None:
        if not self.query("#vars"):
            return
        client, scene = self.client, self.scene
        self.rows = variables(client, scene, self.bypasses[client])
        table = self.query_one("#vars", DataTable)
        table.clear(columns=True)
        narrow = self.size.width < 100
        if narrow:
            table.add_columns("变量", "启动值", "客户端判断")
        else:
            table.add_columns("变量", "父环境", "启动值", "客户端判断")
        for row in self.rows:
            values = (row.key, row.launch, row.adoption) if narrow else (row.key, row.inherited, row.launch, row.adoption)
            table.add_row(*(Text(value) for value in values), key=row.key)
        table.move_cursor(row=KEYS.index(self.selected_key))
        box = self.query_one("#bypass", Checkbox)
        box.disabled = scene in {"inherit", "off"}
        with self.prevent(Checkbox.Changed):
            box.value = self.bypasses[client]
        entry = "直接启动" if scene == "inherit" else "受管启动预览"
        self.query_one("#context", Static).update(
            f"{entry} · /workspace/demo · 演示快照 / 版本未检测\n"
            "启动环境是计划；客户端采用情况与网络连通单独确认。"
        )
        command = client if scene == "inherit" else f"管理器 → {client}"
        self.query_one("#scope", Static).update(
            f"调用终端（示例快照）\n  └ {command}\n      └ 工具 / MCP\n        可能继承或覆盖\n\n"
            "父终端：不修改\n其他终端：不修改\n已运行会话：不更新\n目录：可提供客户端配置"
        )
        sources = "父环境：已观测（演示）\n原始设置位置：未知\n管理器：当前客户端策略\n客户端状态：未检查"
        if scene == "conflict":
            file_hint = ".claude/settings.local.json" if client == "claude" else ".codex/config.toml"
            sources += f"\n\n[!] 配置候选存在差异\n{file_hint}\n已加载与否：待核实"
        elif scene == "inherit":
            sources += "\n\n直接入口不采用管理器策略。\n环境变量存在不证明来自 Codex。"
        else:
            sources += "\n\n文件检查：假设无覆盖\n只是演示条件，不能代表本机。"
        self.query_one("#sources", Static).update(sources)
        self.update_detail()
        self.update_route()

    def update_detail(self) -> None:
        row = next((row for row in self.rows if row.key == self.selected_key), None)
        if row:
            self.query_one("#selected", Static).update(f"{row.key} · 父环境：{row.inherited}\n{row.detail}")

    def update_route(self) -> None:
        title, reason = route(self.client, self.scene, self.bypasses[self.client], self.query_one("#target", Input).value)
        self.query_one("#route", Static).update(f"{title}\n{reason}\n网络连通：尚未检查")

    @on(Select.Changed)
    def selection_changed(self) -> None:
        if self.is_mounted:
            self.refresh_preview()

    @on(Checkbox.Changed, "#bypass")
    def bypass_changed(self, event: Checkbox.Changed) -> None:
        self.bypasses[self.client] = event.value
        self.refresh_preview()

    @on(Input.Changed, "#target")
    def target_changed(self) -> None:
        if self.is_mounted:
            self.update_route()

    @on(DataTable.RowHighlighted, "#vars")
    def row_changed(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key.value in KEYS:
            self.selected_key = str(event.row_key.value)
            self.update_detail()

    def action_client(self) -> None:
        self.query_one("#client", Select).value = "codex" if self.client == "claude" else "claude"

    def action_detail(self) -> None:
        self.query_one("#selected", Detail).focus()

    def action_bypass(self) -> None:
        box = self.query_one("#bypass", Checkbox)
        if not box.disabled:
            box.value = not box.value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-color", action="store_true", default=None)
    args = parser.parse_args()
    ScopePrototype(no_color=args.no_color).run()

from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual import on, work, events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, DataTable, Input, Label, Select, Static, TabbedContent, TabPane

from .catalog import BY_NAME, COMMANDS, translated
from .doctor import CheckResult
from .operations import Manager
from .paths import Paths
from .presentation import safe_error, display_width
from .ui_presentation import help_view
from .ui_theme import COLORS, graphite_theme
from .profiles import validate_name, validate_url
from .progress import STAGES


class Pane(VerticalScroll):
    # A hidden page must not regain focus via a sibling scroll container while
    # TabbedContent hides the previously focused table. Children remain focusable.
    can_focus = False


class Detail(Static):
    can_focus = True
    BINDINGS = [("down", "down", "Scroll"), ("up", "up", "Scroll"),
                ("pagedown", "page_down", "Scroll"), ("pageup", "page_up", "Scroll")]

    def action_down(self):
        self.parent.scroll_relative(y=1, animate=False)

    def action_up(self):
        self.parent.scroll_relative(y=-1, animate=False)

    def action_page_down(self):
        self.parent.scroll_relative(y=8, animate=False)

    def action_page_up(self):
        self.parent.scroll_relative(y=-8, animate=False)


class RevealCheckbox(Checkbox):
    def render(self):
        # Default Checkbox distinguishes on/off by color alone. Use explicit
        # brackets and a changing glyph, including in NO_COLOR terminals.
        return Text(("[x] " if self.value else "[ ] ") + self.label.plain)


class Confirm(ModalScreen[bool]):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, title: str, body: str, lang: str):
        super().__init__()
        self.heading, self.body, self.lang = title, body, lang

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="dialog"):
            yield Label(Text(self.heading), classes="dialog-title")
            yield Static(Text(self.body))
            with Horizontal(classes="buttons"):
                yield Button(translated(self.lang, "Cancel", "取消"), id="cancel")
                yield Button(translated(self.lang, "Confirm", "确认"), id="confirm", variant="warning")

    def on_mount(self) -> None:
        self.query_one("#cancel", Button).focus()

    def action_cancel(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed)
    def choose(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")


class OperationResult(ModalScreen[None]):
    """Full, scrollable result, also reachable while a worker is running."""
    BINDINGS = [("escape", "close", "Close"), ("f2", "close", "Close")]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="dialog"):
            yield Label(self.app.t("Operation result", "操作结果"), classes="dialog-title")
            yield Detail(Text(self.app.full_status()), id="result-detail")
            yield Button(self.app.t("Close", "关闭"), id="close-result")

    def action_close(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#close-result")
    def close_result(self) -> None:
        self.action_close()


class OperationForm(ModalScreen[dict | None]):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, command: str, lang: str, name: str = "", url: str = "",
                 snapshots: list[Path] | None = None):
        super().__init__()
        self.command, self.lang = command, lang
        self.profile_name, self.profile_url = name, url
        self.snapshots = snapshots or []

    def t(self, en: str, zh: str) -> str:
        return translated(self.lang, en, zh)

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="dialog"):
            yield Label(Text(BY_NAME[self.command].text("summary", self.lang)), classes="dialog-title")
            if self.command in {"add", "edit"}:
                yield Label(self.t("Profile name", "配置名称"))
                yield Input(self.profile_name, id="profile-name", disabled=self.command == "edit")
                yield Label(self.t("Proxy URL (explicit port required)", "代理 URL（必须包含端口）"))
                yield Input(self.profile_url, password=True, id="profile-url", placeholder="socks5://proxy.example:1080")
                yield RevealCheckbox(self.t("Show URL", "显示 URL"), id="reveal-url")
                yield Static(self.t("Saving does not apply the profile.", "保存不会自动应用配置。"))
            elif self.command == "restore":
                yield Label(self.t("Local snapshots", "本地快照"))
                yield Select([(path.name, str(path)) for path in self.snapshots],
                             prompt=self.t("Choose a snapshot", "选择快照"), id="snapshot-choice")
                yield Label(self.t("Snapshot path (blank = latest known-good)", "快照路径（留空使用最新 known-good）"))
                yield Input(id="snapshot-path", placeholder="/path/to/snapshot")
            else:
                yield Static(Text(BY_NAME[self.command].text("detail", self.lang)))
                yield Label(self.t("JP file (optional)", "JP 文件（可选）"))
                yield Input(id="jp-path", placeholder="/path/to/jp.env")
                yield Label(self.t("US file (optional)", "US 文件（可选）"))
                yield Input(id="us-path", placeholder="/path/to/us.env")
            yield Static("", id="form-error")
            with Horizontal(classes="buttons"):
                yield Button(self.t("Cancel", "取消"), id="cancel")
                yield Button(self.t("Save" if self.command in {"add", "edit"} else "Continue",
                                    "保存" if self.command in {"add", "edit"} else "继续"),
                             id="submit", variant="primary")

    def on_mount(self) -> None:
        if self.command in {"add", "edit"}:
            self.query_one("#profile-url" if self.command == "edit" else "#profile-name", Input).focus()

    @on(Checkbox.Changed, "#reveal-url")
    def reveal(self, event: Checkbox.Changed) -> None:
        self.query_one("#profile-url", Input).password = not event.value

    @on(Select.Changed, "#snapshot-choice")
    def select_snapshot(self, event: Select.Changed) -> None:
        if event.value is not Select.BLANK:
            self.query_one("#snapshot-path", Input).value = str(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed)
    def submit(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.action_cancel()
            return
        if event.button.id != "submit":
            return
        try:
            if self.command in {"add", "edit"}:
                result = {"name": validate_name(self.query_one("#profile-name", Input).value.strip()),
                          "url": validate_url(self.query_one("#profile-url", Input).value.strip())}
            elif self.command == "restore":
                value = self.query_one("#snapshot-path", Input).value.strip()
                result = {"snapshot": Path(value).expanduser() if value else None}
            else:
                result = {}
                for key in ("jp", "us"):
                    value = self.query_one(f"#{key}-path", Input).value.strip()
                    result[key] = Path(value).expanduser() if value else None
        except ValueError as error:
            self.query_one("#form-error", Static).update(Text(safe_error(error)))
            return
        self.dismiss(result)


class ManagerApp(App):
    CSS_PATH = "manager.tcss"
    TITLE = "Codex SOCKS Manager"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("a", "add", "Add", show=False),
        Binding("e", "edit", "Edit", show=False),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("l", "language", "Language", show=False),
        Binding("q", "quit", "Quit", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False, priority=True),
        Binding("f2", "result", "Result", show=False),
    ]

    def __init__(self, paths: Paths, lang: str = "en", manager: Manager | None = None):
        super().__init__()
        self.register_theme(graphite_theme())
        self.theme = "graphite"
        self.manager = manager or Manager(paths)
        self.lang = lang
        self.busy = False
        self.selected_name: str | None = None
        self.profiles: list[dict[str, object]] = []
        self.last_check: CheckResult | None = None
        self.check_stale = False
        self.last_stage: str | None = None
        self.status_message = ("Ready.", "就绪。")
        self.status_error = False
        self.command_names: list[str] = []

    def t(self, en: str, zh: str) -> str:
        return translated(self.lang, en, zh)

    def button(self, operation: str, en: str, zh: str, variant: str = "default") -> Button:
        return Button(self.t(en, zh), id=f"op-{operation}", classes="operation", variant=variant)

    def compose(self) -> ComposeResult:
        yield Static("", id="masthead")
        yield Static("", id="size-warning")
        with TabbedContent(id="pages"):
            with TabPane(self.t("Profiles", "代理管理"), id="profiles-page"):
                with Pane(id="profile-layout"):
                    yield DataTable(id="profiles", cursor_type="row")
                    with Pane(id="profile-side", classes="panel"):
                        yield Detail("", id="profile-detail")
                        with Horizontal(classes="buttons"):
                            yield self.button("use", "Apply", "应用", "primary")
                            yield self.button("edit", "Edit", "编辑")
                        with Horizontal(classes="buttons"):
                            yield self.button("add", "Add", "新增")
                            yield self.button("off", "Off", "关闭")
                            yield self.button("del", "Delete", "删除")
            with TabPane(self.t("Diagnostics", "诊断"), id="diagnostics-page"):
                with Pane(id="diagnostic-layout", classes="split"):
                    with Pane(id="diagnostic-main", classes="panel primary-pane"):
                        yield Detail("", id="diagnostics")
                        yield self.button("check", "Run Doctor", "运行 Doctor", "primary")
                    with Pane(id="diagnostic-side", classes="panel detail-pane"):
                        yield Detail("", id="diagnostic-note")
            with TabPane(self.t("Maintenance", "维护"), id="maintenance-page"):
                with Pane(id="maintenance-layout", classes="panel"):
                    yield Static("", id="maintenance-note")
                    with Vertical(classes="maintenance-group"):
                        yield Static("Launcher", classes="section-title")
                        yield Static("", id="launcher-hint", classes="group-hint")
                        yield self.button("install", "Repair launcher", "修复 launcher")
                    with Vertical(classes="maintenance-group"):
                        yield Static("", id="backup-label", classes="section-title")
                        yield Static("", id="backup-hint", classes="group-hint")
                        with Horizontal(classes="buttons"):
                            yield self.button("backup", "Backup", "备份")
                            yield self.button("restore", "Restore", "恢复")
                    with Vertical(classes="maintenance-group"):
                        yield Static("", id="update-label", classes="section-title")
                        yield Static("", id="update-hint", classes="group-hint")
                        with Horizontal(classes="buttons"):
                            yield self.button("safe-update", "Safe update", "安全更新")
                            yield self.button("migrate-legacy", "Import legacy", "导入旧配置")
            with TabPane(self.t("Commands", "命令手册"), id="commands-page"):
                with Pane(id="command-layout", classes="split"):
                    with Vertical(id="command-main", classes="primary-pane panel"):
                        yield Input(placeholder=self.t("Filter commands…", "筛选命令…"), id="command-filter")
                        yield DataTable(id="commands", cursor_type="row")
                    with Pane(id="command-side", classes="detail-pane panel"):
                        yield Detail("", id="command-detail")
        yield Static("", id="status")
        yield Static("", id="keys")

    def on_mount(self) -> None:
        self.set_class(self.size.width < 100, "compact")
        self.update_language()
        self.query_one("#profiles", DataTable).focus()

    def on_resize(self, event: events.Resize) -> None:
        self.set_class(event.size.width < 100, "compact")
        self.set_class(event.size.width < 80 or event.size.height < 24, "undersized")
        if self.is_mounted and self.query("#commands"):
            self.call_after_refresh(self.resize_tables)

    def resize_tables(self) -> None:
        active = self.query_one("#pages", TabbedContent).active
        if active == "profiles-page":
            self.refresh_profiles()
        elif active == "commands-page":
            self.refresh_commands()

    @on(TabbedContent.TabActivated)
    def page_activated(self) -> None:
        self.call_after_refresh(self.resize_tables)

    def action_result(self) -> None:
        if len(self.screen_stack) == 1:
            self.push_screen(OperationResult())

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in {"add", "edit", "refresh", "language"}:
            return not self.busy and not isinstance(self.focused, (Input, Select)) and len(self.screen_stack) == 1
        return True

    def action_quit(self) -> None:
        if self.busy:
            self.notify(self.t("Wait for the operation and recovery to finish.", "请等待操作及恢复结束。"), severity="warning")
        else:
            self.exit()

    def action_language(self) -> None:
        self.lang = "en" if self.lang == "zh-CN" else "zh-CN"
        self.update_language()

    def update_language(self) -> None:
        pages = self.query_one("#pages", TabbedContent)
        for page, en, zh in (
            ("profiles", "Profiles", "代理管理"), ("diagnostics", "Diagnostics", "诊断"),
            ("maintenance", "Maintenance", "维护"), ("commands", "Commands", "命令手册")):
            pages.get_tab(f"{page}-page").label = self.t(en, zh)
        labels = {
            "add": ("Add", "新增"), "edit": ("Edit", "编辑"), "use": ("Apply", "应用"),
            "off": ("Off", "关闭"), "del": ("Delete", "删除"), "check": ("Run Doctor", "运行 Doctor"),
            "install": ("Repair launcher", "修复 launcher"), "backup": ("Backup", "备份"),
            "restore": ("Restore", "恢复"), "safe-update": ("Safe update", "安全更新"),
            "migrate-legacy": ("Import legacy", "导入旧配置"),
        }
        for command, label in labels.items():
            self.query_one(f"#op-{command}", Button).label = "[" + self.t(*label) + "]"
        for widget, en, zh in (
            ("profiles", "Profiles", "代理配置"), ("profile-side", "Selected profile", "所选配置"),
            ("diagnostic-main", "Check results", "检查结果"), ("diagnostic-side", "Interpretation", "说明"),
            ("maintenance-layout", "Maintenance", "维护操作"), ("command-main", "Commands", "命令目录"),
            ("command-side", "Command details", "命令详情")):
            self.query_one(f"#{widget}").border_title = self.t(en, zh)
        self.query_one("#size-warning", Static).update(self.t("Terminal too small: use at least 80 × 24. q to quit.", "终端过小：请至少使用 80 × 24。q 退出。"))
        self.query_one("#backup-label", Static).update(self.t("Backup / Restore", "备份与恢复"))
        self.query_one("#update-label", Static).update(self.t("Update / Migration", "更新与迁移"))
        for widget, en, zh in (
            ("launcher-hint", "Find Codex and replace the managed launcher.", "发现 Codex，替换受管 launcher。"),
            ("backup-hint", "Private snapshots; restore does not downgrade Codex.", "私密快照；恢复不会降级 Codex。"),
            ("update-hint", "Update with validation; import without changing the active profile.", "更新后验收；导入不改变活动配置。")):
            self.query_one(f"#{widget}", Static).update(self.t(en, zh))
        self.query_one("#command-filter", Input).placeholder = self.t("Filter commands…", "筛选命令…")
        self.query_one("#keys", Static).update(self.t(
            "a Add  e Edit  r Refresh  l 中文  q Quit  F2 Result | Tab / arrows / Enter",
            "a 新增 e 编辑 r 刷新 l English q 退出 F2 结果 | Tab / 方向键 / Enter"))
        self.query_one("#maintenance-note", Static).update(self.t(
            "Snapshots contain credentials. Restore keeps the installed Codex binary. Restarting app-server may interrupt sessions.",
            "快照含凭据，请私密保存。恢复保留当前 Codex 二进制；重启 app-server 可能中断会话。"))
        self.query_one("#diagnostic-note", Static).update(self.t(
            "Doctor categories are diagnostic hints. Account, region, workspace and ACL restrictions still apply.",
            "Doctor 分类是排查线索。账号、地区、workspace 和 ACL 限制仍然适用。"))
        self.refresh_profiles()
        self.refresh_commands()
        self.render_diagnostics()
        self.render_status()

    def action_refresh(self) -> None:
        if not self.busy:
            self.refresh_profiles()
            # Local refresh cannot attest that a previous diagnostic is still current.
            if self.last_check:
                self.check_stale = True
                self.render_diagnostics()

    def refresh_profiles(self) -> None:
        try:
            self.profiles = self.manager.store.list()
            active = self.manager.active
        except (ValueError, OSError) as error:
            self.set_status(("Unable to load profiles: " + safe_error(error), "读取配置失败：" + safe_error(error)), True)
            return
        self.query_one("#masthead", Static).update(Text(
            f"Codex SOCKS Manager\n{self.t('Active', '当前')}: {safe_error(active)}  |  {self.lang}", style="bold"))
        listing = self.query_one("#profiles", DataTable)
        listing.clear(columns=True)
        width = max(42, (listing.container_size.width or int(self.size.width * (0.65 if self.size.width >= 100 else 1))) - 12)
        widths = (10, 12, 8, max(4, width - 30))
        for label, size in zip((self.t(en, zh) for en, zh in (
                ("State", "状态"), ("Name", "名称"), ("Protocol", "协议"), ("Proxy address", "代理地址"))), widths):
            listing.add_column(label, width=size)
        names = [str(item["name"]) for item in self.profiles]
        if self.selected_name not in names:
            self.selected_name = names[0] if names else None
        for item in self.profiles:
            style = "bold" if item["active"] else ""
            listing.add_row(Text(self.t("* Active", "* 当前") if item["active"] else "—", style=style),
                            Text(str(item["name"]), style=style), Text(str(item["scheme"])),
                            Text(str(item["url"])), key=str(item["name"]), height=None)
        if self.selected_name:
            listing.move_cursor(row=names.index(self.selected_name), scroll=False)
        self.update_profile_markers()
        self.render_profile_detail()

    def update_profile_markers(self) -> None:
        listing = self.query_one("#profiles", DataTable)
        if not listing.columns:
            return
        column = next(iter(listing.columns))
        for item in self.profiles:
            prefix = "> " if item["name"] == self.selected_name else "  "
            label = self.t("* Active", "* 当前") if item["active"] else "—"
            listing.update_cell(str(item["name"]), column, Text(prefix + label, style="bold" if item["active"] else ""))

    def render_profile_detail(self) -> None:
        item = next((item for item in self.profiles if item["name"] == self.selected_name), None)
        if item:
            description = f"{item['name']} · {item['scheme']}\n{item['url']}\n" + self.t(
                "Select Apply to restart and validate. Editing only saves the profile.",
                "选择“应用”以重启并验收；编辑仅保存配置。")
        else:
            description = self.t("No profiles yet. Choose Add to save your first proxy.",
                                 "暂无配置。选择“新增”保存第一个代理。")
        self.query_one("#profile-detail", Static).update(Text(description))
        for command in ("edit", "use", "del"):
            self.query_one(f"#op-{command}", Button).disabled = self.busy or item is None

    @on(DataTable.RowHighlighted, "#profiles")
    def profile_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if any(item["name"] == event.row_key.value for item in self.profiles):
            self.selected_name = event.row_key.value
            self.update_profile_markers()
            self.render_profile_detail()

    @on(DataTable.RowSelected, "#profiles")
    def profile_selected(self) -> None:
        self.request_operation("use")

    @on(Input.Changed, "#command-filter")
    def filter_commands(self) -> None:
        self.refresh_commands()

    def refresh_commands(self) -> None:
        term = self.query_one("#command-filter", Input).value.casefold()
        listing = self.query_one("#commands", DataTable)
        listing.clear(columns=True)
        available = max(24, (listing.container_size.width or int(self.size.width * (0.65 if self.size.width >= 100 else 1))) - 12)
        widths = (available // 4, available // 3, available - available // 4 - available // 3)
        for label, width in zip((self.t("Command", "命令"), self.t("Description", "功能"), self.t("Example", "示例")), widths):
            listing.add_column(label, width=width)
        entries = [entry for entry in COMMANDS if term in " ".join((entry.name, *entry.summary)).casefold()]
        self.command_names = [entry.name for entry in entries]
        for entry in entries:
            listing.add_row(Text(entry.usage), Text(entry.text("summary", self.lang)),
                            Text(entry.examples[0]), key=entry.name, height=None)
        self.query_one("#command-detail", Static).update(
            help_view(self.lang, entries[0].name) if entries else Text(self.t("No matching commands.", "没有匹配命令。")))

    @on(DataTable.RowHighlighted, "#commands")
    def command_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key.value in self.command_names:
            self.query_one("#command-detail", Static).update(help_view(self.lang, event.row_key.value))

    def render_diagnostics(self) -> None:
        if self.last_check is None:
            view = Text(self.t("Not checked yet", "尚未检查") + "\n\n", style="bold")
            for label in ("HTTPS", "WSS", "app-server", self.t("Proxy environment", "代理环境")):
                view.append(label + " " * (18 - display_width(label)) + " — " + self.t("Not checked", "尚未检查") + "\n", style="none")
        else:
            result = self.last_check
            headline = self.t("Previous result — refresh required", "历史结果 — 需要重新检查") if self.check_stale else self.t(
                "Healthy" if result.ok else "Needs attention", "正常" if result.ok else "需要检查")
            view = Text(("! " if self.check_stale or not result.ok else "✓ ") + headline + "\n\n",
                        style=COLORS["warning"] if self.check_stale or not result.ok else COLORS["text"])
            for label, value in (("HTTPS", result.https), ("WSS", result.wss), ("app-server", result.app_server),
                                 (self.t("Proxy environment", "代理环境"), result.proxy_env),
                                 (self.t("Category", "分类"), result.category)):
                view.append(f"{label}: {safe_error(value)}\n")
            view.append("\n" + safe_error(result.detail))
        self.query_one("#diagnostics", Static).update(view)

    def action_add(self) -> None:
        self.request_operation("add")

    def action_edit(self) -> None:
        self.request_operation("edit")

    @on(Button.Pressed, ".operation")
    def operation_clicked(self, event: Button.Pressed) -> None:
        self.request_operation(event.button.id.removeprefix("op-"))

    def request_operation(self, command: str) -> None:
        if self.busy:
            return
        if command in {"edit", "use", "del"} and not self.selected_name:
            return
        if command in {"add", "edit", "restore", "migrate-legacy"}:
            try:
                url = self.manager.store.get(self.selected_name) if command == "edit" else ""
                snapshots = self.manager.snapshots() if command == "restore" else []
            except (ValueError, OSError) as error:
                self.set_status((safe_error(error), safe_error(error)), True)
                return
            form = OperationForm(command, self.lang, (self.selected_name or "") if command == "edit" else "", url, snapshots)
            self.push_screen(form, lambda values: self.form_finished(command, values))
        elif command in {"check", "backup"}:
            self.start_operation(command, {})
        else:
            kwargs = {"name": self.selected_name} if command in {"use", "del"} else {}
            if command == "del":
                kwargs["force"] = True
            self.confirm_operation(command, kwargs)

    def form_finished(self, command: str, values: dict | None) -> None:
        if values is not None:
            if command in {"add", "edit"}:
                self.start_operation(command, values)
            else:
                self.confirm_operation(command, values)

    def confirm_operation(self, command: str, kwargs: dict) -> None:
        entry = BY_NAME[command]
        target = "\n".join(f"{key}: {value}" for key, value in kwargs.items() if value is not None)
        self.push_screen(Confirm(entry.text("summary", self.lang), entry.text("detail", self.lang) + "\n\n" + target, self.lang),
                         lambda confirmed: self.start_operation(command, kwargs) if confirmed else None)

    def start_operation(self, command: str, kwargs: dict) -> None:
        if self.busy:
            return
        self.busy = True
        if self.last_check:
            self.check_stale = True
            self.render_diagnostics()
        self.last_stage = "working"
        self.status_error = False
        for button in self.query(".operation"):
            button.disabled = True
        self.render_status()
        self.execute_operation(command, kwargs)

    @work(thread=True, exit_on_error=False)
    def execute_operation(self, command: str, kwargs: dict) -> None:
        try:
            result = self.manager.execute(command, **kwargs,
                                          progress=lambda stage: self.call_from_thread(self.show_stage, stage))
        except Exception as error:
            self.call_from_thread(self.operation_finished, command, None, safe_error(error))
        else:
            self.call_from_thread(self.operation_finished, command, result, None)

    def show_stage(self, stage: str) -> None:
        self.last_stage = stage
        self.render_status()

    def operation_finished(self, command: str, result, error: str | None) -> None:
        self.busy = False
        for button in self.query(".operation"):
            button.disabled = False
        if command != "check" and self.last_check:
            self.check_stale = True
        if error:
            recovery = STAGES.get(self.last_stage, ("", "")) if self.last_stage in {"rolled_back", "rollback_failed"} else ("", "")
            self.set_status((f"Failed: {error} {recovery[0]}", f"失败：{error} {recovery[1]}"), True)
        elif command == "check":
            self.last_check, self.check_stale = result, False
            self.set_status(("Doctor completed.", "Doctor 检查完成。"), not result.ok)
        elif command == "edit":
            self.set_status(("Saved. Apply the profile to restart and validate.", "已保存。请另行应用以重启并验收。"))
        else:
            detail = str(result) if isinstance(result, Path) else ", ".join(result) if isinstance(result, list) else ""
            self.set_status((f"{command}: completed. {detail}", f"{command}：已完成。{detail}"))
        self.refresh_profiles()
        self.render_diagnostics()

    def set_status(self, message: tuple[str, str], error: bool = False) -> None:
        self.last_stage = None
        self.status_message, self.status_error = message, error
        self.render_status()

    def render_status(self) -> None:
        message = STAGES.get(self.last_stage, self.status_message)
        text = ("! " if self.status_error else "… " if self.busy else "· ") + self.t(*message)
        self.query_one("#status", Static).update(Text(text, overflow="ellipsis", no_wrap=True,
                                                      style=COLORS["error"] if self.status_error else ""))
        if isinstance(self.screen, OperationResult):
            self.screen.query_one("#result-detail", Static).update(Text(self.full_status()))

    def full_status(self) -> str:
        return safe_error(self.t(*STAGES.get(self.last_stage, self.status_message)))

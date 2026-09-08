from __future__ import annotations

import threading
from pathlib import Path

import pytest
from textual.widgets import Button, Checkbox, DataTable, Input, Select, Static, TabbedContent

from codex_socks_manager.doctor import CheckResult
from codex_socks_manager.operations import Manager
from codex_socks_manager.profiles import ProfileStore
from codex_socks_manager.tui import Confirm, ManagerApp, OperationForm, OperationResult


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [(80, 24), (120, 36)])
@pytest.mark.parametrize("lang", ["en", "zh-CN"])
async def test_navigation_language_and_table(manager_paths, size, lang):
    store = ProfileStore(manager_paths)
    store.add("office", "socks5://alice:example-password@proxy.example:1080")
    store.set_active("office")
    app = ManagerApp(manager_paths, lang)
    async with app.run_test(size=size) as pilot:
        await pilot.pause()
        table = app.query_one("#profiles", DataTable)
        assert len(table.columns) == 4 and table.row_count == 1
        assert "example-password" not in str(table.get_row("office"))
        assert app.has_class("compact") == (size[0] < 100)
        for page in ("diagnostics", "maintenance", "commands", "profiles"):
            app.query_one("#pages", TabbedContent).active = f"{page}-page"
            await pilot.pause()
            assert app.query_one("#pages", TabbedContent).active == f"{page}-page"
        table.focus()
        await pilot.press("l")
        assert app.lang != lang
        assert app.selected_name == "office"
        app.query_one("#pages", TabbedContent).active = "commands-page"
        await pilot.pause()
        commands = app.query_one("#commands", DataTable)
        assert commands.max_scroll_x == 0
        field = app.query_one("#command-filter", Input)
        field.focus()
        await pilot.press("a", "e", "r", "l", "q")
        assert field.value == "aerlq"
        assert len(app.screen_stack) == 1
        field.value = "restore"
        await pilot.pause()
        assert app.query_one("#commands", DataTable).row_count == 1


@pytest.mark.asyncio
async def test_form_validation_save_edit_and_cancel(manager_paths):
    app = ManagerApp(manager_paths)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, OperationForm)
        app.screen.query_one("#profile-name", Input).value = "../bad"
        app.screen.query_one("#profile-url", Input).value = "ftp://proxy.example:21"
        app.screen.query_one("#submit", Button).press()
        await pilot.pause()
        assert isinstance(app.screen, OperationForm)
        assert app.manager.store.list() == []
        app.screen.query_one("#profile-name", Input).value = "office"
        url = app.screen.query_one("#profile-url", Input)
        assert url.password
        reveal = app.screen.query_one("#reveal-url", Checkbox)
        assert "[ ]" in str(reveal.render())
        reveal.value = True
        await pilot.pause()
        assert not url.password and "[x]" in str(reveal.render())
        reveal.value = False
        await pilot.pause()
        assert url.password
        url.value = "http://proxy.example:8080"
        app.screen.query_one("#submit", Button).press()
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert app.manager.store.get("office") == "http://proxy.example:8080"
        app.request_operation("edit")
        await pilot.pause()
        app.screen.query_one("#profile-url", Input).value = "socks5://proxy.example:1080"
        app.screen.query_one("#submit", Button).press()
        await pilot.pause()
        await app.workers.wait_for_complete()
        assert app.manager.store.get("office") == "socks5://proxy.example:1080"
        assert app.manager.active == "off"
        app.request_operation("del")
        await pilot.pause()
        assert isinstance(app.screen, Confirm)
        await pilot.press("escape")
        await pilot.pause()
        assert app.manager.store.get("office")


@pytest.mark.asyncio
async def test_background_gate_error_and_diagnostics(manager_paths, monkeypatch):
    app = ManagerApp(manager_paths)
    entered, release = threading.Event(), threading.Event()
    calls = []

    def execute(command, **kwargs):
        calls.append(command)
        entered.set()
        release.wait(5)
        kwargs["progress"]("rollback")
        kwargs["progress"]("rollback_failed")
        raise RuntimeError("failed http://alice:example-password@proxy.example:8080")

    monkeypatch.setattr(app.manager, "execute", execute)
    async with app.run_test() as pilot:
        app.start_operation("use", {"name": "office"})
        await pilot.pause()
        assert entered.is_set() and app.busy
        app.start_operation("off", {})
        app.action_quit()
        assert calls == ["use"] and app.is_running
        assert app.query_one("#op-add", Button).disabled
        release.set()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert not app.busy
        assert "example-password" not in str(app.status_message)
        assert "Recovery failed" in app.status_message[0]
        result = CheckResult(True, "ok", "ok", "101", "ok", "ok")
        monkeypatch.setattr(app.manager, "execute", lambda *args, **kwargs: result)
        app.start_operation("check", {})
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert app.last_check.ok and not app.check_stale
        app.action_refresh()
        assert app.check_stale


@pytest.mark.asyncio
@pytest.mark.parametrize("command", ["use", "off", "del", "install", "backup", "restore", "safe-update", "migrate-legacy", "check"])
async def test_all_operation_routes(manager_paths, monkeypatch, command):
    manager = Manager(manager_paths)
    manager.store.add("office", "http://proxy.example:8080")
    calls = []

    def execute(operation, **kwargs):
        calls.append((operation, kwargs))
        return CheckResult(True, "ok", "ok", "101", "ok", "ok") if operation == "check" else None

    monkeypatch.setattr(manager, "execute", execute)
    app = ManagerApp(manager_paths, manager=manager)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.request_operation(command)
        await pilot.pause()
        if command in {"restore", "migrate-legacy"}:
            assert isinstance(app.screen, OperationForm)
            if command == "restore":
                app.screen.query_one("#snapshot-path", Input).value = "/tmp/example-snapshot"
            else:
                app.screen.query_one("#jp-path", Input).value = "/tmp/example.env"
            app.screen.query_one("#submit", Button).press()
            await pilot.pause()
        if command not in {"check", "backup"}:
            assert calls == [] and isinstance(app.screen, Confirm)
            app.screen.query_one("#confirm", Button).press()
            await pilot.pause()
        await app.workers.wait_for_complete()
        assert len(calls) == 1 and calls[0][0] == command
        if command == "restore":
            assert calls[0][1]["snapshot"] == Path("/tmp/example-snapshot")
        if command == "migrate-legacy":
            assert calls[0][1]["jp"] == Path("/tmp/example.env") and calls[0][1]["us"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [(80, 24), (120, 36)])
async def test_mouse_controls_and_snapshot_selection(manager_paths, size):
    app = ManagerApp(manager_paths, "zh-CN")
    snapshot = manager_paths.backups / "known-good-example"
    snapshot.mkdir(parents=True)
    (snapshot / "manifest.json").write_text("{}")
    async with app.run_test(size=size) as pilot:
        await pilot.pause()
        add = app.query_one("#op-add", Button)
        add.scroll_visible(animate=False)
        await pilot.pause()
        assert await pilot.click("#op-add")
        await pilot.pause()
        assert isinstance(app.screen, OperationForm)
        cancel = app.screen.query_one("#cancel", Button)
        cancel.scroll_visible(animate=False)
        await pilot.pause()
        assert await pilot.click("#cancel")
        await pilot.pause()
        pages = app.query_one("#pages", TabbedContent)
        assert await pilot.click("#" + pages.get_tab("maintenance-page").id)
        await pilot.wait_for_scheduled_animations()
        assert pages.active == "maintenance-page"
        assert await pilot.click("#op-restore")
        await pilot.pause()
        app.screen.query_one("#snapshot-choice", Select).value = str(snapshot)
        await pilot.pause()
        assert app.screen.query_one("#snapshot-path", Input).value == str(snapshot)
        await pilot.press("escape")
        await pilot.pause()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("no_color", [False, True])
async def test_responsive_focus_markers_and_long_results(manager_paths, monkeypatch, no_color):
    if no_color:
        monkeypatch.setenv("NO_COLOR", "1")
    else:
        monkeypatch.delenv("NO_COLOR", raising=False)
    manager = Manager(manager_paths)
    manager.store.add("office", "socks5://proxy.example:1080")
    long_url = "http://" + "long-proxy-" * 10 + "host.example:8080"
    manager.store.add("local", long_url)
    manager.store.set_active("office")
    app = ManagerApp(manager_paths, "zh-CN", manager=manager)
    async with app.run_test(size=(120, 36)) as pilot:
        await pilot.pause()
        for width, height in ((120, 36), (80, 24), (120, 36), (80, 24)):
            await pilot.resize_terminal(width, height)
            await pilot.pause()
            table = app.query_one("#profiles", DataTable)
            side = app.query_one("#profile-side")
            assert app.has_class("compact") == (width < 100)
            if width >= 100:
                ratio = table.region.width / (table.region.width + side.region.width)
                assert abs(ratio - .65) <= .065
                assert table.region.y == side.region.y
            else:
                assert table.region.y < side.region.y
            assert app.query_one("#status").region.height == 1
            assert app.query_one("#keys").region.bottom <= height
            table.focus()
            table.move_cursor(row=0)
            await pilot.pause()
            assert app.selected_name == "local" and manager.active == "office"
            assert ">" in str(table.get_row("local")[0])
            assert "*" in str(table.get_row("office")[0])
            assert long_url in str(app.query_one("#profile-detail", Static).render())
            for command in ("add", "edit", "use", "off", "del"):
                button = app.query_one(f"#op-{command}", Button)
                button.focus()
                button.scroll_visible(animate=False)
                await pilot.pause()
                assert 0 <= button.region.y < height - 2
        message = "failed http://alice:example-password@proxy.example:8080 " + "details " * 100 + "END"
        from codex_socks_manager.presentation import safe_error
        app.set_status((safe_error(message), safe_error(message)), True)
        await pilot.press("f2")
        await pilot.pause()
        assert isinstance(app.screen, OperationResult)
        detail = app.screen.query_one("#result-detail", Static)
        assert "END" in str(detail.render()) and "example-password" not in str(detail.render())
        detail.focus()
        await pilot.press("pagedown")
        assert detail.parent.scroll_y > 0
        await pilot.press("escape")
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_default_diagnostics_and_confirm_focus(manager_paths):
    manager = Manager(manager_paths)
    manager.store.add("office", "http://proxy.example:8080")
    app = ManagerApp(manager_paths, manager=manager)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        diagnostics = str(app.query_one("#diagnostics", Static).render())
        for label in ("HTTPS", "WSS", "app-server", "Proxy environment", "Not checked"):
            assert label in diagnostics
        app.request_operation("use")
        await pilot.pause()
        assert app.focused.id == "cancel"
        await pilot.press("escape")
        assert manager.active == "off"

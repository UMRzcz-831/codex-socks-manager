from __future__ import annotations

import json
import sys

import pytest

from codex_socks_manager.catalog import COMMANDS, language
from codex_socks_manager.cli import run
from codex_socks_manager.doctor import CheckResult
from codex_socks_manager.profiles import ProfileStore


@pytest.mark.parametrize("lang", ["en", "zh-CN"])
@pytest.mark.parametrize("command", [None, *(entry.name for entry in COMMANDS)])
def test_every_help_has_examples_without_initializing_storage(manager_paths, capsys, command, lang):
    args = ([command] if command else []) + ["-h", "--lang", lang]
    with pytest.raises(SystemExit) as result:
        run(args, manager_paths)
    assert result.value.code == 0
    output = capsys.readouterr().out
    assert ("示例" if lang == "zh-CN" else "Example") in output
    assert "--no-restart" not in output
    assert "\x1b" not in output
    assert not manager_paths.settings.exists()
    if command:
        assert command in output


def test_language_priority():
    env = {"CODEX_SOCKS_LANG": "en", "LC_ALL": "zh_CN.UTF-8", "LANG": "en_US"}
    assert language("zh-CN", env) == "zh-CN"
    assert language(None, env) == "en"
    env.pop("CODEX_SOCKS_LANG")
    assert language(None, env) == "zh-CN"
    assert language(None, {}) == "en"
    assert language(None, {"LC_MESSAGES": "zh_TW.UTF-8", "LANG": "en"}) == "zh-CN"


@pytest.mark.parametrize("prefix,suffix", [(["--lang", "zh-CN"], []), ([], ["--lang", "zh-CN"])])
def test_list_language_and_empty_header(manager_paths, capsys, prefix, suffix):
    assert run(prefix + ["list"] + suffix, manager_paths) == 0
    output = capsys.readouterr().out
    for heading in ("状态", "名称", "协议", "代理地址", "暂无配置"):
        assert heading in output


def test_noninteractive_entrypoints_do_not_initialize(manager_paths, capsys, monkeypatch):
    monkeypatch.setattr("codex_socks_manager.cli.interactive", lambda: False)
    assert run([], manager_paths) == 0
    assert "Example" in capsys.readouterr().out
    assert run(["tui"], manager_paths) == 2
    assert "interactive terminal" in capsys.readouterr().err
    assert not manager_paths.settings.exists()


@pytest.mark.parametrize("args", [[], ["tui"], ["--lang", "zh-CN"]])
def test_interactive_entry_dispatch(manager_paths, monkeypatch, args):
    called = []
    class FakeApp:
        def __init__(self, paths, lang):
            self.lang = lang

        def run(self):
            called.append(self.lang)

    monkeypatch.setattr("codex_socks_manager.cli.interactive", lambda: True)
    monkeypatch.setattr("codex_socks_manager.cli.tui_available", lambda: True)
    monkeypatch.setattr("codex_socks_manager.cli.load_tui", lambda: FakeApp)
    assert run(args, manager_paths) == 0
    assert len(called) == 1


def test_list_folded_address_and_credentials(manager_paths, capsys, monkeypatch):
    monkeypatch.setenv("COLUMNS", "48")
    monkeypatch.setenv("NO_COLOR", "1")
    store = ProfileStore(manager_paths)
    host = "very-long-" * 7 + "proxy"
    store.add("office", f"socks5://alice:example-password@{host}.example:1080")
    store.set_active("office")
    run(["list", "--lang", "en"], manager_paths)
    output = capsys.readouterr().out
    assert "alice" not in output and "example-password" not in output
    assert "\x1b" not in output
    # Wrapping must preserve every character, including the end of a long URL.
    cells = [line.split("|")[-2].strip() for line in output.splitlines() if "|" in line]
    assert host + ".example:1080" in "".join(cells)
    assert "*" in output


def test_json_unchanged_in_chinese(manager_paths, monkeypatch, capsys):
    store = ProfileStore(manager_paths)
    store.add("office", "http://alice:example-password@proxy.example:8080")
    assert run(["--lang", "zh-CN", "list", "--json"], manager_paths) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"active": "off", "profiles": [
        {"name": "office", "scheme": "http", "url": "http://***:***@proxy.example:8080", "active": False}]}
    result = CheckResult(False, "configuration", "missing", "missing", "missing", "missing")
    monkeypatch.setattr("codex_socks_manager.operations.check", lambda paths: result)
    assert run(["check", "--lang", "zh-CN"], manager_paths) == 1
    assert json.loads(capsys.readouterr().out) == result.to_dict()


def test_exec_path_does_not_import_ui():
    import subprocess
    result = subprocess.run([sys.executable, "-c",
                             "import sys; import codex_socks_manager.exec_codex; import codex_socks_manager.cli; "
                             "assert 'textual' not in sys.modules; assert 'rich' not in sys.modules"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_localized_error_does_not_expose_url(monkeypatch, capsys):
    from codex_socks_manager import cli
    monkeypatch.setattr(sys, "argv", ["codex-socks", "--lang", "zh-CN", "check"])
    def fail(*args, **kwargs):
        raise RuntimeError("failed http://alice:example-password@proxy.example:8080")
    monkeypatch.setattr(cli, "run", fail)
    with pytest.raises(SystemExit) as result:
        cli.main()
    output = capsys.readouterr().err
    assert result.value.code == 2 and output.startswith("错误")
    assert "example-password" not in output and "alice" not in output


@pytest.mark.parametrize("lang", ["en", "zh-CN"])
def test_missing_ui_is_safe(manager_paths, monkeypatch, capsys, lang):
    monkeypatch.setattr("codex_socks_manager.cli.interactive", lambda: True)
    monkeypatch.setattr("codex_socks_manager.cli.tui_available", lambda: False)
    assert run(["--lang", lang], manager_paths) == 0
    assert run(["tui", "--lang", lang], manager_paths) == 2
    output = capsys.readouterr()
    assert "--with-tui" in output.err and "codex-socks-manager[tui]" in output.err
    assert "Traceback" not in output.err
    assert not manager_paths.config.exists()


def test_broken_ui_is_not_missing(manager_paths, monkeypatch, capsys):
    monkeypatch.setattr("codex_socks_manager.cli.interactive", lambda: True)
    monkeypatch.setattr("codex_socks_manager.cli.tui_available", lambda: True)
    def broken():
        raise ImportError("internal widget import failed")
    monkeypatch.setattr("codex_socks_manager.cli.load_tui", broken)
    assert run(["tui"], manager_paths) == 2
    assert "damaged" in capsys.readouterr().err
    assert not manager_paths.config.exists()


def test_no_color_is_not_noninteractive(monkeypatch):
    from codex_socks_manager.cli import interactive
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("TERM", "xterm")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert interactive()
    monkeypatch.setenv("TERM", "dumb")
    assert not interactive()


def test_unicode_table_width_and_content():
    from codex_socks_manager.presentation import display_width, fold, plain_table
    assert display_width("中文e\u0301") == 5
    assert "".join(fold("中文e\u0301", 2)) == "中文e\u0301"
    output = plain_table(("名称", "代理地址"), [("中文e\u0301", "http://proxy.example:8080"), ("a\tb", "x")], 32)
    assert len({display_width(line) for line in output.splitlines()}) == 1
    assert max(map(display_width, output.splitlines())) <= 32
    assert "\t" not in output

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from codex_socks_manager.clients import ClientPolicy, ClientPolicyStore
from codex_socks_manager.cli import run
from codex_socks_manager.profiles import ProfileStore
from codex_socks_manager.scope import build_client_env, discover_client, exec_client, scope_report
from codex_socks_manager.storage import Settings, atomic_write


def test_scope_direct_is_read_only_and_reports_transport_boundaries(manager_paths):
    report = scope_report(
        manager_paths, "claude", "direct", "https://api.deepseek.example/v1",
        base={"HTTPS_PROXY": "http://proxy.example:8080", "NO_PROXY": "api.deepseek.example"},
        cwd=manager_paths.config.parent,
    )
    assert report["route_prediction"]["status"] == "direct"
    assert report["connectivity"]["mcp_remote_http"] == "configured_not_verified"
    assert report["connectivity"]["mcp_stdio"].startswith("local_transport")
    assert "not_verified" in report["connectivity"]["official_connectors"]
    assert not manager_paths.config.exists()


def test_client_policies_are_isolated_and_secure(manager_paths):
    profiles = ProfileStore(manager_paths)
    profiles.add("office", "http://proxy.example:8080")
    store = ClientPolicyStore(manager_paths)
    store.set("claude", "profile", "office")
    store.add_bypass("claude", "api.deepseek.example")
    assert store.get("claude").bypass == ["api.deepseek.example"]
    assert store.get("codex").bypass == []
    assert manager_paths.clients.stat().st_mode & 0o777 == 0o600
    payload = json.loads(manager_paths.clients.read_text())
    assert payload["clients"]["claude"]["mode"] == "profile"


def test_claude_http_environment_and_socks_rejection(manager_paths):
    store = ProfileStore(manager_paths)
    store.add("office", "http://proxy.example:8080")
    env = build_client_env(
        manager_paths, "claude",
        base={"ALL_PROXY": "socks5://old.example:1080", "NO_PROXY": "metadata.example"},
        policy=ClientPolicy("profile", "office", ["api.deepseek.example"]),
    )
    assert env["HTTP_PROXY"] == env["https_proxy"] == "http://proxy.example:8080"
    assert "ALL_PROXY" not in env and "all_proxy" not in env
    assert "metadata.example" in env["NO_PROXY"] and "api.deepseek.example" in env["NO_PROXY"]
    store.add("socks", "socks5h://proxy.example:1080")
    with pytest.raises(ValueError, match="does not support SOCKS"):
        build_client_env(manager_paths, "claude", base={}, policy=ClientPolicy("profile", "socks"))


def test_codex_legacy_selection_remains_source_of_truth(manager_paths):
    profiles = ProfileStore(manager_paths)
    profiles.add("office", "http://proxy.example:8080")
    ClientPolicyStore(manager_paths).set("codex", "profile", "office")
    assert Settings.load(manager_paths.settings).active == "office"
    env = build_client_env(manager_paths, "codex", base={})
    assert env["ALL_PROXY"] == "http://proxy.example:8080"


def test_cli_scope_policy_and_bypass(manager_paths, capsys):
    assert run(["scope", "--client", "claude", "--json"], manager_paths) == 0
    assert json.loads(capsys.readouterr().out)["client"] == "claude"
    assert not manager_paths.config.exists()
    ProfileStore(manager_paths).add("office", "http://proxy.example:8080")
    assert run(["policy", "set", "--client", "claude", "--mode", "profile", "--profile", "office"], manager_paths) == 0
    assert run(["bypass", "add", "--client", "claude", "api.deepseek.example"], manager_paths) == 0
    capsys.readouterr()
    assert run(["bypass", "list", "--client", "claude"], manager_paths) == 0
    assert capsys.readouterr().out.strip() == "api.deepseek.example"


def test_discover_claude_uses_explicit_path(manager_paths, tmp_path):
    executable = tmp_path / "bin/claude"
    executable.parent.mkdir()
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o700)
    assert discover_client(manager_paths, "claude", {"PATH": str(executable.parent)}) == executable.resolve()
    with pytest.raises(FileNotFoundError):
        discover_client(manager_paths, "claude", {"PATH": ""})


def test_exec_claude_replaces_process_with_scoped_environment(manager_paths, tmp_path, monkeypatch):
    executable = tmp_path / "bin/claude"
    executable.parent.mkdir()
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o700)
    ProfileStore(manager_paths).add("office", "http://proxy.example:8080")
    captured = {}

    def fake_execve(path, argv, env):
        captured.update(path=path, argv=argv, env=env)

    monkeypatch.setenv("PATH", str(executable.parent))
    monkeypatch.setenv("ALL_PROXY", "socks5://old.example:1080")
    monkeypatch.setattr(os, "execve", fake_execve)
    exec_client(manager_paths, "claude", ["--version"], policy=ClientPolicy("profile", "office"))
    assert captured["path"] == executable.resolve()
    assert captured["argv"] == [str(executable.resolve()), "--version"]
    assert captured["env"]["HTTPS_PROXY"] == "http://proxy.example:8080"
    assert "ALL_PROXY" not in captured["env"]


def test_codex_persistent_inherit_policy_is_rejected(manager_paths):
    with pytest.raises(ValueError, match="must be profile or off"):
        ClientPolicyStore(manager_paths).set("codex", "inherit")


def test_claude_all_proxy_alone_is_not_claimed_for_model_or_remote_mcp(manager_paths):
    report = scope_report(manager_paths, "claude", "direct", "https://api.example.test", base={
        "ALL_PROXY": "socks5://proxy.example:1080"
    })
    assert report["route_prediction"]["status"] == "direct"
    assert report["connectivity"]["model_http"] == "direct_not_verified"
    assert report["connectivity"]["mcp_remote_http"] == "direct_not_verified"


def test_scope_never_serializes_proxy_values(manager_paths):
    report = scope_report(manager_paths, "claude", "direct", base={
        "HTTPS_PROXY": "http://alice:example-password@proxy.example:8080"
    }, policy=ClientPolicy("inherit", bypass=["private-service.example"]))
    serialized = json.dumps(report)
    assert "alice" not in serialized and "example-password" not in serialized and "proxy.example" not in serialized
    assert "private-service.example" not in serialized
    assert report["policy"]["bypass_count"] == 1


@pytest.mark.parametrize("rule", ["https://api.example", "host/path", "alice@host", "two hosts", "host.example:8443"])
def test_bypass_rejects_urls_credentials_paths_and_whitespace(manager_paths, rule):
    with pytest.raises(ValueError):
        ClientPolicyStore(manager_paths).add_bypass("claude", rule)

from __future__ import annotations

import os
import shutil
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .clients import ClientPolicy, ClientPolicyStore, validate_client
from .paths import Paths
from .profiles import ProfileStore
from .runtime import LOCAL_BYPASS, proxy_environment
from .storage import Settings

PROXY_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
BYPASS_KEYS = ("NO_PROXY", "no_proxy")


def _presence(value: str | None) -> str:
    return "unset" if value is None else "empty" if value == "" else "set"


def _merge_bypass(existing: str, rules: list[str]) -> str:
    values: list[str] = []
    for item in [*LOCAL_BYPASS, *existing.replace(" ", ",").split(","), *rules]:
        clean = item.strip()
        if clean and clean not in values:
            values.append(clean)
    return ",".join(values)


def _proxy_for(paths: Paths, policy: ClientPolicy) -> str | None:
    return ProfileStore(paths).get(policy.profile) if policy.mode == "profile" else None


def build_client_env(paths: Paths, client: str, *, base: dict[str, str] | None = None,
                     policy: ClientPolicy | None = None) -> dict[str, str]:
    validate_client(client)
    source = dict(os.environ if base is None else base)
    selected = policy or ClientPolicyStore(paths).get(client)
    if selected.mode == "inherit":
        return source
    proxy = _proxy_for(paths, selected)
    if client == "claude" and proxy and urllib.parse.urlsplit(proxy).scheme.lower().startswith("socks"):
        raise ValueError("Claude Code does not support SOCKS proxies; choose an HTTP or HTTPS profile")
    inherited_bypass = _merge_bypass(
        ",".join(value for value in (source.get("NO_PROXY", ""), source.get("no_proxy", "")) if value), [])
    source["NO_PROXY"] = source["no_proxy"] = inherited_bypass
    if client == "codex":
        env = proxy_environment(source, proxy)
    else:
        env = dict(source)
        for key in PROXY_KEYS:
            env.pop(key, None)
        if proxy:
            for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
                env[key] = proxy
        env["NO_PROXY"] = env["no_proxy"] = inherited_bypass
    merged = _merge_bypass(env.get("NO_PROXY", env.get("no_proxy", "")), selected.bypass)
    env["NO_PROXY"] = env["no_proxy"] = merged
    return env


def _masked_launch(value: str | None, profile: str) -> str:
    if value is None:
        return "unset"
    if value == "":
        return "empty"
    return f"profile:{profile}" if profile else "inherited"


def _matches_target(target: str, bypass: str) -> tuple[str, str]:
    parsed = urllib.parse.urlsplit(target)
    if parsed.scheme not in {"http", "https", "ws", "wss"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("target must be an HTTP, HTTPS, WS or WSS URL without credentials")
    host = parsed.hostname.lower().rstrip(".")
    rules = [item.strip().lower() for item in bypass.replace(" ", ",").split(",") if item.strip()]
    for rule in rules:
        clean = rule.lstrip(".").rstrip(".")
        if rule == "*" or host == clean or (rule.startswith(".") and host.endswith("." + clean)):
            return "bypass", rule
    return "proxy", ""


def _config_candidates(paths: Paths, client: str, cwd: Path) -> list[dict[str, str]]:
    home = paths.launcher.parents[2]
    if client == "codex":
        candidates = [home / ".codex/config.toml", cwd / ".codex/config.toml"]
    else:
        root = Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude"))
        candidates = [root / "settings.json", cwd / ".claude/settings.json", cwd / ".claude/settings.local.json"]
    return [{"path": str(path), "status": "present" if path.is_file() else "missing"} for path in candidates]


def scope_report(paths: Paths, client: str, entry: str = "managed", target: str | None = None,
                 base: dict[str, str] | None = None, cwd: Path | None = None,
                 policy: ClientPolicy | None = None) -> dict[str, Any]:
    validate_client(client)
    if entry not in {"direct", "managed"}:
        raise ValueError("entry must be direct or managed")
    inherited = dict(os.environ if base is None else base)
    selected = policy or ClientPolicyStore(paths).get(client)
    launch = inherited if entry == "direct" else build_client_env(paths, client, base=inherited, policy=selected)
    profile = selected.profile if entry == "managed" and selected.mode == "profile" else ""
    variables = []
    for key in (*PROXY_KEYS, *BYPASS_KEYS):
        variables.append({
            "name": key,
            "inherited": _presence(inherited.get(key)),
            "launch": _masked_launch(launch.get(key), profile) if key in PROXY_KEYS else _presence(launch.get(key)),
            "source": "parent" if entry == "direct" or selected.mode == "inherit" else "manager",
        })
    route: dict[str, str] = {"status": "not_requested", "matched_rule": ""}
    if target:
        status, matched = _matches_target(target, launch.get("NO_PROXY", launch.get("no_proxy", "")))
        effective_keys = PROXY_KEYS if client == "codex" else ("https_proxy", "HTTPS_PROXY", "http_proxy", "HTTP_PROXY")
        has_proxy = any(launch.get(key) for key in effective_keys)
        route = {"status": "direct" if status == "bypass" or not has_proxy else "proxy",
                 "matched_rule": matched}
    effective_keys = PROXY_KEYS if client == "codex" else ("https_proxy", "HTTPS_PROXY", "http_proxy", "HTTP_PROXY")
    proxy_present = any(launch.get(key) for key in effective_keys)
    transports = {
        "model_http": "configured_not_verified" if proxy_present else "direct_not_verified",
        "websocket": "configured_not_verified" if proxy_present else "direct_not_verified",
        "mcp_remote_http": "configured_not_verified" if proxy_present else "direct_not_verified",
        "mcp_remote_ws": "configured_not_verified" if proxy_present else "direct_not_verified",
        "mcp_stdio": "local_transport; child_network_may_inherit",
        "official_connectors": "client_or_cloud_managed; not_verified",
    }
    return {
        "schema_version": 1,
        "client": client,
        "entry": entry,
        "cwd": str((cwd or Path.cwd()).resolve()),
        "observation_scope": "current process snapshot; no network request",
        "policy": {"mode": selected.mode, "profile": selected.profile,
                   "bypass_count": len(selected.bypass)},
        "variables": variables,
        "config_candidates": _config_candidates(paths, client, (cwd or Path.cwd()).resolve()),
        "route_prediction": route,
        "connectivity": transports,
    }


def discover_client(paths: Paths, client: str, env: dict[str, str] | None = None) -> Path:
    validate_client(client)
    if client == "codex":
        configured = Settings.load(paths.settings).real_codex
        if not configured:
            raise FileNotFoundError("Codex executable is not configured")
        executable = Path(configured)
    else:
        values = os.environ if env is None else env
        found = shutil.which("claude", path=values.get("PATH"))
        if not found:
            raise FileNotFoundError("unable to find Claude Code executable")
        executable = Path(found)
    if not executable.exists() or not os.access(executable, os.X_OK):
        raise FileNotFoundError(f"client executable is not usable: {executable}")
    return executable.resolve()


def exec_client(paths: Paths, client: str, argv: list[str], *, policy: ClientPolicy | None = None) -> None:
    env = build_client_env(paths, client, policy=policy)
    executable = discover_client(paths, client, env)
    os.execve(executable, [str(executable), *argv], env)

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from .paths import Paths
from .runtime import run_codex
from .storage import Settings


@dataclass
class CheckResult:
    ok: bool
    category: str
    https: str
    wss: str
    app_server: str
    proxy_env: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _find_checks(value: Any, result: dict[str, Any]) -> None:
    if isinstance(value, dict):
        name = str(value.get("name", value.get("id", "")))
        if name:
            result[name] = value
        for child in value.values():
            _find_checks(child, result)
    elif isinstance(value, list):
        for child in value:
            _find_checks(child, result)


def _status(checks: dict[str, Any], fragment: str) -> str:
    for name, item in checks.items():
        if fragment in name:
            value = item.get("status", item.get("result", "unknown"))
            details = json.dumps(item, sort_keys=True).lower()
            if fragment == "websocket_reachability" and ("101" in details or value in {"ok", "pass", True}):
                return "101"
            return "ok" if value in {"ok", "pass", "passed", True} else str(value)
    return "missing"


def evaluate_doctor(payload: dict[str, Any]) -> CheckResult:
    checks: dict[str, Any] = {}
    _find_checks(payload, checks)
    https = _status(checks, "provider_reachability")
    wss = _status(checks, "websocket_reachability")
    app = _status(checks, "app_server.status")
    env = _status(checks, "network.env")
    blob = json.dumps(payload, sort_keys=True).lower()
    category = "ok"
    detail = ""
    if "403" in blob:
        auth_words = ("account", "workspace", "plugin", "authorization", "permission", "acl")
        category = "authorization" if any(word in blob for word in auth_words) else "proxy_transport"
        detail = "403 is authorization/ACL related" if category == "authorization" else "403 occurred on the proxy transport path"
    ok = https == "ok" and wss == "101" and app == "ok" and env == "ok" and category == "ok"
    return CheckResult(ok, category, https, wss, app, env, detail)


def check(paths: Paths) -> CheckResult:
    settings = Settings.load(paths.settings)
    if not paths.launcher.exists() or not settings.real_codex:
        return CheckResult(False, "configuration", "missing", "missing", "missing", "missing", "launcher or real Codex is missing")
    completed = run_codex(paths, ["doctor", "--json"], timeout=90)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return CheckResult(False, "doctor", "unknown", "unknown", "unknown", "unknown", "Codex Doctor did not return JSON")
    return evaluate_doctor(payload)


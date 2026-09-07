from __future__ import annotations

import shlex
import urllib.parse
from pathlib import Path

from .paths import Paths
from .profiles import ProfileStore


def parse_legacy_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key not in {"PROXY_USER", "PROXY_PASSWORD", "PROXY_HOST", "PROXY_PORT", "PROXY_URL"}:
            continue
        parsed = shlex.split(value, posix=True)
        values[key] = parsed[0] if len(parsed) == 1 else value.strip()
    return values


def legacy_url(values: dict[str, str]) -> str:
    if values.get("PROXY_URL"):
        return values["PROXY_URL"]
    host, port = values.get("PROXY_HOST"), values.get("PROXY_PORT")
    if not host or not port:
        raise ValueError("legacy profile lacks PROXY_HOST or PROXY_PORT")
    auth = ""
    if values.get("PROXY_USER") is not None:
        user = urllib.parse.quote(values.get("PROXY_USER", ""), safe="")
        password = urllib.parse.quote(values.get("PROXY_PASSWORD", ""), safe="")
        auth = f"{user}:{password}@"
    return f"http://{auth}{host}:{port}"


def migrate_legacy(paths: Paths, sources: dict[str, Path]) -> list[str]:
    store = ProfileStore(paths)
    migrated: list[str] = []
    for name, source in sources.items():
        if not source.exists():
            continue
        url = legacy_url(parse_legacy_env(source))
        try:
            existing = store.get(name)
        except FileNotFoundError:
            store.add(name, url)
            migrated.append(name)
        else:
            if existing != url:
                raise FileExistsError(f"profile {name} already exists with different content")
    return migrated


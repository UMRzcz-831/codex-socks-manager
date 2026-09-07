from __future__ import annotations

import re
import urllib.parse
from pathlib import Path

from .paths import Paths
from .storage import Settings, atomic_write, exclusive_lock, initialize

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ALLOWED_SCHEMES = {"socks5h", "socks5", "http", "https"}


def validate_name(name: str) -> str:
    if name == "off" or not NAME_RE.fullmatch(name):
        raise ValueError("name must be 1-64 safe characters and cannot be 'off'")
    return name


def validate_url(url: str) -> str:
    if any(ord(char) < 32 or ord(char) == 127 for char in url):
        raise ValueError("proxy URL contains control characters")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError("proxy URL scheme must be socks5h, socks5, http or https")
    if not parsed.hostname:
        raise ValueError("proxy URL must include a host")
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError("proxy URL has an invalid port") from error
    if port is None:
        raise ValueError("proxy URL must include an explicit port")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("proxy URL cannot include path, query or fragment")
    return url


def mask_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    auth = ""
    if parsed.username is not None:
        auth = "***"
        if parsed.password is not None:
            auth += ":***"
        auth += "@"
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{auth}{host}{port}"


class ProfileStore:
    def __init__(self, paths: Paths):
        self.paths = paths
        initialize(paths)

    def path(self, name: str) -> Path:
        return self.paths.profiles / f"{validate_name(name)}.conf"

    def add(self, name: str, url: str, replace: bool = False) -> None:
        validate_url(url)
        target = self.path(name)
        with exclusive_lock(self.paths.lock):
            if target.exists() and not replace:
                raise FileExistsError(f"profile already exists: {name}")
            atomic_write(target, url + "\n")

    def get(self, name: str) -> str:
        target = self.path(name)
        if not target.exists():
            raise FileNotFoundError(f"profile not found: {name}")
        return validate_url(target.read_text(encoding="utf-8").strip())

    def list(self) -> list[dict[str, object]]:
        active = Settings.load(self.paths.settings).active
        result = []
        for path in sorted(self.paths.profiles.glob("*.conf")):
            name = path.stem
            try:
                url = self.get(name)
                result.append({
                    "name": name,
                    "scheme": urllib.parse.urlsplit(url).scheme,
                    "url": mask_url(url),
                    "active": name == active,
                })
            except ValueError:
                result.append({"name": name, "scheme": "invalid", "url": "<invalid>", "active": name == active})
        return result

    def set_active(self, name: str) -> str:
        if name != "off":
            self.get(name)
        with exclusive_lock(self.paths.lock):
            settings = Settings.load(self.paths.settings)
            previous = settings.active
            settings.active = name
            atomic_write(self.paths.settings, settings.dump())
        return previous

    def delete(self, name: str, force: bool = False) -> bool:
        target = self.path(name)
        with exclusive_lock(self.paths.lock):
            settings = Settings.load(self.paths.settings)
            switched_off = False
            if settings.active == name:
                if not force:
                    raise PermissionError("active profile cannot be deleted without --force")
                settings.active = "off"
                atomic_write(self.paths.settings, settings.dump())
                switched_off = True
            if not target.exists():
                raise FileNotFoundError(f"profile not found: {name}")
            target.unlink()
            return switched_off


from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .paths import Paths


def secure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)


def atomic_write(path: Path, data: str, mode: int = 0o600) -> None:
    secure_dir(path.parent)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        path.chmod(mode)
        dir_fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if tmp.exists():
            tmp.unlink()


@contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    secure_dir(path.parent)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


@dataclass
class Settings:
    schema_version: int = 1
    active: str = "off"
    real_codex: str = ""
    install_source: str = ""
    manager_python: str = ""

    @classmethod
    def load(cls, path: Path) -> "Settings":
        if not path.exists():
            return cls()
        values: dict[str, object] = {}
        for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ValueError(f"invalid settings line {number}")
            key, value = (part.strip() for part in line.split("=", 1))
            if key == "schema_version":
                values[key] = int(value)
            elif key in {"active", "real_codex", "install_source", "manager_python"}:
                parsed = json.loads(value)
                if not isinstance(parsed, str):
                    raise ValueError(f"invalid string at line {number}")
                values[key] = parsed
            else:
                raise ValueError(f"unknown settings key {key}")
        return cls(**values)

    def dump(self) -> str:
        return "\n".join(
            [
                f"schema_version = {self.schema_version}",
                f"active = {json.dumps(self.active)}",
                f"real_codex = {json.dumps(self.real_codex)}",
                f"install_source = {json.dumps(self.install_source)}",
                f"manager_python = {json.dumps(self.manager_python)}",
                "",
            ]
        )


def initialize(paths: Paths) -> None:
    for directory in (paths.config, paths.state, paths.profiles, paths.backups, paths.launcher.parent):
        secure_dir(directory)
    if not paths.settings.exists():
        atomic_write(paths.settings, Settings().dump())


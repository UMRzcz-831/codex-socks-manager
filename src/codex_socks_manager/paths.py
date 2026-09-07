from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    config: Path
    state: Path
    profiles: Path
    backups: Path
    launcher: Path
    lock: Path
    settings: Path

    @classmethod
    def discover(cls, env: dict[str, str] | None = None) -> "Paths":
        values = os.environ if env is None else env
        home = Path(values.get("HOME", str(Path.home()))).expanduser()
        config = Path(values.get("XDG_CONFIG_HOME", home / ".config")) / "codex-socks-manager"
        state = Path(values.get("XDG_STATE_HOME", home / ".local/state")) / "codex-socks-manager"
        data_home = Path(values.get("XDG_DATA_HOME", home / ".local/share"))
        return cls(
            config=config,
            state=state,
            profiles=config / "profiles",
            backups=state / "backups",
            launcher=home / ".local/bin/codex",
            lock=state / "manager.lock",
            settings=config / "config.toml",
        )


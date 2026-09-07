from __future__ import annotations

import os
from pathlib import Path

import pytest

from codex_socks_manager.paths import Paths


@pytest.fixture
def manager_paths(tmp_path: Path) -> Paths:
    home = tmp_path / "home"
    return Paths.discover(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "XDG_STATE_HOME": str(tmp_path / "state"),
            "XDG_DATA_HOME": str(tmp_path / "data"),
            "PATH": os.environ.get("PATH", ""),
        }
    )


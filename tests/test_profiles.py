from __future__ import annotations

import json
import os
import stat
from concurrent.futures import ThreadPoolExecutor

import pytest

from codex_socks_manager.cli import run
from codex_socks_manager.profiles import ProfileStore, mask_url, validate_name, validate_url
from codex_socks_manager.storage import Settings, atomic_write


@pytest.mark.parametrize("url", [
    "socks5h://127.0.0.1:1080",
    "socks5://user:pass@proxy.example:1080",
    "http://proxy.example:8080",
    "https://proxy.example:8443",
])
def test_validate_url_accepts_supported_urls(url):
    assert validate_url(url) == url


@pytest.mark.parametrize("url", [
    "ftp://proxy.example:21",
    "http://proxy.example",
    "http:///missing:80",
    "http://proxy.example:99999",
    "http://proxy.example:80/path",
    "http://proxy.example:80\nattack",
])
def test_validate_url_rejects_unsafe_values(url):
    with pytest.raises(ValueError):
        validate_url(url)


def test_names_and_masking():
    assert validate_name("jp-1") == "jp-1"
    with pytest.raises(ValueError):
        validate_name("../jp")
    with pytest.raises(ValueError):
        validate_name("off")
    assert mask_url("socks5h://alice:example-pass@proxy.test:1080") == "socks5h://***:***@proxy.test:1080"


def test_storage_permissions_and_atomic_replace(manager_paths):
    store = ProfileStore(manager_paths)
    store.add("jp", "http://alice:example-pass@proxy.test:8080")
    assert stat.S_IMODE(manager_paths.config.stat().st_mode) == 0o700
    assert stat.S_IMODE(manager_paths.profiles.stat().st_mode) == 0o700
    assert stat.S_IMODE(store.path("jp").stat().st_mode) == 0o600
    inode = store.path("jp").stat().st_ino
    atomic_write(store.path("jp"), "http://proxy.test:8081\n")
    assert store.path("jp").stat().st_ino != inode


def test_cli_list_json_never_prints_credentials(manager_paths, capsys):
    secret = "not-a-real-secret"
    run(["add", "jp", f"http://alice:{secret}@proxy.test:8080"], manager_paths)
    capsys.readouterr()
    assert run(["list", "--json"], manager_paths) == 0
    output = capsys.readouterr().out
    assert secret not in output
    payload = json.loads(output)
    assert payload["profiles"][0]["url"] == "http://***:***@proxy.test:8080"


def test_active_delete_requires_force(manager_paths):
    store = ProfileStore(manager_paths)
    store.add("jp", "http://proxy.test:8080")
    store.set_active("jp")
    with pytest.raises(PermissionError):
        store.delete("jp")
    assert store.get("jp")
    assert store.delete("jp", force=True)
    assert Settings.load(manager_paths.settings).active == "off"


def test_edit_failure_preserves_profile(manager_paths, monkeypatch):
    store = ProfileStore(manager_paths)
    store.add("jp", "http://proxy.test:8080")
    monkeypatch.setenv("EDITOR", "/bin/false")
    with pytest.raises(RuntimeError):
        run(["edit", "jp"], manager_paths)
    assert store.get("jp") == "http://proxy.test:8080"


def test_concurrent_profile_writes_are_complete(manager_paths):
    store = ProfileStore(manager_paths)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda number: store.add(f"p{number}", f"http://proxy.test:{8000 + number}"), range(24)))
    assert len(store.list()) == 24
    assert all(item["scheme"] == "http" for item in store.list())

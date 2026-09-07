#!/usr/bin/env python3
"""Fail closed when a real-looking proxy credential enters worktree or Git history."""

from __future__ import annotations

import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".venv", "venv", "build", "dist", "__pycache__", ".pytest_cache"}
URL_PATTERN = re.compile(rb"(?:socks5h?|https?)://[^\s\"'<>]+", re.IGNORECASE)
PASSWORD_PATTERN = re.compile(rb"(?:PROXY_PASSWORD|proxy_password)\s*=\s*[^\s#]{8,}", re.IGNORECASE)
SAFE_HOST_SUFFIXES = (".test", ".example", ".invalid", "localhost")


def suspicious(data: bytes) -> bool:
    if PASSWORD_PATTERN.search(data):
        return True
    for match in URL_PATTERN.finditer(data):
        raw = match.group().decode("utf-8", "ignore").rstrip(".,);]")
        parsed = urllib.parse.urlsplit(raw)
        if parsed.password is not None and not (parsed.hostname or "").endswith(SAFE_HOST_SUFFIXES):
            return True
    return False


def worktree_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not any(part in SKIP_PARTS or part.endswith(".egg-info") for part in path.relative_to(ROOT).parts)
    ]


def scan_history() -> list[str]:
    check = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT, capture_output=True)
    if check.returncode:
        return []
    objects = subprocess.run(
        ["git", "rev-list", "--objects", "--all"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.splitlines()
    failures = []
    for line in objects:
        object_id, _, name = line.partition(" ")
        if not name:
            continue
        blob = subprocess.run(["git", "cat-file", "-p", object_id], cwd=ROOT, capture_output=True, check=False)
        if blob.returncode == 0 and suspicious(blob.stdout):
            failures.append(f"git object {object_id[:12]} ({name})")
    return failures


def main() -> int:
    failures = []
    for path in worktree_files():
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if suspicious(data):
            failures.append(str(path.relative_to(ROOT)))
    failures.extend(scan_history())
    if failures:
        print("Refusing to continue: possible proxy credential found in:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print("secret scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

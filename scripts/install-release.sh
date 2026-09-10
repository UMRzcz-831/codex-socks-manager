#!/bin/sh
set -eu

repository=UMRzcz-831/codex-socks-manager
python_bin=${PYTHON:-/usr/bin/python3}
version=latest
with_tui=false

usage() {
    cat <<'EOF'
Usage: install-release.sh [--with-tui] [--version VERSION]

Install the latest GitHub Release (default), or a pinned release.
默认安装 GitHub latest；可用 --version 固定版本，--with-tui 安装界面。

Options:
  --with-tui          Install Textual and Rich.
  --version VERSION   Release such as v0.3.0 or 0.3.0.
  -h, --help          Show this help.
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --with-tui)
            with_tui=true
            shift
            ;;
        --version)
            if [ "$#" -lt 2 ]; then
                echo "Missing value for --version." >&2
                exit 2
            fi
            version=$2
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [ ! -x "$python_bin" ]; then
    echo "Python 3 executable not found: $python_bin" >&2
    exit 1
fi
if ! "$python_bin" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
    echo "Python 3.10 or later is required." >&2
    exit 1
fi

case "$version" in
    latest)
        release_path=latest/download
        ;;
    [0-9]*)
        version=v$version
        release_path=download/$version
        ;;
    v[0-9]*)
        release_path=download/$version
        ;;
    *)
        echo "Invalid release version: $version" >&2
        exit 2
        ;;
esac
case "$version" in
    *[!0-9A-Za-z._-]*)
        echo "Invalid release version: $version" >&2
        exit 2
        ;;
esac

if [ -n "${CODEX_SOCKS_RELEASE_BASE_URL:-}" ]; then
    release_base=${CODEX_SOCKS_RELEASE_BASE_URL%/}
else
    release_base=https://github.com/$repository/releases/$release_path
fi

release_tmp=$(mktemp -d "${TMPDIR:-/tmp}/codex-socks-release.XXXXXX")
cleanup() {
    rm -rf "$release_tmp"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

download() {
    "$python_bin" - "$1" "$2" <<'PY'
import pathlib
import shutil
import sys
import urllib.request

source, destination = sys.argv[1:]
request = urllib.request.Request(source, headers={"User-Agent": "codex-socks-manager-installer"})
with urllib.request.urlopen(request, timeout=60) as response:
    with pathlib.Path(destination).open("wb") as output:
        shutil.copyfileobj(response, output)
PY
}

checksums=$release_tmp/SHA256SUMS
if ! download "$release_base/SHA256SUMS" "$checksums"; then
    echo "Unable to download release checksums from $release_base." >&2
    exit 1
fi

wheel_info=$("$python_bin" - "$checksums" <<'PY'
import pathlib
import re
import sys

entries = []
for line in pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    parts = line.split(maxsplit=1)
    if len(parts) != 2:
        continue
    digest, name = parts
    name = name.lstrip("*")
    if pathlib.PurePosixPath(name).name != name:
        continue
    if re.fullmatch(r"codex_socks_manager-[0-9][0-9A-Za-z._]*-py3-none-any\.whl", name):
        if re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            entries.append((digest.lower(), name))
if len(entries) != 1:
    raise SystemExit("SHA256SUMS must contain exactly one universal codex-socks-manager wheel")
print(*entries[0])
PY
) || {
    echo "Release checksum manifest is invalid." >&2
    exit 1
}

expected=${wheel_info%% *}
wheel_name=${wheel_info#* }
if [ "$version" != latest ]; then
    expected_name=codex_socks_manager-${version#v}-py3-none-any.whl
    if [ "$wheel_name" != "$expected_name" ]; then
        echo "Release wheel does not match requested version $version." >&2
        exit 1
    fi
fi

wheel=$release_tmp/$wheel_name
if ! download "$release_base/$wheel_name" "$wheel"; then
    echo "Unable to download $wheel_name." >&2
    exit 1
fi
"$python_bin" - "$wheel" "$expected" <<'PY'
import hashlib
import hmac
import pathlib
import sys

wheel, expected = pathlib.Path(sys.argv[1]), sys.argv[2]
actual = hashlib.sha256(wheel.read_bytes()).hexdigest()
if not hmac.compare_digest(actual, expected):
    raise SystemExit(f"SHA-256 mismatch for {wheel.name}")
PY

echo "Verified $wheel_name from $release_base."
if [ "$with_tui" = true ]; then
    PYTHONPATH="$wheel" "$python_bin" -m codex_socks_manager.bootstrap "$wheel" --with-tui
else
    PYTHONPATH="$wheel" "$python_bin" -m codex_socks_manager.bootstrap "$wheel"
fi

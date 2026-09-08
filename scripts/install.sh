#!/bin/sh
set -eu

project_dir=$(unset CDPATH; cd -- "$(dirname -- "$0")/.." && pwd)
python_bin=${PYTHON:-/usr/bin/python3}

if [ ! -x "$python_bin" ]; then
  echo "Python 3 executable not found: $python_bin" >&2
  exit 1
fi

PYTHONPATH="$project_dir/src" exec "$python_bin" -m codex_socks_manager.bootstrap "$project_dir" "$@"

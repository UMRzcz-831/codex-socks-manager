#!/bin/sh
set -eu

project_dir=$(unset CDPATH; cd -- "$(dirname -- "$0")/.." && pwd)
python_bin=${PYTHON:-/usr/bin/python3}
home_dir=${HOME:?HOME is required}
data_home=${XDG_DATA_HOME:-"$home_dir/.local/share"}
state_home=${XDG_STATE_HOME:-"$home_dir/.local/state"}
install_root="$data_home/codex-socks-manager"
state_root="$state_home/codex-socks-manager"
bin_dir="$home_dir/.local/bin"

if [ ! -x "$python_bin" ]; then
  echo "Python 3 executable not found: $python_bin" >&2
  exit 1
fi

install -d -m 700 "$install_root/lib" "$state_root/bootstrap-backups" "$bin_dir"
cp -R "$project_dir/src/codex_socks_manager" "$install_root/lib/"
find "$install_root/lib/codex_socks_manager" -type d -exec chmod 700 {} \;
find "$install_root/lib/codex_socks_manager" -type f -exec chmod 600 {} \;

manager="$bin_dir/codex-socks"
temporary="$manager.tmp.$$"
umask 077
{
  echo '#!/bin/sh'
  # shellcheck disable=SC2016
  printf 'PYTHONPATH=%s${PYTHONPATH:+:":$PYTHONPATH"}\n' "'$install_root/lib'"
  echo 'export PYTHONPATH'
  printf 'exec %s -m codex_socks_manager.cli "$@"\n' "'$python_bin'"
} >"$temporary"
chmod 700 "$temporary"
mv -f "$temporary" "$manager"

guard="$bin_dir/codex-proxy-guard"
temporary="$guard.tmp.$$"
{
  echo '#!/bin/sh'
  printf 'exec %s "$@"\n' "'$manager'"
} >"$temporary"
chmod 700 "$temporary"
mv -f "$temporary" "$guard"

exec "$manager" install

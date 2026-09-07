# Codex SOCKS Manager

Linux-only, zero-runtime-dependency proxy profile manager for Codex CLI. It keeps
proxy credentials in local `0600` files, installs a stable managed launcher, and
restores the proxy layer after a Codex update without copying or downgrading the
Codex binary.

## Install

Python 3.10 or newer is required. The dependency-free installer copies the
package into the XDG data directory and creates user-local entry points:

```bash
scripts/install.sh
```

Packaging through `pip install .` is also supported.

Make sure `~/.local/bin` is before other Codex locations in `PATH`.

## Profiles

```bash
# Preferred: hidden input avoids shell history.
codex-socks add jp

# Explicit URLs support socks5h, socks5, http, and https. Prefer hidden input
# whenever a URL contains credentials.
codex-socks add local socks5h://127.0.0.1:1080
codex-socks list
codex-socks list --json
codex-socks edit local
codex-socks use local
codex-socks off
codex-socks del local
codex-socks del local --force
```

`use` and `off` atomically switch the active profile, restart only matching
current-user Codex app-server roles, then validate HTTPS, WSS (HTTP 101), proxy
environment inheritance, and app-server status. A failed validation rolls the
active profile back.

Profiles live under `${XDG_CONFIG_HOME:-~/.config}/codex-socks-manager/profiles`
and state under `${XDG_STATE_HOME:-~/.local/state}/codex-socks-manager`.
Directories are `0700`; credentials and state files are `0600`. Usernames and
passwords are always masked by list and diagnostic output.

## Updates and recovery

```bash
codex-socks check
codex-socks backup
codex-socks safe-update
codex-socks restore
```

`safe-update` creates a known-good snapshot, runs the official `codex update`,
reinstalls the launcher, restores proxy state, restarts app-server roles, and
runs Doctor. If update or validation fails, it restores only the proxy layer and
previous active profile. It intentionally does not roll back a Codex binary.

The `codex-proxy-guard` console entry remains available and accepts the same
`backup`, `check`, `restore`, and `safe-update` commands.

## Migrate older JP/US files

```bash
codex-socks backup
codex-socks migrate-legacy \
  --jp ~/.config/openai-proxy/jp.env \
  --us ~/.config/openai-proxy/us.env
```

Legacy component variables are parsed without sourcing shell code. Values are
never printed. Migration is idempotent and refuses to overwrite a profile whose
content differs.

## What a 403 means

`check` only promises to diagnose 403 responses caused on the proxy transport
path. Account, workspace, connector/plugin authorization, and remote ACL errors
are classified as authorization failures; changing a proxy cannot fix those.

Codex apps/connectors do not expose one universal business-level smoke test.
After `check` succeeds, run a connector-specific read-only operation in Codex and
confirm that it returns expected data without a 403. Do not use a write operation
as a transport test.

## Development

```bash
python3 -m pip install -e '.[test]'
pytest
python3 -m compileall -q src tests
openspec validate create-codex-socks-manager --strict
scripts/check-secrets.py
shellcheck .githooks/pre-commit
```

No proxy URL, credential, snapshot, Doctor output, or runtime log belongs in Git.
Enable the bundled fail-closed pre-commit scan with
`git config core.hooksPath .githooks` before the first commit.

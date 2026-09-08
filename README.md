# Codex SOCKS Manager

![Bold three-dimensional comic lettering reading no more codex 403 bursts through terminal panels showing codex-socks commands](docs/assets/readme-hero.png)

> no more codex 403

[English](README.md) · [简体中文](README.zh-CN.md)

Codex SOCKS Manager keeps proxy profiles, app-server restarts, diagnostics, and update recovery in one Linux tool. Use the dependency-free CLI in scripts or install the optional Textual interface for day-to-day management.

It fixes proxy transport problems. It cannot grant account access, enable an unsupported region, change workspace permissions, or bypass a remote ACL. The slogan is a goal, not a promise that every 403 is fixable.

![Codex SOCKS Manager TUI showing the profile table and selected-profile details](docs/designs/tui-graphite/rendered/profiles-en-120x36.png)

## At a glance

| Area | What the manager does |
| --- | --- |
| Profiles | Stores named `socks5h://`, `socks5://`, `http://`, and `https://` endpoints. |
| Apply and rollback | Exports upper- and lowercase proxy variables, restarts matching current-user app-server roles, validates with Doctor, and restores the previous selection when validation fails. |
| Diagnostics | Summarizes HTTPS, WebSocket, app-server, and proxy-environment checks without treating them as proof of account authorization. |
| Maintenance | Installs or repairs the managed launcher, creates snapshots, restores the proxy layer, migrates old profiles, and protects `codex update` with recovery. |
| Interfaces | Provides 13 bilingual CLI commands plus an optional four-page Textual TUI. Machine-readable JSON stays unchanged. |

An ordinary `export ALL_PROXY=...` is fine for one shell. This project is for setups that also need named endpoints, app-server lifecycle handling, validation, and a recovery path after Codex updates.

## Install

Requirements: Linux, Python 3.10+ with venv/pip support, and an existing Codex CLI installation. Profile switching and `check` require a Codex version with `doctor --json`; `safe-update` also requires `codex update`.

| Edition | Project installer | pip in a retained environment |
| --- | --- | --- |
| CLI, no third-party runtime dependencies | `./scripts/install.sh` | `python3 -m pip install .` |
| CLI + Textual TUI | `./scripts/install.sh --with-tui` | `python3 -m pip install '.[tui]'` |

The managed installer is the simplest route:

```bash
git clone https://github.com/UMRzcz-831/codex-socks-manager.git
cd codex-socks-manager
./scripts/install.sh --with-tui
export PATH="$HOME/.local/bin:$PATH"
```

For the lightweight edition, omit `--with-tui`. Each installer run builds a new versioned environment under `~/.local/share/codex-socks-manager/venvs/`, verifies it, then switches the entry points. A failed install leaves the old entry points intact. Existing profiles, private bootstrap backups, and previous environments are retained.

Keep `--with-tui` on later upgrades if you want the full edition. Running the installer without it switches to a new CLI-only environment. A normal pip reinstall does not remove extras already present, so use a fresh environment when you need a strictly lightweight pip installation.

The installer replaces `~/.local/bin/codex` with a managed launcher after finding the real standalone, npm, or pnpm Codex executable. Back up a custom launcher first. Use `PYTHON=/path/to/python3 ./scripts/install.sh` to select the interpreter. For a pip installation, run `codex-socks install` in the same environment after installing the package.

## First profile

Use the hidden prompt for a URL that contains credentials:

```bash
codex-socks add office
codex-socks list
codex-socks use office
codex-socks check
```

Passing a URL directly is convenient for a credential-free local proxy:

```bash
codex-socks add local socks5://127.0.0.1:1080
```

Command-line URLs may remain in shell history or process arguments. `list` masks usernames and passwords but still prints hosts and ports. Review its output before sharing it.

Applying a profile restarts matching app-server roles and can interrupt the current Codex session. The manager does not start an app-server that was not already running. `off` also validates; if direct connectivity fails, it restores the previous selection.

## Textual interface

Run `codex-socks` in an interactive terminal after installing the TUI edition, or use `codex-socks tui` explicitly.

| Page | Available work |
| --- | --- |
| Profiles | Add, edit, delete, apply, or turn off a profile. `>` marks the cursor; `*` marks the active selection. Editing saves without applying. |
| Diagnostics | Run Doctor on demand and inspect HTTPS, WSS, app-server, and proxy-environment results. Old results are marked stale after local changes. |
| Maintenance | Repair the launcher, create a backup, select or enter a restore snapshot, run a safe update, or migrate legacy files. |
| Commands | Filter the bilingual command table and read parameters, examples, and behavior notes. |

The graphite theme uses warm-white text, ice-blue focus, and orange or red only for warnings and errors. At 100 columns or wider, the main list and details use an approximately 65/35 split. Narrower terminals stack the panels; 80×24 is the supported compact size.

Use the mouse, Tab, arrows, Enter, Page Up, and Page Down. Shortcuts are `a` add, `e` edit, `r` refresh, `l` language, `q` quit, and `F2` full operation result. Letter shortcuts are inactive while typing. Actions that restart processes or replace data require confirmation. Duplicate submission and normal exit are blocked until an operation and any rollback finish.

[Browse screenshots for every page, both languages, and both terminal sizes](docs/designs/tui-graphite/rendered/README.md). They were rendered from the real Textual app with disposable fake profiles; no live diagnostic or proxy operation was used.

```bash
codex-socks tui --lang zh-CN
codex-socks --lang en list
CODEX_SOCKS_LANG=zh-CN codex-socks
```

`--lang` works before or after a subcommand. Selection order is the explicit option, `CODEX_SOCKS_LANG`, then `LC_ALL` / `LC_MESSAGES` / `LANG`. Chinese locales select simplified Chinese; everything else falls back to English. A language change inside the TUI lasts for that session.

Without Textual and Rich, a bare interactive invocation prints help and returns 0; explicit `tui` explains how to install it and returns 2. In a non-interactive terminal or with `TERM=dumb`, bare invocation also prints help while explicit `tui` returns 2. CLI tables never emit ANSI. `NO_COLOR` keeps the TUI usable because text and symbols also identify state.

## Command reference

| Command | Behavior | Example |
| --- | --- | --- |
| `add NAME [URL]` | Create a validated profile; omit URL for hidden input. | `codex-socks add office` |
| `use NAME` | Apply a profile, restart matching app-server roles, and validate. | `codex-socks use office` |
| `list [--json]` | Show the four-column profile table or stable JSON. | `codex-socks list --json` |
| `edit NAME` | Edit through `$EDITOR` using a `0600` temporary file; save without applying. | `EDITOR=vi codex-socks edit office` |
| `del NAME [--force]` | Delete a profile; an active profile requires a validated switch to off. | `codex-socks del office --force` |
| `off` | Clear managed proxy variables, restart matching roles, and validate direct access. | `codex-socks off` |
| `check` | Print the Doctor summary as JSON; return 1 when unhealthy. | `codex-socks check` |
| `install` | Find Codex and install or repair the managed launcher. | `codex-socks install` |
| `backup` | Create a local snapshot, including Codex configuration when present. | `codex-socks backup` |
| `restore [SNAPSHOT]` | Restore the proxy layer; default to the latest known-good snapshot. | `codex-socks restore /path/to/snapshot` |
| `safe-update` | Snapshot, run `codex update`, repair the launcher, restart, and validate. | `codex-socks safe-update` |
| `migrate-legacy [--jp PATH] [--us PATH]` | Import old JP/US environment files without sourcing shell. | `codex-socks migrate-legacy --jp /path/to/jp.env --us /path/to/us.env` |
| `tui` | Open the optional interactive manager. | `codex-socks tui` |

Run `codex-socks -h` for this table in the terminal and `codex-socks COMMAND -h` for detailed parameters, examples, and boundaries. `codex-proxy-guard` remains a compatible entry point for `backup`, `check`, `restore`, and `safe-update`.

## Diagnostics and 403 boundaries

`codex-socks check` returns `https`, `wss`, `app_server`, `proxy_env`, overall `ok`, and a `category`. The 403 classification uses keywords from Doctor output. Values such as `authorization` and `proxy_transport` are diagnostic hints, not verdicts. A healthy transport check does not audit every file permission, child-process environment, connector, account, or workspace.

For a `codex_apps` or MCP connector, follow Doctor with a read-only request that your account is authorized to make. Keep raw responses and diagnostics private if they contain identifiers or credentials.

OpenAI publishes an [API-supported countries and territories list](https://help.openai.com/en/articles/5347006-openai-api-supported-countries-and-territories), not a separate unsupported list. When checked on **2026-09-07**, Mainland China, Hong Kong, Macao, Iran, North Korea, Russia, Belarus, Cuba, and Venezuela were absent. This is a dated inference from the API list, not a complete official blacklist or a statement about every Codex/ChatGPT sign-in path. OpenAI warns that access from unsupported locations may lead to an account block or suspension. A proxy does not change service eligibility.

## Updates and recovery

```bash
codex-socks check
codex-socks backup
codex-socks safe-update

# Restore the latest known-good snapshot:
codex-socks restore
```

`safe-update` takes a proxy-layer snapshot, asks the configured real Codex executable to update, repairs the launcher, restarts app-server, and runs Doctor. On failure it attempts snapshot recovery and reports whether rollback succeeded. Recovery keeps the installed Codex binary version; it does not downgrade the binary.

`restore` first creates a pre-restore snapshot. It restores manager settings, profiles, and the saved launcher while retaining the current Codex binary path. Profiles absent from the selected snapshot leave active storage but remain in the pre-restore snapshot. `backup` saves `~/.codex/config.toml` when present; `restore` does not write that Codex configuration back automatically. A `known-good` label does not itself run a health check.

## Storage and migration

| Data | Default location |
| --- | --- |
| Settings and profiles | `~/.config/codex-socks-manager/` |
| Snapshots and state | `~/.local/state/codex-socks-manager/` |
| Versioned installer environments | `~/.local/share/codex-socks-manager/` |
| Commands and managed Codex launcher | `~/.local/bin/` |

`XDG_CONFIG_HOME`, `XDG_STATE_HOME`, and the installer's `XDG_DATA_HOME` override these roots. Sensitive directories use `0700`; settings and profile files use `0600`. Credentials remain plaintext on the local machine, including inside snapshots.

```bash
codex-socks backup
codex-socks migrate-legacy \
  --jp ~/.config/openai-proxy/jp.env \
  --us ~/.config/openai-proxy/us.env
```

With neither path, migration uses those two defaults. Re-importing identical data is safe; conflicting same-name profiles are rejected. Migration does not change the active selection.

Never publish real proxy URLs, host details, credentials, snapshots, Doctor output, or runtime logs in Git, Issues, CI output, or release assets. The repository's ignore rules and heuristic scanner help, but they do not replace review of the staged diff.

## Development

See [AGENTS.md](AGENTS.md) for project-specific guidance and [SECURITY.md](SECURITY.md) for vulnerability reports.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,tui]'
git config core.hooksPath .githooks

.venv/bin/python -m pytest
.venv/bin/python -m compileall -q src tests
python3 scripts/check-secrets.py
shellcheck .githooks/pre-commit scripts/install.sh
```

CI runs Python 3.10 and 3.12 in separate CLI-only and TUI jobs. The offline installer integration test also needs a local wheel directory through `CODEX_SOCKS_TEST_WHEELHOUSE`; without it, that one test is skipped.

Licensed under MIT. See [LICENSE](LICENSE).

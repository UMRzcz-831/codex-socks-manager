# Codex SOCKS Manager

> no more codex 403

[English](README.md) · [简体中文](README.zh-CN.md)

Keep Codex CLI proxy settings consistent across launches and recover them after updates. Manage SOCKS and HTTP profiles, inject proxy variables into Codex, and diagnose HTTPS and WebSocket connectivity from one Linux CLI. The slogan describes the goal: reduce proxy-related failures. Account access, service availability, and remote authorization still apply.

## What it does

- Manage named `socks5h://`, `socks5://`, `http://`, and `https://` profiles.
- Install a launcher for an existing standalone, npm, or pnpm Codex installation.
- Set uppercase and lowercase `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY`; retain local bypasses in `NO_PROXY`.
- Switch profiles, restart matching current-user app-server roles, and roll back the active selection if validation fails.
- Summarize Codex Doctor checks for HTTPS, WebSockets, app-server status, and proxy environment.
- Back up and restore the proxy layer; retain the `codex-proxy-guard` command.

## Quick start

Requires Linux, Python 3.10+, and an existing Codex CLI installation. Runtime Python dependencies are standard-library only. A Codex version providing `doctor --json` is needed for `check` and switch validation; `safe-update` requires `codex update`.

```bash
git clone https://github.com/UMRzcz-831/codex-socks-manager.git
cd codex-socks-manager
./scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"

# Enter the proxy URL at the hidden prompt.
codex-socks add office
codex-socks list

# Requires existing, matching Codex app-server processes.
codex-socks use office
codex-socks check
```

The installer writes user-local commands and replaces `~/.local/bin/codex`. Back up an existing custom launcher before installation. Add `~/.local/bin` early in your shell's `PATH`. To select another interpreter, run `PYTHON=/path/to/python3 ./scripts/install.sh`.

For a pip installation, install this package in your chosen Python environment with `python3 -m pip install .`, then run `codex-socks install` from that environment. Keep the environment available: the generated launcher uses its Python interpreter.

## Commands

| Command | Behavior |
| --- | --- |
| `add NAME [URL]` | Create a profile; omitting URL opens a hidden prompt. |
| `list [--json]` | Show profiles and active selection with username/password masked. |
| `use NAME` | Select a profile, restart matching app-server roles, and validate. |
| `use off` / `off` | Clear managed proxy variables, restart, and validate direct connectivity. |
| `edit NAME` | Edit via `$EDITOR` in a `0600` temporary file; validate before replacement. |
| `del NAME` | Delete an inactive profile. |
| `del NAME --force` | Switch an active profile to off and validate before deleting it. |
| `check` | Print a JSON summary of Codex Doctor results. |
| `install` | Discover Codex and install or repair the managed launcher. |
| `backup` | Create a local snapshot, including Codex configuration when present. |
| `restore [SNAPSHOT]` | Restore the proxy layer; defaults to the latest known-good snapshot. |
| `safe-update` | Back up, invoke `codex update`, repair the launcher, restart, and validate. |
| `migrate-legacy [--jp PATH] [--us PATH]` | Import old JP/US environment files without sourcing shell code. |

Use `EDITOR=vi codex-socks edit office` to select an editor for one invocation. Editing an active profile does not restart existing processes; run `codex-socks use office` afterward to apply and validate it.

Switches can interrupt an active Codex session. They restart discovered app-server roles; they do not bootstrap an absent app-server. `off` can fail and roll back when direct connectivity is unavailable.

For a credential-free local proxy, an explicit URL is convenient:

```bash
codex-socks add local socks5h://127.0.0.1:1080
```

Use the hidden prompt for real credentials. A positional URL can appear in shell history and process arguments. List output masks credentials but still shows the host and port; review it before sharing.

## Unsupported regions: API examples

OpenAI publishes a [supported countries and territories list for its API](https://help.openai.com/en/articles/5347006-openai-api-supported-countries-and-territories), rather than a separate unsupported list. As checked on **2026-09-07**, examples absent from that list include:

- Mainland China, Hong Kong, Macao, Iran, North Korea.
- Russia, Belarus.
- Cuba, Venezuela.

These are non-exhaustive examples inferred from the published list, not a complete official blacklist. Ukraine is listed with certain exceptions. Check the linked page for current details.

This source covers API availability, not every Codex or ChatGPT sign-in arrangement. OpenAI states that access outside supported locations may lead to an account block or suspension. Proxy configuration does not change service eligibility or grant account/workspace permissions.

## Diagnostics and connectors

```bash
codex-socks check
```

The JSON summary reports `https`, `wss`, `app_server`, and `proxy_env`, plus an overall `ok` and a `category`. The tool derives these from Doctor output; a green result is not a separate audit of every file permission, child-process environment, or connector operation.

The current 403 classification uses keywords in Doctor output. Treat `authorization` and `proxy_transport` as diagnostic hints, not proof of the root cause. Check account/workspace permissions and remote ACLs when transport configuration alone does not resolve access.

For `codex_apps`/MCP, finish with a connector-specific read-only smoke test:

1. Run `codex-socks check` and inspect the summary.
2. In Codex, ask an already connected app to read an item you are authorized to access, such as an issue title.
3. Confirm the expected result arrives without a transport or authorization error. Keep raw responses and diagnostics private if they contain sensitive information.

## Updates and recovery

```bash
codex-socks backup
codex-socks safe-update

# To recover from an existing known-good snapshot:
codex-socks restore
```

`safe-update` snapshots the proxy layer, invokes the configured real Codex executable's update command, reinstalls the launcher, restarts app-server roles, and runs Doctor. On failure it attempts to restore the snapshot. It does not copy or downgrade Codex binaries. Run `check` before updating to establish a healthy baseline, and inspect any recovery errors.

`restore` creates a pre-restore snapshot and restores manager settings, profiles, and the saved launcher while retaining the current binary path. Profiles absent from the selected snapshot are removed from active storage and remain recoverable from the pre-restore snapshot. Although `backup` also saves `~/.codex/config.toml` when present, `restore` does not automatically write that Codex configuration back.

The `codex-proxy-guard` entry point forwards the same `backup`, `check`, `restore`, and `safe-update` commands.

## Local storage and legacy migration

| Data | Default location |
| --- | --- |
| Manager settings and profiles | `~/.config/codex-socks-manager/` |
| Snapshots and state | `~/.local/state/codex-socks-manager/` |
| Package installed by the shell installer | `~/.local/share/codex-socks-manager/` |
| User commands and Codex launcher | `~/.local/bin/` |

`XDG_CONFIG_HOME`, `XDG_STATE_HOME`, and the shell installer's `XDG_DATA_HOME` override the corresponding roots. Sensitive directories use `0700`, and settings/profile files use `0600`. Credentials are stored as local plaintext; protect snapshots as carefully as the original profiles.

To import an older setup:

```bash
codex-socks backup
codex-socks migrate-legacy \
  --jp ~/.config/openai-proxy/jp.env \
  --us ~/.config/openai-proxy/us.env
```

Omitting both paths uses those legacy locations. Re-importing identical profiles is safe; different existing content is rejected. Migration does not change the active selection: choose the imported profile with `use` when ready to restart.

Real proxy URLs, host details, credentials, snapshots, Doctor output, and runtime logs must stay out of public Git, Issues, and CI logs. The repository provides ignore rules and a heuristic secret scanner; review the staged diff as well.

## Contributing

See [AGENTS.md](AGENTS.md) for task-specific guidance and [SECURITY.md](SECURITY.md) for reporting vulnerabilities. Keep English and Chinese usage instructions aligned. Use OpenSpec for requested structured changes; documentation-only changes can declare `skip_specs: true`.

Install development dependencies in an isolated environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
git config core.hooksPath .githooks
```

Choose checks appropriate to the change:

```bash
git diff --check
python3 scripts/check-secrets.py
openspec validate refresh-readmes-and-agent-guidance --strict
# For Python or shell changes:
.venv/bin/python -m pytest
.venv/bin/python -m compileall -q src tests
shellcheck .githooks/pre-commit scripts/install.sh
```

MIT licensed. See [LICENSE](LICENSE).

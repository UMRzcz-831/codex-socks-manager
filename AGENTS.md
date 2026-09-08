# Working on Codex SOCKS Manager

Applies to this repository and its descendants. Keep instructions task-specific; explicit user direction and existing authorization govern the work.

## Scope and completion

This is a Linux CLI with an optional Textual TUI, using Python 3.10+. The default CLI and Codex execution path use only the standard library. Textual and Rich are installed through the `tui` extra or installer `--with-tui`. It manages proxy profiles, the Codex launcher, and update recovery. Other repositories and VPS services are outside its scope unless the user includes them.

Inspect `git status --short --branch` and the relevant diff; preserve unrelated work. Read the files needed for the task. Continue through implementation, relevant verification, and fixes within the authorized scope. Ask only when a missing decision or new authority prevents correct completion; do not ask again for authorization already given.

When OpenSpec is requested, use the selected change's CLI instructions and track tasks. An implementation request includes progressing from artifacts into apply; a planning-only request stops at the artifacts. For documentation-only work, use `skip_specs: true` without inventing runtime requirements.

Done means the requested result is present, applicable checks pass, and remaining limitations are stated. Commit/push/deploy when included in the user's request or existing authorization. Report the changed behavior or documents and the actual verification; do not call an unrun check passed.

## Read according to the task

| Area | Starting points |
| --- | --- |
| Commands and usage | [cli.py](src/codex_socks_manager/cli.py), [README.md](README.md), [中文 README](README.zh-CN.md) |
| TUI, help, shared operations | [tui.py](src/codex_socks_manager/tui.py), [catalog.py](src/codex_socks_manager/catalog.py), [operations.py](src/codex_socks_manager/operations.py) |
| Profile validation and persistence | [profiles.py](src/codex_socks_manager/profiles.py), [storage.py](src/codex_socks_manager/storage.py), [paths.py](src/codex_socks_manager/paths.py) |
| Launcher, process lifecycle, diagnosis | [runtime.py](src/codex_socks_manager/runtime.py), [appserver.py](src/codex_socks_manager/appserver.py), [doctor.py](src/codex_socks_manager/doctor.py) |
| Install, recovery, migration | [install.sh](scripts/install.sh), [recovery.py](src/codex_socks_manager/recovery.py), [migration.py](src/codex_socks_manager/migration.py) |

The shell installer uses versioned private virtual environments. Check packaging of TUI resources and failure preservation when changing [bootstrap.py](src/codex_socks_manager/bootstrap.py). TUI tests use Textual Pilot with temporary XDG paths and fake operations; never load real profiles for screenshots.

Install `.[test,tui]` for full development tests. Also test `.[test]` in a separate environment without Textual/Rich, using `CODEX_SOCKS_TEST_EDITION=cli`; this explicitly excludes UI-only tests. Full CI uses `CODEX_SOCKS_TEST_EDITION=tui` and must not skip them. The installer defaults to CLI on every run; retaining TUI during upgrades requires `--with-tui`.

Use matching files under `tests/` for code changes. Select skills for the actual workflow or when explicitly requested; keep skill routing concise and read supporting material as needed.

## Credentials and operational boundaries

- Never publish the owner's two real VPS proxy links, credentials, endpoints, or derived identifying components. Keep real profiles, legacy environment files, snapshots, Doctor dumps, and logs outside the repository. This also applies to Issues, CI output, comments, and release assets. Masked credentials do not make a real endpoint public-safe.
- Use loopback addresses or reserved `.test`/`.example` domains for examples and fixtures. Prefer hidden input for real proxy URLs; do not put secrets in command arguments or print environment/configuration dumps. Documentation work does not need real credentials.
- Preserve atomic writes, locking, XDG paths, `0700` sensitive directories, and `0600` sensitive files. Launcher replacement must not follow a symlink and overwrite the real Codex binary. Recovery must retain the installed binary version.
- Tests use disposable fixtures and fakes. Keep environment and subprocess access isolated from actual Codex, app-server, credentials, and network services. Run relevant tests, fix failures caused by the change, and rerun affected checks without step-by-step approval.
- Installation, switching, restore, migration, and safe-update have local side effects; restarting app-server may interrupt the session. Apply these to a real environment only when that operation is in the authorized task. Before an authorized replacement, preserve existing configuration in a private backup outside Git. Documentation changes require no live restart or update.
- The slogan is not a guarantee that every 403 is fixable. Describe Doctor's classification as a diagnostic hint; distinguish proxy configuration from account, workspace, connector authorization, and regional service availability.

## Verification and documentation

For documentation changes, check links, command accuracy, bilingual consistency, and `git diff --check`. Validate any changed OpenSpec artifacts with `openspec validate <change-name> --strict`. No new tests or production smoke run are needed for prose alone.

For Python changes, use an isolated development environment described in README and run the affected tests with `.venv/bin/python -m pytest tests/<affected-test>.py`. For shell changes, run `shellcheck .githooks/pre-commit scripts/install.sh`. Expand to the full suite when the affected behavior crosses modules or a failure warrants it; do not repeat successful checks without a reason.

Before committing or publishing, inspect the staged diff and run `python3 scripts/check-secrets.py`. The scanner is heuristic, so a pass does not authorize uploading real configuration. Never weaken it to admit a real value. Use `codex/` for new branches and focused conventional commit messages.

Keep README.md and README.zh-CN.md aligned on commands, limitations, and sources. Regional examples need the official source, a checked date, and API-specific scope; revisit both translations when that information changes.

## Reference

Inspired by Eric Provencher's [Rethinking skills and prompts for GPT-6 Astra](https://x.com/pvncher/status/2095991462416490862), published 2026-09-04: keep context selective, instructions economical, and completion boundaries clear. The security and runtime constraints above are specific to this project. These guidelines are intended for contributors using different models.

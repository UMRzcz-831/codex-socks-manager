# Release checklist

GitHub Releases and PyPI are published by [release.yml](../.github/workflows/release.yml) when a `v*` tag is pushed. The workflow runs the full TUI test suite, checks package metadata, builds wheel and sdist files, creates checksums, uploads the standalone installer, publishes the GitHub Release, and then publishes the same Python distributions to PyPI.

## One-time PyPI setup

The workflow uses OIDC Trusted Publishing. It does not need a repository API token.

Before the first release, sign in to PyPI and add a pending trusted publisher with these values:

| Field | Value |
| --- | --- |
| PyPI project name | `codex-socks-manager` |
| GitHub owner | `UMRzcz-831` |
| Repository | `codex-socks-manager` |
| Workflow | `release.yml` |
| Environment | `pypi` |

The matching GitHub environment must also exist. It needs no secrets; environment protection rules are optional. PyPI creates the project during the first trusted publication.

## Publish a version

1. Update `project.version` in `pyproject.toml` and `__version__` in `src/codex_socks_manager/__init__.py`.
2. Run the relevant local tests and push the version commit.
3. Wait for the main CI matrix to pass.
4. Create an annotated tag with the same version, for example `v0.3.0`, and push it.
5. Check the Release workflow. Do not upload a different wheel to either registry.

The GitHub publishing job is safe to rerun because it replaces existing assets. PyPI rejects a filename or version that has already been published. After a first-publication setup failure, rerun the failed PyPI job; do not republish a version that already succeeded.

## Release contents

The GitHub Release contains:

- the universal Python wheel;
- the source distribution;
- `install.sh`, which installs the latest release by default;
- `SHA256SUMS` covering all three files.

The installer downloads only the wheel selected by the checksum manifest. It verifies SHA-256 before importing bootstrap code or creating a managed environment.

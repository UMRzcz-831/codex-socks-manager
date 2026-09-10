from importlib import metadata, util
import os
from pathlib import Path


def test_package_runtime_requirements_are_optional():
    requirements = metadata.requires("codex-socks-manager") or []
    assert all("extra ==" in requirement for requirement in requirements)
    assert any("textual" in item and '"tui"' in item for item in requirements)
    assert any("rich" in item and '"tui"' in item for item in requirements)


def test_explicit_test_edition_matches_environment():
    edition = os.environ.get("CODEX_SOCKS_TEST_EDITION")
    if edition == "cli":
        assert util.find_spec("textual") is None and util.find_spec("rich") is None
    elif edition == "tui":
        assert util.find_spec("textual") is not None and util.find_spec("rich") is not None


def test_package_metadata_has_public_project_links():
    links = metadata.metadata("codex-socks-manager").get_all("Project-URL") or []
    assert any(item.startswith("Repository, https://github.com/") for item in links)
    assert any(item.startswith("Issues, https://github.com/") for item in links)


def test_release_workflow_uses_trusted_publishing_and_verified_assets():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/release.yml").read_text()
    assert "id-token: write" in workflow
    assert "environment:\n      name: pypi" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "python -m twine check" in workflow
    assert "cp scripts/install-release.sh dist/github/install.sh" in workflow
    assert "sha256sum *.whl *.tar.gz install.sh > SHA256SUMS" in workflow
    assert "PYPI_API_TOKEN" not in workflow and "password:" not in workflow

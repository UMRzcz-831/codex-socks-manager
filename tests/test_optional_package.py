from importlib import metadata, util
import os


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

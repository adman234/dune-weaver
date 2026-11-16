"""Tests for version_manager repo detection and version comparison."""
import pytest

from modules.core import version_manager as vm


@pytest.mark.parametrize("url,expected", [
    ("https://github.com/adman234/dune-weaver.git", ("adman234", "dune-weaver")),
    ("https://github.com/adman234/dune-weaver", ("adman234", "dune-weaver")),
    ("git@github.com:someone/dw-fork.git\n", ("someone", "dw-fork")),
    ("https://gitlab.com/x/y.git", None),
    ("", None),
])
def test_parse_github_remote(url, expected):
    assert vm._parse_github_remote(url) == expected


def test_env_override(monkeypatch):
    monkeypatch.setenv("DW_GITHUB_REPO", "me/table")
    assert vm._detect_repo() == ("me", "table")


@pytest.mark.parametrize("a,b,expected", [
    ("4.1.4", "4.2.0", -1),
    ("4.2.0", "4.2", 0),
    ("4.10.0", "4.9.9", 1),
])
def test_compare_versions(a, b, expected):
    assert vm.VersionManager().compare_versions(a, b) == expected

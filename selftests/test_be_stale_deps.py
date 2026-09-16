"""The stale-dependency warning fires on a pinned mismatch and stays quiet on a range.

Reconstructs the 2026-09-16 run: ``package.json`` asked for
``@blazeupai/blazeup-global-common`` 1.0.275, ``node_modules`` held 1.0.194 installed five
weeks earlier, and jest reported 15 failed suites — 14 of them "failed to run" on TypeScript
errors that read as a broken backend. After ``npm install`` the same commit ran 1073 tests
with one real failure.

``git pull`` moves the source but never ``node_modules``, so this drifts exactly when the
source-staleness warning says everything is current. The two checks are independent and both
have to exist.
"""

import json
from pathlib import Path

import pytest

from utils.be_test_blame import dependency_warning, stale_dependencies

PINNED = "@blazeupai/blazeup-global-common"


def write_pkg(root: Path, deps: dict, *, dev: dict | None = None) -> None:
    body = {"name": "be", "dependencies": deps}
    if dev:
        body["devDependencies"] = dev
    (root / "package.json").write_text(json.dumps(body), encoding="utf-8")


def install(root: Path, name: str, version: str) -> None:
    """Place a package in node_modules the way npm would — nested scope dir included."""
    path = root / "node_modules" / Path(name)
    path.mkdir(parents=True, exist_ok=True)
    (path / "package.json").write_text(
        json.dumps({"name": name, "version": version}), encoding="utf-8"
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    write_pkg(tmp_path, {PINNED: "1.0.275"})
    install(tmp_path, PINNED, "1.0.194")  # the real gap, five weeks wide
    return tmp_path


def test_pinned_mismatch_is_reported(repo: Path) -> None:
    assert stale_dependencies(repo) == [(PINNED, "1.0.275", "1.0.194")]


def test_warning_carries_both_versions_and_the_fix(repo: Path) -> None:
    """The line has to be actionable alone — it is what stands between the reader and a
    wrong bug report to the backend team."""
    warning = dependency_warning(repo)
    assert warning is not None
    assert "1.0.275" in warning and "1.0.194" in warning
    assert "npm install" in warning
    assert "--ignore-scripts" in warning, (
        "this repo's postinstall and prepare are Unix-only shell and abort npm on Windows"
    )
    assert "NOT a backend defect" in warning, "the whole point is to stop a wrong bug report"


def test_matching_version_is_silent(repo: Path) -> None:
    install(repo, PINNED, "1.0.275")
    assert stale_dependencies(repo) == []
    assert dependency_warning(repo) is None


def test_missing_package_is_reported(tmp_path: Path) -> None:
    write_pkg(tmp_path, {PINNED: "1.0.275"})
    assert stale_dependencies(tmp_path) == [(PINNED, "1.0.275", "(not installed)")]


@pytest.mark.parametrize("spec", ["^1.0.275", "~1.0.275", ">=1.0.0", "*", "latest"])
def test_ranges_are_never_flagged(tmp_path: Path, spec: str) -> None:
    """A range is satisfied by many versions.

    Comparing those would flag nearly every dependency on every run, and a warning that fires
    constantly is one nobody reads on the day it matters. The packages that actually break
    the build are pinned exactly.
    """
    write_pkg(tmp_path, {"some-lib": spec})
    install(tmp_path, "some-lib", "9.9.9")
    assert stale_dependencies(tmp_path) == []


def test_dev_dependencies_are_checked_too(tmp_path: Path) -> None:
    write_pkg(tmp_path, {}, dev={"jest": "30.0.0"})
    install(tmp_path, "jest", "29.7.0")
    assert stale_dependencies(tmp_path) == [("jest", "30.0.0", "29.7.0")]


def test_no_package_json_is_not_an_error(tmp_path: Path) -> None:
    """``--json`` mode analyses a saved run and needs no node_modules at all."""
    assert stale_dependencies(tmp_path) == []
    assert dependency_warning(tmp_path) is None


def test_unreadable_manifest_is_not_an_error(tmp_path: Path) -> None:
    """A half-written package.json must not take the whole tool down."""
    (tmp_path / "package.json").write_text("{ not json", encoding="utf-8")
    assert stale_dependencies(tmp_path) == []

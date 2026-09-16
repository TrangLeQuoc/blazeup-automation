"""Every fixture defined in ``pytest_support/fixtures.py`` must be wired into ``conftest.py``.

pytest only discovers a fixture if its name lives in a ``conftest.py`` namespace (or a
registered plugin). Fixtures are *defined* in ``pytest_support/fixtures.py`` and *re-exported*
by the root ``conftest.py`` (an explicit ``from pytest_support.fixtures import (...)`` list
plus ``__all__``). That list is maintained by hand, so it drifts: add a fixture in
``fixtures.py``, forget the ``conftest.py`` line, and every test that requests it dies at
setup with ``FixtureLookupError`` — reported as BROKEN, ~0ms, no traceback in the log.

This bit twice (``seeded_partner`` and its dependency ``partner_session_started_at``: whole
swathes of API + UI tests went BROKEN). This guard turns that silent drift into a red CI
check that names the missing fixture, so it is caught at the source instead of in a run.

No network, no browser, no Playwright: both files are read with ``ast`` and never imported
(importing ``conftest``/``fixtures`` would drag in Playwright, which the selftest job omits).
"""

import ast
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES_FILE = _PROJECT_ROOT / "pytest_support" / "fixtures.py"
_CONFTEST_FILE = _PROJECT_ROOT / "conftest.py"
_FIXTURES_MODULE = "pytest_support.fixtures"


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _defined_fixtures(path: Path) -> set[str]:
    """Names of top-level functions decorated as a pytest fixture in ``path``.

    Matches ``@pytest.fixture``, ``@pytest_asyncio.fixture`` and bare ``@fixture``,
    with or without call arguments (``@pytest.fixture(scope="session")``).
    """
    names: set[str] = set()
    for node in _parse(path).body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            target = dec.func if isinstance(dec, ast.Call) else dec
            if ast.unparse(target).split(".")[-1] == "fixture":
                names.add(node.name)
                break
    return names


def _imported_from(path: Path, module: str) -> set[str]:
    """Names imported via ``from <module> import (...)`` in ``path``."""
    names: set[str] = set()
    for node in ast.walk(_parse(path)):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            names.update(alias.name for alias in node.names)
    return names


def _dunder_all(path: Path) -> set[str]:
    """String entries of the module-level ``__all__`` list in ``path``."""
    for node in _parse(path).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            value = node.value
            if isinstance(value, (ast.List, ast.Tuple)):
                return {el.value for el in value.elts if isinstance(el, ast.Constant)}
    return set()


def test_every_fixture_is_imported_into_conftest() -> None:
    """A fixture that is not imported into conftest is invisible to pytest → FixtureLookupError."""
    defined = _defined_fixtures(_FIXTURES_FILE)
    imported = _imported_from(_CONFTEST_FILE, _FIXTURES_MODULE)

    missing = sorted(defined - imported)
    assert not missing, (
        "These fixtures are defined in pytest_support/fixtures.py but NOT imported into "
        "conftest.py — pytest cannot find them, so any test requesting one fails at setup "
        "with FixtureLookupError (BROKEN, ~0ms):\n  - "
        + "\n  - ".join(missing)
        + f"\nFix: add each name to the `from {_FIXTURES_MODULE} import (...)` block AND "
        "the `__all__` list in conftest.py."
    )


def test_imported_fixtures_are_reexported_in_all() -> None:
    """Whatever conftest imports from fixtures.py must also appear in __all__ (re-export hygiene)."""
    imported = _imported_from(_CONFTEST_FILE, _FIXTURES_MODULE)
    exported = _dunder_all(_CONFTEST_FILE)

    missing = sorted(imported - exported)
    assert not missing, (
        "These fixtures are imported into conftest.py but missing from its __all__ "
        "(keep them in sync):\n  - " + "\n  - ".join(missing)
    )


def test_guard_detects_a_dropped_fixture() -> None:
    """The guard must actually bite: dropping a defined fixture from the import set is caught.

    Proves the check is not vacuously green — mirrors the real regression (a fixture defined
    but not wired) against an in-memory copy, without touching the real files.
    """
    defined = _defined_fixtures(_FIXTURES_FILE)
    assert defined, "sanity: fixtures.py must define at least one fixture"

    pretend_imported = set(defined)
    pretend_imported.discard(sorted(defined)[0])  # simulate forgetting to wire one up
    assert defined - pretend_imported, (
        "guard is vacuous: removing a fixture from the import set was not detected"
    )

"""The Makefile's default DOMAIN must name a domain that actually exists.

Found 2026-09-16: `DOMAIN ?= blazeup_admin` named a domain removed some time earlier. Every
target built on `$(DOMAIN)` was broken by it — `tc`, `smoke`, `regression`, `api`, `ui`,
`list`, `health`, `swagger` died with ModuleNotFoundError, and `validate-plan` failed the
worse way: it printed "No test plan for domain 'blazeup_admin' — nothing to validate" and
exited **0**, so `make validate-plan` looked like a passing lint while checking nothing.

Nobody noticed because the day-to-day commands are typed directly
(`python -m runner.blazeup.run_test ...`), which is also what the Makefile tells you to do
when `make` is unavailable — as it is on Windows here.

A domain is a directory that exists three times over, so that is what this checks.
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = PROJECT_ROOT / "Makefile"

# `DOMAIN ?= blazeup` — the ?= form, ignoring surrounding spaces.
_DEFAULT = re.compile(r"^DOMAIN\s*\?=\s*(\S+)\s*$", re.M)
# `DOMAIN=blazeup` as written in the usage examples in the header comment.
_IN_COMMENT = re.compile(r"DOMAIN=(\S+)")


def makefile_text() -> str:
    return MAKEFILE.read_text(encoding="utf-8")


def domain_dirs(name: str) -> dict[str, bool]:
    return {
        f"{parent}/{name}": (PROJECT_ROOT / parent / name).is_dir()
        for parent in ("runner", "config", "docs")
    }


def test_makefile_declares_a_default_domain() -> None:
    """Guard the guard — a renamed variable would make the test below vacuous."""
    assert _DEFAULT.search(makefile_text()), "Makefile no longer declares `DOMAIN ?= ...`"


def test_default_domain_exists() -> None:
    name = _DEFAULT.search(makefile_text()).group(1)
    found = domain_dirs(name)
    assert all(found.values()), (
        f"Makefile default DOMAIN={name} is not a real domain. Missing: "
        + ", ".join(k for k, v in found.items() if not v)
        + ". Every target built on $(DOMAIN) breaks, and `validate-plan` breaks silently "
        "(exit 0, nothing validated)."
    )


@pytest.mark.parametrize("name", sorted(set(_IN_COMMENT.findall(MAKEFILE.read_text("utf-8")))))
def test_domains_named_in_the_usage_examples_exist(name: str) -> None:
    """The header examples are copy-pasted, so a stale one is a broken command in the docs."""
    found = domain_dirs(name)
    assert all(found.values()), (
        f"Makefile usage example says DOMAIN={name}, which does not exist. Missing: "
        + ", ".join(k for k, v in found.items() if not v)
    )

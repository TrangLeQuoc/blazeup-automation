"""Registry for the `blazeup` domain — merges runner/blazeup/registry_modules/*.py.
(AUTO-GENERATED — do not edit. Add TCs by writing tests + running utils/sync_registry.py.)

Each top-level module has its own file under registry_modules/ so per-module PRs
don't collide; this file globs + merges them into one TC_REGISTRY.
"""

import importlib
import pkgutil
from pathlib import Path

from runner.blazeup.registry_modules._base import TestCase

TC_REGISTRY: dict[int, TestCase] = {}

_pkg_path = Path(__file__).parent / "registry_modules"
for _m in pkgutil.iter_modules([str(_pkg_path)]):
    if _m.name.startswith("_"):
        continue
    _mod = importlib.import_module(f"runner.blazeup.registry_modules.{_m.name}")
    TC_REGISTRY.update(getattr(_mod, "TC_REGISTRY", {}))


def get_tc(tc_id: int) -> TestCase:
    if tc_id not in TC_REGISTRY:
        raise KeyError(f"TC {tc_id} does not exist in the registry")
    return TC_REGISTRY[tc_id]


def validate_registry() -> None:
    """Verify that all registered test functions exist (optional utility)."""
    for tc in TC_REGISTRY.values():
        if not Path(tc.test_path).exists():
            print(f"Warning: Test file {tc.test_path} missing for TC {tc.tc_id}")


def list_by_module(module: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if tc.module == module]


def list_by_type(tc_type: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if tc.type == tc_type]


def list_by_marker(marker: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if marker in tc.markers]

"""Central TC registry — auto-merges all domain registries.

DO NOT add TCs here directly.  Instead:
  1. Write your test function in tests/{domain}/...
  2. Run: python utils/sync_registry.py --domain {domain}
     This regenerates runner/{domain}/registry.py automatically.

Adding a new domain
-------------------
Create runner/{newdomain}/registry.py (via sync_registry.py).
This file auto-discovers it — no edits needed here.
"""

import importlib
from pathlib import Path
from typing import Literal
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TestCase:
    """Metadata for a single automation test case."""

    tc_id:     int
    tc_string: str
    type:      Literal["api", "ui"]
    module:    str
    title:     str
    test_path: str
    test_func: str
    markers:   list[str] = field(default_factory=list)
    priority:  Literal["P1", "P2", "P3"] = "P2"

    @property
    def node_id(self) -> str:
        return f"{self.test_path}::{self.test_func}"


# Auto-discover and merge all domain registries from runner/*/registry.py
TC_REGISTRY: dict[int, TestCase] = {}

_runner_dir = Path(__file__).parent
for _domain_dir in sorted(_runner_dir.iterdir()):
    _registry_file = _domain_dir / "registry.py"
    if _domain_dir.is_dir() and _registry_file.exists():
        try:
            _mod = importlib.import_module(f"runner.{_domain_dir.name}.registry")
            TC_REGISTRY.update(_mod.TC_REGISTRY)
        except Exception as _e:
            print(f"[tc_registry] Warning: could not load runner/{_domain_dir.name}/registry.py: {_e}")


def get_tc(tc_id: int) -> TestCase:
    if tc_id not in TC_REGISTRY:
        raise KeyError(f"TC {tc_id} does not exist in the registry")
    return TC_REGISTRY[tc_id]


def list_by_module(module: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if tc.module == module]


def list_by_type(tc_type: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if tc.type == tc_type]


def list_by_marker(marker: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if marker in tc.markers]

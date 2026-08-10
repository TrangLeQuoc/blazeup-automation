"""Make the project root importable for the framework's own tests.

These tests live OUTSIDE ``tests/`` on purpose. ``utils/sync_registry.py`` builds the
TC registry by walking every sub-directory of ``tests/`` and globbing ``test_*.py``,
so a unit test parked there would be scanned as if it were a test-case domain.
Keeping them here means the two worlds never touch: ``pytest.ini`` points
``testpaths`` at ``tests/``, so the product suite never picks these up either.

Run them with the project conftest cut off (they need none of its fixtures, and
loading it would drag in Playwright/httpx/Faker for no reason)::

    python -m pytest selftests/ -o addopts= --confcutdir=selftests -q

Write ``addopts=`` without quotes: PowerShell forwards ``""`` literally and pytest
then rejects the value.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

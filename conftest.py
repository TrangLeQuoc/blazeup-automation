"""Pytest discovery entrypoint.

Keep this file thin so pytest can discover project fixtures and hooks while
the implementation stays organized under `pytest_support/`.
"""

from pytest_support.fixtures import *  # noqa: F403
from pytest_support.hooks import *  # noqa: F403


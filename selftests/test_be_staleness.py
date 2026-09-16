"""The stale-clone warning fires when the clone is behind, and stays silent otherwise.

Worth a real git repo rather than a mock. The whole warning exists because all four backend
tools read files on disk, files follow ``HEAD``, and ``HEAD`` only moves on a pull — so the
thing under test IS git's notion of "behind upstream". A mocked ``subprocess.run`` would
prove the parsing and none of the premise.

The dangerous case is ``be_drift``: an unpulled clone has no changes to find, so it prints
"nothing to re-run" — a false all-clear, not an error. A test that only checked the silent
case would have passed against a function that never warns at all.
"""

import os
import subprocess
from pathlib import Path

import pytest

from utils.be_coverage import remote_lag, staleness_warning


def git(repo: Path, *args: str) -> str:
    """Run git against *repo* with no inherited git state.

    Every ``GIT_*`` variable is dropped and the identity supplied explicitly. A git hook
    exports ``GIT_DIR``, ``GIT_INDEX_FILE`` and ``GIT_AUTHOR_*`` to whatever it runs, so when
    this suite runs from a pre-commit hook an inherited ``GIT_DIR`` would point these
    throwaway commands at the REAL repository regardless of ``cwd``. The sibling fixture in
    ``test_be_test_blame.py`` was caught by the identity half of this on 2026-09-16.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_AUTHOR_NAME="QA",
        GIT_AUTHOR_EMAIL="qa@example.invalid",
        GIT_COMMITTER_NAME="QA",
        GIT_COMMITTER_EMAIL="qa@example.invalid",
    )
    out = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True, env=env
    )
    return (out.stdout or "").strip()


@pytest.fixture
def clone_behind(tmp_path: Path) -> Path:
    """A clone whose ``HEAD`` sits one commit behind its upstream.

    Built by pushing two commits and then rewinding the working branch, which leaves
    ``origin/<branch>`` ahead without needing a second clone or a fetch.
    """
    origin = tmp_path / "origin.git"
    origin.mkdir()
    git(origin, "init", "--bare", "--initial-branch=main", ".")

    work = tmp_path / "work"
    work.mkdir()
    git(work, "clone", str(origin), ".")
    for n in (1, 2):
        (work / f"f{n}.ts").write_text(f"export const n = {n};\n", encoding="utf-8")
        git(work, "add", "-A")
        git(work, "commit", "-m", f"commit {n}")
    git(work, "push", "-u", "origin", "main")

    git(work, "reset", "--hard", "HEAD~1")  # now behind origin/main by one
    return work


def test_lag_is_reported_when_the_clone_is_behind(clone_behind: Path) -> None:
    lag = remote_lag(clone_behind)
    assert lag is not None, "a clone one commit behind upstream must report lag"
    count, upstream = lag
    assert count == 1
    assert upstream == "origin/main"


def test_warning_names_both_the_lag_and_the_fix(clone_behind: Path) -> None:
    """The line has to be actionable on its own — it is the only thing the reader sees."""
    warning = staleness_warning(clone_behind)
    assert warning is not None
    assert "origin/main" in warning
    assert "1 commit" in warning and "1 commits" not in warning, "singular for one commit"
    assert "git pull" in warning, "naming the lag without the fix leaves the reader stuck"


def test_silent_when_the_clone_is_current(clone_behind: Path) -> None:
    """No warning once pulled — a warning that cries wolf gets ignored on the day it matters."""
    git(clone_behind, "merge", "--ff-only", "origin/main")
    assert remote_lag(clone_behind) is None
    assert staleness_warning(clone_behind) is None


def test_silent_when_there_is_no_upstream(tmp_path: Path) -> None:
    """A clone with no tracking branch cannot be judged, so it is not accused."""
    solo = tmp_path / "solo"
    solo.mkdir()
    git(solo, "init", "--initial-branch=main", ".")
    (solo / "f.ts").write_text("export const n = 1;\n", encoding="utf-8")
    git(solo, "add", "-A")
    git(solo, "commit", "-m", "only commit")
    assert remote_lag(solo) is None


def test_detached_head_is_not_accused(clone_behind: Path) -> None:
    """``git checkout <sha>`` drops the upstream ref; that is not staleness."""
    sha = git(clone_behind, "rev-parse", "HEAD")
    git(clone_behind, "checkout", "--detach", sha)
    assert remote_lag(clone_behind) is None


def test_never_moves_head(clone_behind: Path) -> None:
    """The clone is input, never written.

    A ``--pull`` flag was the obvious fix and is the reason for this test: it would have
    moved the user's ``HEAD`` as a side effect of asking a read-only question.
    """
    before = git(clone_behind, "rev-parse", "HEAD")
    staleness_warning(clone_behind, fetch=True)
    assert git(clone_behind, "rev-parse", "HEAD") == before

"""Commands printed in the docs must actually run on the shell they are labelled for.

Both guards here come from one paste. The README said

    cd "C:\\Users\\you\\Desktop\\blazeup\\blazeup-microservice-sa-partners" && git pull

which fails twice over on the machine it was written for: the path is a placeholder that
looks real enough to paste, and Windows PowerShell 5.1 has no ``&&`` — it is a parser error,
not a fallback to sequential execution. Neither is caught by ruff, pytest or a doc-sync
check, because nothing else in this repo reads the fenced blocks.
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SKIP_DIRS = {".venv", ".venv-selftest", "node_modules", ".git", "results"}

# ```powershell ... ``` — the language tag is what claims the shell, so it is what binds.
_PS_BLOCK = re.compile(r"^```powershell\s*$(.*?)^```\s*$", re.M | re.S)

# A placeholder home directory that reads as a real path. `<...>` and `$env:` are fine —
# nobody pastes those and expects them to work.
_FAKE_HOME = re.compile(r"[Cc]:[\\/]Users[\\/]you\b")


def markdown_files() -> list[Path]:
    return sorted(
        p
        for p in PROJECT_ROOT.rglob("*.md")
        if not _SKIP_DIRS & set(p.relative_to(PROJECT_ROOT).parts)
    )


def powershell_blocks() -> list[tuple[Path, str]]:
    out = []
    for path in markdown_files():
        for m in _PS_BLOCK.finditer(path.read_text(encoding="utf-8")):
            out.append((path, m.group(1)))
    return out


def test_there_are_blocks_to_check() -> None:
    """Guard the guard: a broken fence regex would make both tests below vacuously pass."""
    assert len(powershell_blocks()) >= 20


@pytest.mark.parametrize(
    ("path", "block"),
    powershell_blocks(),
    ids=[
        f"{p.relative_to(PROJECT_ROOT).as_posix()}:{i}"
        for i, (p, _) in enumerate(powershell_blocks())
    ],
)
def test_powershell_blocks_avoid_bash_chaining(path: Path, block: str) -> None:
    """``&&`` in a block labelled powershell is a parser error on PowerShell 5.1.

    ``;`` chains unconditionally; ``A; if ($?) { B }`` is the conditional form. Neither is
    ``&&``, and the failure is not graceful — the whole line refuses to parse.
    """
    offenders = [line.strip() for line in block.splitlines() if "&&" in line]
    # ASCII only in the message: pytest writes it to a console that may be cp1252, where an
    # em dash arrives as a replacement char. The tool output had the same bug this week.
    assert not offenders, (
        f"{path.relative_to(PROJECT_ROOT).as_posix()}: PowerShell 5.1 has no `&&` -- "
        f"use `;`, or `A; if ($?) {{ B }}` when B depends on A:\n  " + "\n  ".join(offenders)
    )


@pytest.mark.parametrize(
    ("path", "block"),
    powershell_blocks(),
    ids=[
        f"{p.relative_to(PROJECT_ROOT).as_posix()}:{i}"
        for i, (p, _) in enumerate(powershell_blocks())
    ],
)
def test_runnable_blocks_have_no_paste_me_placeholder(path: Path, block: str) -> None:
    """A placeholder inside a *runnable* block gets pasted.

    ``C:\\Users\\you\\...`` is indistinguishable from a real path at a glance, and the app
    puts a Run button on these blocks. Use ``<the path in BLAZEUP_BE_REPO>`` — unmistakably
    not a path — or an env var that resolves.

    Prose and value templates (``BLAZEUP_BE_REPO="C:/Users/you/..."`` showing the shape of a
    config value) are deliberately out of scope: those fail loudly at ``be_repo()``, which
    checks for ``src/`` and says so.
    """
    hits = [line.strip() for line in block.splitlines() if _FAKE_HOME.search(line)]
    assert not hits, (
        f"{path.relative_to(PROJECT_ROOT).as_posix()}: placeholder path in a runnable block "
        f"-- it will be pasted verbatim:\n  " + "\n  ".join(hits)
    )

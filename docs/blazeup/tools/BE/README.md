# Backend cross-check tools — output archive

Four tools read the backend source (`blazeupai/blazeup-microservice-sa-partners`) and
compare it against this suite. Every run archives its output here, dated, so the folder is
a **history** rather than a single always-current file — "when did that number move" is the
question you cannot answer afterwards.

Run all four from the **automation repo**, not the backend clone: they are modules here and
need `api_clients/` and `runner/tc_registry` to name the TCs. The clone is only input and is
never written to.

```
BLAZEUP_BE_REPO="C:/Users/you/Desktop/blazeup/blazeup-microservice-sa-partners"
```

Set once in `config/blazeup/.env` (an environment variable of the same name overrides it).

---

## Before every run: pull the clone

All four read **files on disk**, and those files follow the clone's `HEAD`. `HEAD` only moves
on a `git pull` — `git fetch` alone updates `origin/<branch>` and leaves both `HEAD` and the
working tree exactly where they were. So an unpulled clone makes all four report on yesterday's
source.

```powershell
cd <the path in BLAZEUP_BE_REPO>; git pull
```

Substitute your own path — a plausible-looking `C:\Users\you\...` here just gets pasted and
fails. `;` not `&&`: Windows PowerShell 5.1 has no `&&` and treats it as a parser error.

**One pull covers all four** — they read the same clone. No need to pull again between
commands unless BE merged something while you were running them.

`be_drift` is the one that fails *quietly*: an unpulled clone has no changes to find, so it
prints `No source changes since the baseline. Nothing to re-run.` — a **false all-clear**
rather than an error. The other three print the commit they read, so a stale date is visible.

### The warning

Each of the four prints a line when the clone is behind its upstream:

```
Backend : v26 @ 284ce5e (2026-08-07)
WARNING: origin/v26 has 6 commits this clone does not — `git pull` it and re-run, or you are reading stale source
```

For `be_coverage` it also lands **in the map**, because a map built from a stale clone stays
misleading for as long as the file exists while the console line scrolls away in a minute. For
`be_drift` it prints *above* the all-clear and adds a second line qualifying it. For
`be_test_blame --run` it prints *before* jest starts, so you are not two minutes into a run on
source a pull is about to replace.

It reads the remote-tracking ref **as it already stands**: no network, and nothing writes the
clone. The gap is that `origin/<branch>` is itself only as fresh as your last fetch — add
`--check-remote` to any of the four to `git fetch` first (~3 s, still no write to `HEAD`).

These tools deliberately **never pull for you**. A `--pull` flag was the obvious fix and was
rejected: it would move your `HEAD` as a side effect of asking a read-only question, and it
would break the promise that the clone is only ever input.

## Run order after a pull

| Order | Command | Answers |
|---|---|---|
| 1 | `python -m utils.be_drift` | BE changed what → which TCs to re-run |
| 2 | `python -m utils.be_coverage` | which endpoints nobody tests |
| 3 | `python -m utils.be_unit_audit` | are the BE unit tests protecting anything |
| 4 | `python -m utils.be_test_blame --run` | a BE unit test is red — who, when, what was missed (~2 min) |

`be_drift` goes first because it is the one whose stale output reads as good news, and because
its answer — *what moved* — is what decides whether the other three are worth running today.
`be_test_blame --run` goes last: it is the only one that costs minutes.

---

## 1. `python -m utils.be_coverage`

**Question** — which backend endpoints does anyone test?

**What it does** — extracts every `@Get`/`@Post`/… route from the backend controllers,
extracts every endpoint this suite's `api_clients/` actually calls, and joins them on
method + path. A route counts as unit-tested only when a spec naming its controller
**class** also names the handler.

| | |
|---|---|
| Input | backend `src/**/*.controller.ts` + `**/*.spec.ts` · this repo's `api_clients/` · `runner/tc_registry` |
| Output | `<stamp>_be_coverage_map.md` — one file, the full report |
| Options | `--check-remote` to `git fetch` first, so the staleness warning is current |
| Runtime | seconds |
| Network | none (`--check-remote` adds one fetch, ~3 s) |

The map carries its own provenance: the commit read, how many routes were parsed, how many
client paths resolved, and — if the extractor dropped anything — a warning at the top plus
an **Extraction losses** section at the end. A dropped route reads as *covered*, so those
numbers belong in the report rather than only on the console.

**Reading it** — four quadrants over 101 routes:

| Quadrant | Means |
|---|---|
| `BOTH` | backend unit test **and** QA API test |
| `BE ONLY` | unit test only — the DB is mocked, nothing proves it works wired up |
| `QA ONLY` | **QA is the only safety net**; skipping that TC leaves the endpoint bare |
| `NEITHER` | **nobody tests the HTTP entry point** |

The map groups `NEITHER` by business risk and lists, per endpoint, which TCs hit it.

**Careful** — this is controller-level. `NEITHER` does *not* mean the logic was never
tested; it means no test exercises the HTTP entry point, so the guard, the DTO validation
and the status code are unverified. Say it that way to BE, or they will point at the service
spec and be right.

---

## 2. `python -m utils.be_unit_audit`

**Question** — are those unit tests protecting anything?

**What it does** — four heuristics, all read from **source alone**. No Bug_Tracker lookup,
so a brand-new API is audited the same as an old one.

| Check | Finds |
|---|---|
| `A` | a missing record answered with `400` instead of `404` — both the literal `throw` and the `isThrow: true` helper that raises `BadRequestException` |
| `B` | a test whose NAME claims a rule while its body only proves a stubbed exception passed through. Names about *propagation* are exempt — those do what they say |
| `C` | a controller spec with **no** error assertion at all: only the happy path is pinned |
| `D` | a guard declared with `@UseGuards` that no spec ever names — the authorization path is untested |

| | |
|---|---|
| Input | backend `src/` only |
| Output | `<stamp>_be_unit_audit.md` |
| Options | `--check A` / `B` / `C` / `D` for one at a time · `--check-remote` |
| Runtime | seconds |

**Careful** — none of it proves a test is *wrong*. That needs the PRD and a person. The
tool says where to spend that person's time, and why.

---

## 3. `python -m utils.be_drift`

**Question** — the backend changed; which TCs should I re-run?

**What it does** — diffs the recorded baseline commit against the clone's `HEAD`, walks the
import graph back from every controller (up to 3 hops) to find which endpoints the changed
files can reach, then maps those endpoints to TC ids. Separately reads the **old** tree via
`git show` to spot routes that did not exist before.

| | |
|---|---|
| Input | backend git history · baseline in `docs/api-snapshots/blazeup/be-commit.txt` |
| Output | `<stamp>_be_drift.md` |
| Options | `--base <sha>` to diff an explicit ref · `--save` to record `HEAD` as the new baseline · `--check-remote` |
| Runtime | seconds |

**Reading it** — four blocks:

* `NEW ENDPOINTS` — shipped since the baseline. `NO TC YET` is a coverage gap
* `AFFECTED ENDPOINTS` — with the TC ids that cover them; `— no TC` means BE changed
  something nothing here checks
* `WIDE CHANGE` — a shared module moved; run the whole area rather than the listed TCs
* `RE-RUN` — a ready-to-paste `run_test --execute` line
* `SHARED LIBRARY BUMPED` — a `@blazeupai/*` version changed. Behaviour changes inside those
  packages live in **other repos** and are invisible to the import graph

`--save` does not write a log: it bookmarks a commit, it does not produce a report.

**Careful** — the TC list is a *suggestion*: "TCs touching the affected endpoints", not
"TCs that will fail". And the baseline is **our own bookmark**, not what staging runs — the
service exposes no `/version` endpoint and its deploy tag lives in a shared CI repo.

---

## 4. `python -m utils.be_test_blame --run`

**Question** — this backend unit test is red. Who changed what, and did they update the test?

**What it does** — runs jest (the same one `npm test` runs), then for each failure pulls the
one string that appears on **one side** of the diff only and follows it through git:

```
git log -S "<string>" -- src        which commit put it in the code
git show --name-only <commit>       did that commit touch the failing spec?
git log -S "<string>" -- <spec>     has the spec EVER known about it?
```

| | |
|---|---|
| Input | a jest run · backend git history |
| Output | `<stamp>_be_test_blame.md` · `be-jest.json` (the raw jest output) |
| Options | `--json <file>` analyse a saved run (**default**, keeps the clone read-only)<br>`--run` run jest first (~2 min)<br>`--run <pattern>` run one spec (~10 s)<br>`--check-remote` fetch first — checked *before* jest, so a stale clone costs you 3 s not 2 min |
| Runtime | 2 minutes with `--run`, instant with `--json` |

It prints the `Test Suites: / Tests: / Time:` block, so **`npm test` is not needed
separately** — running both would execute the whole suite twice.

**It also checks `node_modules` against `package.json` before starting jest.** `git pull`
moves the source but never the dependencies, so they drift exactly when the source-staleness
warning says everything is current. Measured 2026-09-16: a run reported **15 failed suites**,
14 of them "failed to run" on TypeScript errors — which reads as a broken backend. The cause
was `@blazeupai/blazeup-global-common` pinned at 1.0.275 while `node_modules` held 1.0.194
from five weeks earlier. After `npm install` the same commit ran **1073 tests with one real
failure**. Only exactly-pinned versions are compared; a range would fire on nearly every
dependency and be ignored by the time it mattered.

On Windows use `npm install --ignore-scripts`: this backend's `postinstall` (`rm -rf`) and
`prepare` (`[ -f ... ]`) are Unix-only shell and abort npm *after* the packages are in place.

**Reading a blame** — the conclusion only appears when two things hold together: the commit
updated *other* specs, and this spec never knew about the change. That combination points at
a stale test rather than wrong code.

**Careful** — it needs a distinctive **string** in the diff. Numeric-only failures
(`expect(count).toBe(3)`), timeouts and environment problems give the search nothing, and it
prints the four commands rather than guessing. A suite that failed to **run** (import error,
locked file) is reported as such and deliberately **not** blamed on any commit — there is no
diff, so a commit name would be a fabrication.

---

## Files in this folder

| Pattern | Contents |
|---|---|
| `<stamp>_be_coverage_map.md` | the full coverage report |
| `<stamp>_be_unit_audit.md` | audit findings |
| `<stamp>_be_drift.md` | drift report |
| `<stamp>_be_test_blame.md` | blame report |
| `be-jest.json` | raw jest output behind the latest blame |

One file per run, `<stamp>` = `YYYYMMDD-HHMMSS`, so `ls` is already in run order. The other
three record the exact command line, because the same tool with different flags produces a
very different report; the coverage map has a header table instead.

**Everything in this folder is gitignored except the two READMEs** — decided 2026-09-16. Four
new dated files appear on every pass, all of them re-derivable by running the tool again, so
they are local history rather than repo content. `.gitignore` excludes the directory and
re-admits the READMEs, which means a tool added later needs no new rule.

The consequence to be aware of: this history lives on **one machine**. Delete the folder, or
work from a fresh clone, and the "when did that number move" question stops being answerable.
If you ever need a report to survive that, copy it out of here — committing it back is the
only thing the ignore rule prevents.

## These are outputs, not sources

Nothing reads this folder. Deleting it loses history and breaks nothing.

---

> Vietnamese: [README_vi.md](README_vi.md). These two are **not** checked for sync
> automatically (the selftest only constrains `*_TEST_CASES.md` pairs), so edit both.

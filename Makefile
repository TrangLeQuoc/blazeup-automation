# BlazeUp Automation — common tasks.
#
# Pick the domain with DOMAIN=... (default: blazeup).  Each domain runner sets
# BLAZEUP_DOMAIN so the matching config/{domain}/.env is loaded and only that
# domain's test cases are scoped.
#
# A domain is a directory that exists three times over — runner/{domain}/,
# config/{domain}/, docs/{domain}/.  Today there is exactly one: `blazeup`.
# The default used to be `blazeup_admin`, a domain that no longer exists, which
# made every target below fail: the runner ones with ModuleNotFoundError, and
# `validate-plan` SILENTLY — it printed "nothing to validate" and exited 0.
#
#   make tc 10101 10102                  # run TCs on the default domain
#   make tc DOMAIN=blazeup 10101         # name the domain explicitly
#   make smoke                           # smoke-marked TCs
#   make regression                      # P1 regression suite
#   make sync                            # regenerate the TC registry
#   make validate-plan                   # lint the Excel test plan vs the column contract
#   make report                          # open the latest Allure results
#   make health                          # are the backend API services alive?
#   make swagger                         # show Swagger drift vs the saved baseline
#   make swagger-save                    # save Swagger baseline + update CHANGELOG
#   make be-coverage                     # which endpoints nobody tests (needs a BE clone)
#   make be-drift                        # what changed in the backend -> which TCs to re-run
#   make be-audit                        # are the BE unit tests protecting anything?
#   make be-blame JSON=path              # why is a BE unit test red — who, when, what was missed

DOMAIN ?= blazeup
RUN = python -m runner.$(DOMAIN).run_test

# Run selected TC numbers: make tc 1 5 1001
tc:
	$(RUN) --execute $(filter-out $@,$(MAKECMDGOALS))

smoke:
	$(RUN) --mode smoke

regression:
	$(RUN) --mode regression

api:
	$(RUN) --type api

ui:
	$(RUN) --type ui

list:
	$(RUN) --list

# Regenerate the dependency locks after editing requirements.txt.
# requirements.txt stays the human-readable source (16 direct pins + comments); the
# locks add the ~25 transitive packages that would otherwise float free and can turn
# CI red on a day nothing changed.
#   --python-platform linux : CI runs ubuntu-latest. Locking on Windows without this
#                             produces a lock that fails to install on the runner.
# No make on Windows? Run the two uv lines directly.
lock:
	uv pip compile requirements.txt -o requirements.lock --python-platform linux --python-version 3.13 --no-header
	uv pip compile requirements-selftest.txt -o requirements-selftest.lock --python-platform linux --python-version 3.13 --no-header
	uv pip compile requirements-dev.txt -o requirements-dev.lock --python-platform linux --python-version 3.13 --no-header

# Framework selftests — the runner/registry logic itself, plus the be_gap traceability
# chain (marker id <-> TEST_CASES docs <-> Bug_Tracker). No staging, no browser,
# no secrets; runs in about a second. Same command CI uses (selftest.yml).
#   -o addopts=   : pytest.ini's --alluredir needs allure-pytest, not used here
#                   (write it WITHOUT quotes — PowerShell passes `""` through literally)
#   --confcutdir  : keep the project conftest (Playwright fixtures) out
# No make on Windows? Run the same line directly:
#   python -m pytest selftests/ -o addopts= --confcutdir=selftests -q
selftest:
	python -m pytest selftests/ -o addopts= --confcutdir=selftests -q

# Same selftests, but in a THROWAWAY venv built from requirements-selftest.lock — i.e.
# what selftest.yml actually installs. Run this before pushing a new selftest.
#
# Why it exists: your working env has the full requirements.txt, so a selftest that
# imports something missing from the LOCK still passes locally and only turns red on
# push. That happened twice — `pydantic` (the API clients' schemas) was absent from the
# lock, and separately a module-level `importorskip` silently took 17 Playwright-FREE
# tests out of the CI run while the local count looked unchanged.
#
# Expect exactly ONE skip: test_shared_session_wait_ready.py needs a page object.
# No make on Windows? Run these three lines directly.
selftest-ci:
	python -m venv .venv-selftest
	.venv-selftest/Scripts/python -m pip install -q -r requirements-selftest.lock
	.venv-selftest/Scripts/python -m pytest selftests/ -o addopts= --confcutdir=selftests -q -rs

# Regenerate runner/{domain}/registry.py from tests/{domain}/ (all domains).
sync:
	python utils/sync_registry.py

# Lint the Excel test plan against the column contract (read-only; exit 1 on errors).
validate-plan:
	python utils/validate_test_plan.py --domain $(DOMAIN)

report:
	allure serve $$(ls -dt results/run_* | head -1)/allure-results

# ── Backend source cross-check (needs a clone, no staging) ──────────────────
# Reads a local clone of blazeupai/blazeup-microservice-sa-partners. Set BLAZEUP_BE_REPO in
# config/blazeup/.env (an env var of the same name overrides it):
#   export BLAZEUP_BE_REPO="/c/Users/you/Desktop/blazeup/blazeup-microservice-sa-partners"
#
# Complements `make swagger`, which detects CONTRACT drift against a saved OpenAPI
# baseline. Swagger cannot see a change that leaves the contract intact — which is most of
# them — and says nothing about whether an endpoint is tested.
#
# Run these from THIS repo, not the backend clone: they are modules here and need
# api_clients/ + runner/tc_registry to name the TCs. The backend clone is only input.
#
# Every run archives its output to docs/blazeup/tools/BE/<timestamp>_<tool>.md — the
# generated reports are always "now", those logs are the history.
#
# PULL THE CLONE FIRST — all four read files on disk, and those follow the clone's HEAD.
# HEAD only moves on `git pull` (fetch alone leaves the working tree untouched), so an
# unpulled clone makes all four report on yesterday's source. One pull covers all four.
#   cd <backend clone> && git pull
#
# Each tool warns when the clone is behind its upstream, reading the remote-tracking ref as
# it stands (no network, no write). Add --check-remote to fetch first (~3 s). They never pull
# for you: that would move your HEAD as a side effect of a read-only question.
#
# Run order after a pull: be-drift, be-coverage, be-audit, be-blame. be-drift first because
# it is the only one whose stale output reads as good news ("nothing to re-run"), and its
# answer decides whether the rest are worth running today; be-blame last, it costs minutes.
#
# No make on Windows? Run the python line under each target directly.

# Which endpoints have a backend unit test, a QA API test, both, or neither. Writes a dated
# map into docs/blazeup/tools/BE/ rather than overwriting one file.
#   python -m utils.be_coverage
be-coverage:
	python -m utils.be_coverage

# What changed in the backend since the recorded baseline, and which TCs to re-run.
# Pull the backend clone first, or it reports "nothing to re-run" — a false all-clear.
#   python -m utils.be_drift               (add --check-remote to fetch + verify first)
be-drift:
	python -m utils.be_drift

# Record the backend clone's HEAD as the new baseline — do this after reconciling a deploy.
#   python -m utils.be_drift --save
be-drift-save:
	python -m utils.be_drift --save

# Are the backend's unit tests protecting anything? Four source-only heuristics: not-found
# answered 400, tests that assert what they stubbed, controller specs with no error path,
# guards no spec exercises. Reads source only, so a brand-new API is audited like an old one.
#   python -m utils.be_unit_audit            (add --check A|B|C|D for one)
be-audit:
	python -m utils.be_unit_audit

# Why is a backend unit test red: which commit introduced the difference, whether that
# commit updated the other specs but missed this one, and how long it has been red.
#   python -m utils.be_test_blame --json <jest.json>   analyse a saved run (read-only)
#   python -m utils.be_test_blame --run                let it run jest first (~2 min)
be-blame:
	python -m utils.be_test_blame --json $(JSON)

# ── Backend monitoring (per-domain) ─────────────────────────────────────────
# Health-check: ping each service's /health (is the backend alive?).
health:
	python -m runner.$(DOMAIN).health

# Swagger drift: compare each service's live OpenAPI spec to the saved baseline
# (shows ADDED / REMOVED / CHANGED endpoints). Read-only.
swagger:
	python -m runner.$(DOMAIN).swagger_check

# Save the current Swagger as the new baseline + append the per-domain CHANGELOG.
swagger-save:
	python -m runner.$(DOMAIN).swagger_check --save

%:
	@:

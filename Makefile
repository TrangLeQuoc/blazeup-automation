# BlazeUp Automation — common tasks.
#
# Pick the domain with DOMAIN=... (default: blazeup_admin).  Each domain runner
# sets BLAZEUP_DOMAIN so the matching config/{domain}/.env is loaded and only
# that domain's test cases are scoped.
#
#   make tc 10101 10102                  # run TCs on the default domain
#   make tc DOMAIN=blazeup_partner 10101 # run TCs on the partner domain
#   make smoke DOMAIN=blazeup_partner    # smoke-marked TCs for a domain
#   make regression                      # P1 regression suite
#   make sync                            # regenerate the TC registry
#   make validate-plan                   # lint the Excel test plan vs the column contract
#   make report                          # open the latest Allure results
#   make health                          # are the backend API services alive?
#   make swagger                         # show Swagger drift vs the saved baseline
#   make swagger-save                    # save Swagger baseline + update CHANGELOG

DOMAIN ?= blazeup_admin
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

# Framework selftests — the runner/registry logic itself. No staging, no browser,
# no secrets; runs in about a second. Same command CI uses (selftest.yml).
#   -o addopts=   : pytest.ini's --alluredir needs allure-pytest, not used here
#                   (write it WITHOUT quotes — PowerShell passes `""` through literally)
#   --confcutdir  : keep the project conftest (Playwright fixtures) out
# No make on Windows? Run the same line directly:
#   python -m pytest selftests/ -o addopts= --confcutdir=selftests -q
selftest:
	python -m pytest selftests/ -o addopts= --confcutdir=selftests -q

# Regenerate runner/{domain}/registry.py from tests/{domain}/ (all domains).
sync:
	python utils/sync_registry.py

# Lint the Excel test plan against the column contract (read-only; exit 1 on errors).
validate-plan:
	python utils/validate_test_plan.py --domain $(DOMAIN)

report:
	allure serve $$(ls -dt results/run_* | head -1)/allure-results

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

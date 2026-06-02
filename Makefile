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
#   make report                          # open the latest Allure results

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

# Regenerate runner/{domain}/registry.py from tests/{domain}/ (all domains).
sync:
	python utils/sync_registry.py

report:
	allure serve $$(ls -dt results/run_* | head -1)/allure-results

%:
	@:

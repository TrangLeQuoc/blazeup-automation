# Run selected TC numbers: make tc 1 5 1001
tc:
	python -m runner.run_test --execute $(filter-out $@,$(MAKECMDGOALS))

smoke:
	python -m runner.run_test --marker smoke

regression:
	python -m runner.run_test --type api --type ui

api:
	python -m runner.run_test --type api

ui:
	python -m runner.run_test --type ui

list:
	python -m runner.run_test --list

report:
	allure serve $$(ls -dt results/run_* | head -1)/allure-results

%:
	@:

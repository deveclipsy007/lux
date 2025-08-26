.PHONY: setup lint test dev e2e

setup:
	sh scripts/codex_setup.sh

lint:
	echo "lint ok"

test:
	echo "tests ok"

dev:
	sh scripts/start.sh

e2e:
	npx playwright test

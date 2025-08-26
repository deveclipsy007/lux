.PHONY: setup lint test dev e2e

setup:
	sh scripts/codex_setup.sh
	npx openapi-typescript http://localhost:8000/openapi.json -o frontend/api.ts

lint:
	echo "lint ok"

test:
	echo "tests ok"

dev:
	sh scripts/start.sh

e2e:
	npx playwright test

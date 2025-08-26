# Agent Instructions

## Scope
These instructions apply to the entire repository.

## Workflow
- Use the provided Makefile targets to setup, lint and test before committing: `make setup lint test`.
- Use `make dev` to run a local development environment and `make e2e` for end-to-end checks.
- Use `rg` for searching the repository instead of recursive `grep`.

## Code Style
- Shell scripts must be POSIX compatible and start with `#!/bin/sh` and `set -e`.
- Keep Makefile targets simple and cross-platform.

## Environment Configuration
- Configure a `.env` file with the required settings.
- Define `DB_PROVIDER` (e.g., `sqlite` or `postgres`).
- Define `DATABASE_URL`; this is mandatory when `DB_PROVIDER=postgres`.
- Ensure the `.env` file is not committed and has restricted permissions (e.g., `chmod 600 .env`).

## Do not
- Do not modify files inside `node_modules/` or generated artifacts.
- Do not store secrets in the repository.

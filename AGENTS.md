# Agent Instructions

## Scope
These instructions apply to the entire repository.

## Workflow
- Use the provided Makefile targets to setup, lint and test before committing: `make setup lint test`.
- Use `make dev` to run a local development environment and `make e2e` for end-to-end checks.

## Code Style
- Shell scripts must be POSIX compatible and start with `#!/bin/sh` and `set -e`.
- Keep Makefile targets simple and cross-platform.

## Do not
- Do not modify files inside `node_modules/` or generated artifacts.
- Do not store secrets in the repository.

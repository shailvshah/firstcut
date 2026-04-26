.DEFAULT_GOAL := help
.PHONY: help install lint format format-check typecheck test secrets-init secrets quality release-check firstcut

RUNNER = uv run

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install dev dependencies
	uv sync --all-extras

lint: ## ruff check (zero warnings)
	$(RUNNER) ruff check .

format: ## Auto-format with ruff + black
	$(RUNNER) ruff format .
	$(RUNNER) black .

format-check: ## Check formatting without writing (used in CI)
	$(RUNNER) ruff format --check .
	$(RUNNER) black --check .

typecheck: ## mypy --strict
	$(RUNNER) mypy src/ tests/ --strict

test: ## pytest with coverage gate
	$(RUNNER) pytest

secrets-init: ## Create .secrets.baseline (run once after cloning)
	$(RUNNER) detect-secrets scan > .secrets.baseline

secrets: ## Scan for new secrets against baseline
	$(RUNNER) detect-secrets scan --baseline .secrets.baseline

quality: lint format-check typecheck test secrets ## All gates: lint + format-check + typecheck + test + secrets

release-check: quality ## Build distributions and validate PyPI metadata
	uv build
	$(RUNNER) twine check dist/*

firstcut: ## Run the interactive scaffolder
	$(RUNNER) firstcut init

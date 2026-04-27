.DEFAULT_GOAL := help
.PHONY: help install lint format format-check typecheck test secrets-init secrets quality release-bump release-metadata pypi-check npm-check go-check release-check release-prepare release-tag release-tag-dirty firstcut

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

release-bump: ## Update PyPI/GitHub/Go and npm versions (VERSION=x.y.z, optional NPM_VERSION=x.y.z)
	@test -n "$(VERSION)" || (echo "VERSION is required, e.g. make release-bump VERSION=0.1.1" && exit 1)
	python3 scripts/release_bump.py $(VERSION) $(if $(NPM_VERSION),--npm-version $(NPM_VERSION),)

release-metadata: ## Validate PyPI, npm, and Go release metadata
	python3 scripts/release_check.py

pypi-check: ## Build Python distributions and validate PyPI metadata
	uv build
	$(RUNNER) twine check dist/*

npm-check: ## Validate npm launcher package contents
	cd packages/npm && npm pack --dry-run

go-check: ## Validate Go launcher module
	cd packages/go && go test ./...
	cd packages/go && go list ./...

release-check: release-metadata quality pypi-check npm-check go-check ## Validate all release surfaces without publishing

release-prepare: release-bump release-check ## Bump versions and validate release readiness (VERSION=x.y.z)

release-tag: release-check ## Create local GitHub/PyPI and Go tags (VERSION=x.y.z)
	@test -n "$(VERSION)" || (echo "VERSION is required, e.g. make release-tag VERSION=0.1.1" && exit 1)
	python3 scripts/release_tag.py $(VERSION)

release-tag-dirty: release-check ## Commit known release files, then create local tags (VERSION=x.y.z)
	@test -n "$(VERSION)" || (echo "VERSION is required, e.g. make release-tag-dirty VERSION=0.1.1" && exit 1)
	python3 scripts/release_tag.py $(VERSION) --allow-dirty

firstcut: ## Run the interactive scaffolder
	$(RUNNER) firstcut init

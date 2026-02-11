# codeindex Makefile
# Automated release and development workflow

.PHONY: help install install-dev install-hooks test lint clean build release bump-version check-version

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
RESET := \033[0m

help:  ## Show this help message
	@echo "$(CYAN)codeindex Makefile$(RESET)"
	@echo ""
	@echo "$(GREEN)Development Commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Release Commands:$(RESET)"
	@echo "  $(CYAN)make release VERSION=0.13.0$(RESET)  - Full release workflow (tag + push)"
	@echo "  $(CYAN)make bump-version VERSION=0.13.0$(RESET) - Update version in files"
	@echo ""

install:  ## Install package in editable mode
	pip install -e ".[all]"

install-dev:  ## Install package with dev dependencies
	pip install -e ".[dev,all]"

install-hooks:  ## Install Git hooks for automated checks
	@echo "$(CYAN)Installing Git hooks...$(RESET)"
	@mkdir -p .git/hooks
	@cp scripts/hooks/pre-push .git/hooks/pre-push
	@chmod +x .git/hooks/pre-push
	@echo "$(GREEN)✓ Git hooks installed$(RESET)"
	@echo "  - pre-push: runs tests and lint before pushing"

test:  ## Run all tests
	@echo "$(CYAN)Running tests...$(RESET)"
	pytest -v

test-fast:  ## Run tests without coverage
	@echo "$(CYAN)Running fast tests...$(RESET)"
	pytest -v -x

test-cov:  ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(RESET)"
	pytest --cov=src/codeindex --cov-report=term-missing --cov-report=html

lint:  ## Run linter (ruff)
	@echo "$(CYAN)Running linter...$(RESET)"
	ruff check src/ tests/

lint-fix:  ## Auto-fix linting issues
	@echo "$(CYAN)Auto-fixing lint issues...$(RESET)"
	ruff check --fix src/ tests/

format:  ## Format code with ruff
	@echo "$(CYAN)Formatting code...$(RESET)"
	ruff format src/ tests/

clean:  ## Clean build artifacts
	@echo "$(CYAN)Cleaning build artifacts...$(RESET)"
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Cleaned$(RESET)"

build: clean  ## Build distribution packages
	@echo "$(CYAN)Building distribution packages...$(RESET)"
	python -m build
	@echo "$(GREEN)✓ Built: dist/$(RESET)"
	@ls -lh dist/

check-dist: build  ## Check distribution with twine
	@echo "$(CYAN)Checking distribution...$(RESET)"
	twine check dist/*
	@echo "$(GREEN)✓ Distribution OK$(RESET)"

# Version management (updates pyproject.toml)
bump-version:  ## Update version in pyproject.toml (usage: make bump-version VERSION=0.13.0)
ifndef VERSION
	@echo "$(RED)Error: VERSION not specified$(RESET)"
	@echo "Usage: make bump-version VERSION=0.13.0"
	@exit 1
endif
	@echo "$(CYAN)Updating version to $(VERSION)...$(RESET)"
	@sed -i.bak 's/^version = .*/version = "$(VERSION)"/' pyproject.toml
	@rm -f pyproject.toml.bak
	@echo "$(GREEN)✓ Updated pyproject.toml$(RESET)"
	@git diff pyproject.toml

check-version:  ## Verify version consistency
	@echo "$(CYAN)Checking version consistency...$(RESET)"
	@PYPROJECT_VERSION=$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	LATEST_TAG=$$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//'); \
	echo "  pyproject.toml: $$PYPROJECT_VERSION"; \
	echo "  Latest Git tag: $$LATEST_TAG"; \
	if [ "$$PYPROJECT_VERSION" != "$$LATEST_TAG" ]; then \
		echo "$(YELLOW)⚠ Version mismatch!$(RESET)"; \
		echo "Run: make bump-version VERSION=$$LATEST_TAG"; \
	else \
		echo "$(GREEN)✓ Versions match$(RESET)"; \
	fi

# Release workflow
pre-release-check:  ## Pre-release checks (tests, lint, version)
ifndef VERSION
	@echo "$(RED)Error: VERSION not specified$(RESET)"
	@echo "Usage: make release VERSION=0.13.0"
	@exit 1
endif
	@echo "$(CYAN)=== Pre-release checks for v$(VERSION) ===$(RESET)"
	@echo ""
	@echo "$(CYAN)[1/5] Checking Git status...$(RESET)"
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "$(RED)Error: Working directory not clean$(RESET)"; \
		git status --short; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Working directory clean$(RESET)"
	@echo ""
	@echo "$(CYAN)[2/5] Checking branch...$(RESET)"
	@BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$BRANCH" != "master" ]; then \
		echo "$(RED)Error: Not on master branch (current: $$BRANCH)$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ On master branch$(RESET)"
	@echo ""
	@echo "$(CYAN)[3/5] Running tests...$(RESET)"
	@pytest -v --tb=short || (echo "$(RED)✗ Tests failed$(RESET)"; exit 1)
	@echo "$(GREEN)✓ All tests passed$(RESET)"
	@echo ""
	@echo "$(CYAN)[4/5] Running linter...$(RESET)"
	@ruff check src/ tests/ || (echo "$(RED)✗ Lint errors found$(RESET)"; exit 1)
	@echo "$(GREEN)✓ No lint errors$(RESET)"
	@echo ""
	@echo "$(CYAN)[5/5] Checking CHANGELOG has version entry...$(RESET)"
	@if ! grep -q "## \[$(VERSION)\]" CHANGELOG.md; then \
		echo "$(RED)Error: Version [$(VERSION)] not found in CHANGELOG.md$(RESET)"; \
		echo "$(YELLOW)  Please add a '## [$(VERSION)] - YYYY-MM-DD' section to CHANGELOG.md$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ CHANGELOG.md has version [$(VERSION)]$(RESET)"
	@echo ""
	@echo "$(GREEN)=== All pre-release checks passed ===$(RESET)"

release: pre-release-check bump-version  ## Full release workflow (usage: make release VERSION=0.13.0)
	@echo ""
	@echo "$(CYAN)=== Creating release v$(VERSION) ===$(RESET)"
	@echo ""
	@echo "$(CYAN)[1/4] Committing version bump...$(RESET)"
	@git add pyproject.toml
	@git commit -m "chore: bump version to $(VERSION)" || echo "No changes to commit"
	@echo ""
	@echo "$(CYAN)[2/4] Creating tag v$(VERSION)...$(RESET)"
	@git tag -a "v$(VERSION)" -m "Release v$(VERSION)" || \
		(echo "$(RED)Error: Tag v$(VERSION) already exists$(RESET)"; exit 1)
	@echo "$(GREEN)✓ Tag created$(RESET)"
	@echo ""
	@echo "$(CYAN)[3/4] Pushing to origin...$(RESET)"
	@git push origin master
	@git push origin "v$(VERSION)"
	@echo "$(GREEN)✓ Pushed to origin$(RESET)"
	@echo ""
	@echo "$(CYAN)[4/4] GitHub Actions will now:$(RESET)"
	@echo "  - Run tests on Python 3.10, 3.11, 3.12"
	@echo "  - Build distribution packages"
	@echo "  - Publish to PyPI (using trusted publisher)"
	@echo "  - Create GitHub Release with assets"
	@echo ""
	@echo "$(GREEN)=== Release v$(VERSION) initiated! ===$(RESET)"
	@echo "$(YELLOW)→ Monitor progress:$(RESET) https://github.com/$$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"

# Development helpers
watch-test:  ## Watch for changes and run tests
	@echo "$(CYAN)Watching for changes...$(RESET)"
	@while true; do \
		inotifywait -r -e modify src/ tests/ 2>/dev/null || \
		fswatch -1 src/ tests/ 2>/dev/null || \
		sleep 2; \
		clear; \
		make test-fast; \
	done

status:  ## Show git and version status
	@echo "$(CYAN)=== codeindex Status ===$(RESET)"
	@echo ""
	@echo "$(GREEN)Version:$(RESET)"
	@PYPROJECT_VERSION=$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	LATEST_TAG=$$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//'); \
	echo "  pyproject.toml: $$PYPROJECT_VERSION"; \
	echo "  Latest Git tag: $$LATEST_TAG"
	@echo ""
	@echo "$(GREEN)Git:$(RESET)"
	@git status --short --branch
	@echo ""
	@echo "$(GREEN)Recent commits:$(RESET)"
	@git log --oneline --graph --decorate -5
	@echo ""
	@echo "$(GREEN)Recent tags:$(RESET)"
	@git tag | tail -5

# CI helpers (used by GitHub Actions)
ci-install:  ## Install dependencies for CI
	pip install -e ".[dev,all]"
	pip install build twine

ci-test:  ## Run tests in CI mode
	pytest -v --tb=short

ci-build:  ## Build and check distribution for CI
	python -m build
	twine check dist/*

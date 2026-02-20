# codeindex Makefile
# Automated release and development workflow

.PHONY: help install install-dev install-hooks \
        test test-fast test-cov lint lint-fix format clean \
        check-version check-docs status build check-dist \
        pre-release-check release bump-version \
        validate-real-projects validate-l1 validate-l2 validate-l3 validate-save-baseline \
        ci-install ci-test ci-build

# Colors
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
RESET := \033[0m

# ============================================================================
# Help
# ============================================================================

help:  ## Show this help message
	@echo "$(CYAN)codeindex Makefile$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Examples:$(RESET)"
	@echo "  make release VERSION=0.19.0    Full release workflow"
	@echo "  make bump-version VERSION=0.20.0  Update version only"

# ============================================================================
# Setup
# ============================================================================

install:  ## Install package in editable mode
	pip install -e ".[all]"

install-dev:  ## Install with dev dependencies
	pip install -e ".[dev,all]"

install-hooks:  ## Install Git hooks (pre-commit, pre-push)
	@echo "$(CYAN)Installing Git hooks...$(RESET)"
	@mkdir -p .git/hooks
	@cp scripts/hooks/pre-push .git/hooks/pre-push
	@chmod +x .git/hooks/pre-push
	@echo "$(GREEN)✓ Git hooks installed$(RESET)"

# ============================================================================
# Development
# ============================================================================

test:  ## Run all tests
	pytest -v

test-fast:  ## Run tests (stop on first failure)
	pytest -v -x

test-cov:  ## Run tests with coverage report
	pytest --cov=src/codeindex --cov-report=term-missing --cov-report=html

lint:  ## Run linter (ruff)
	ruff check src/ tests/

lint-fix:  ## Auto-fix linting issues
	ruff check --fix src/ tests/

format:  ## Format code with ruff
	ruff format src/ tests/

clean:  ## Clean build artifacts
	@rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Cleaned$(RESET)"

# ============================================================================
# Quality Checks
# ============================================================================

check-version:  ## Verify version consistency across all files
	@python3 scripts/check_version_consistency.py || \
		(echo "$(RED)✗ Version inconsistency found$(RESET)"; \
		echo "Run: python3 scripts/check_version_consistency.py --fix"; exit 1)

check-docs:  ## Check documentation for stale content
	@python3 scripts/check_docs_release.py

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

# ============================================================================
# Build & Distribution
# ============================================================================

build: clean  ## Build distribution packages
	python -m build
	@echo "$(GREEN)✓ Built: dist/$(RESET)"
	@ls -lh dist/

check-dist: build  ## Build and check distribution with twine
	twine check dist/*
	@echo "$(GREEN)✓ Distribution OK$(RESET)"

# ============================================================================
# Release
# ============================================================================

bump-version:  ## Update version in pyproject.toml (usage: make bump-version VERSION=X.Y.Z)
ifndef VERSION
	@echo "$(RED)Error: VERSION not specified$(RESET)"
	@echo "Usage: make bump-version VERSION=0.20.0"
	@exit 1
endif
	@echo "$(CYAN)Updating version to $(VERSION)...$(RESET)"
	@sed -i.bak 's/^version = .*/version = "$(VERSION)"/' pyproject.toml
	@rm -f pyproject.toml.bak
	@echo "$(GREEN)✓ Updated pyproject.toml$(RESET)"
	@git diff pyproject.toml

pre-release-check:  ## Pre-release checks (tests, lint, version, docs)
ifndef VERSION
	@echo "$(RED)Error: VERSION not specified$(RESET)"
	@echo "Usage: make release VERSION=0.20.0"
	@exit 1
endif
	@echo "$(CYAN)=== Pre-release checks for v$(VERSION) ===$(RESET)"
	@echo ""
	@echo "$(CYAN)[1/7] Checking Git status...$(RESET)"
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "$(RED)Error: Working directory not clean$(RESET)"; \
		git status --short; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Working directory clean$(RESET)"
	@echo ""
	@echo "$(CYAN)[2/7] Checking branch...$(RESET)"
	@BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$BRANCH" != "master" ]; then \
		echo "$(RED)Error: Not on master branch (current: $$BRANCH)$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ On master branch$(RESET)"
	@echo ""
	@echo "$(CYAN)[3/7] Running tests...$(RESET)"
	@pytest -v --tb=short || (echo "$(RED)✗ Tests failed$(RESET)"; exit 1)
	@echo "$(GREEN)✓ All tests passed$(RESET)"
	@echo ""
	@echo "$(CYAN)[4/7] Running linter...$(RESET)"
	@ruff check src/ tests/ || (echo "$(RED)✗ Lint errors found$(RESET)"; exit 1)
	@echo "$(GREEN)✓ No lint errors$(RESET)"
	@echo ""
	@echo "$(CYAN)[5/7] Checking release notes...$(RESET)"
	@if [ ! -f "RELEASE_NOTES_v$(VERSION).md" ]; then \
		echo "$(RED)Error: RELEASE_NOTES_v$(VERSION).md not found$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Release notes found$(RESET)"
	@echo ""
	@echo "$(CYAN)[6/7] Checking version consistency...$(RESET)"
	@python3 scripts/check_version_consistency.py || \
		(echo "$(RED)✗ Version inconsistency found$(RESET)"; \
		echo "Run: python3 scripts/check_version_consistency.py --fix"; exit 1)
	@echo "$(GREEN)✓ Version consistency OK$(RESET)"
	@echo ""
	@echo "$(CYAN)[7/7] Checking documentation consistency...$(RESET)"
	@python3 scripts/check_docs_release.py || true
	@echo ""
	@echo "$(GREEN)=== All pre-release checks passed ===$(RESET)"

release: pre-release-check bump-version  ## Full release (usage: make release VERSION=X.Y.Z)
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
	@echo "$(YELLOW)→ Monitor:$(RESET) https://github.com/$$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"

# ============================================================================
# Validation (real project testing)
# ============================================================================

validate-real-projects:  ## Run all validation layers on real projects
	python scripts/validate_real_projects.py

validate-l1:  ## L1 functional validation (fast, no AI)
	python scripts/validate_real_projects.py --layer l1

validate-l2:  ## L2 quality validation (metrics + AI)
	python scripts/validate_real_projects.py --layer l2

validate-l3:  ## L3 experience validation (AI only)
	python scripts/validate_real_projects.py --layer l3

validate-save-baseline:  ## Save validation results as baseline
	python scripts/validate_real_projects.py --save-baseline

# ============================================================================
# CI (used by GitHub Actions)
# ============================================================================

ci-install:  ## CI: install dependencies
	pip install -e ".[dev,all]"
	pip install build twine

ci-test:  ## CI: run tests
	pytest -v --tb=short

ci-build:  ## CI: build and check distribution
	python -m build
	twine check dist/*

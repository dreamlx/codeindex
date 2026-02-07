# Contributing to codeindex

Thank you for your interest in contributing to codeindex! 🎉

We welcome contributions of all kinds: bug reports, feature requests, documentation improvements, and code contributions.

---

## 📚 Before You Start

**Read these first**:
- [CLAUDE.md](CLAUDE.md) - Comprehensive developer guide
- [README.md](README.md) - Project overview and features
- [docs/development/requirements-workflow.md](docs/development/requirements-workflow.md) - Issue and planning workflow

---

## 🚀 Quick Start

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR-USERNAME/codeindex.git
cd codeindex
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies with dev extras
pip install -e ".[dev,all]"

# Verify installation
codeindex --version
pytest --version
ruff --version
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/my-awesome-feature
```

---

## 🧪 Development Workflow (TDD Required)

We follow **Test-Driven Development (TDD)**. This is not optional.

### Red → Green → Refactor

```bash
# 1. RED: Write failing tests first
vim tests/test_my_feature.py
pytest tests/test_my_feature.py -v
# Expected: Tests FAIL ❌

# 2. GREEN: Write minimal code to pass tests
vim src/codeindex/my_feature.py
pytest tests/test_my_feature.py -v
# Expected: Tests PASS ✅

# 3. REFACTOR: Optimize while keeping tests green
ruff check src/
pytest  # All tests still pass
```

### Pre-commit Checklist

Before committing:

```bash
# ✅ All tests pass
pytest -v

# ✅ Code style check
ruff check src/

# ✅ Type check (optional but recommended)
mypy src/codeindex/

# ✅ Test coverage (for core modules)
pytest --cov=src/codeindex --cov-report=term-missing
# Core modules: ≥90%, Overall: ≥80%
```

---

## 📝 Commit Guidelines

### Conventional Commits

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks
- `perf`: Performance improvement

**Examples**:

```bash
feat(parser): add Java generic type parsing

Implements parsing for Java generic types like <T extends Comparable<T>>.

Refs #42

---

fix(scanner): handle symlinks correctly

Previously failed on circular symlinks. Now detects and skips them.

Closes #123

---

docs(guides): update git-commit-guide.md

Added examples for multi-line commit messages.
```

### Reference Issues

- **Work in progress**: `Refs #N`
- **Completing work**: `Closes #N`

---

## 🐛 Reporting Bugs

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug.md).

Include:
- **Description**: What's broken?
- **Steps to reproduce**: How can we see the bug?
- **Expected behavior**: What should happen?
- **Environment**: codeindex version, Python version, OS

---

## 💡 Suggesting Features

Use the [Feature/Story template](.github/ISSUE_TEMPLATE/feature.md).

For major features (Epics):
- Create an Epic issue first
- Write an Epic plan in `docs/planning/`
- Break down into Stories

See [requirements-workflow.md](docs/development/requirements-workflow.md).

---

## 🔧 Code Style

### Python Style Guide

- Follow **PEP 8**
- Use **type hints** for function signatures
- Write **docstrings** (Google style)
- Max line length: **100 characters**
- Use **ruff** for linting

**Example**:

```python
from typing import Optional

def parse_file(file_path: str, language: str = "python") -> Optional[ParseResult]:
    """Parse a source code file and extract symbols.

    Args:
        file_path: Absolute path to the file to parse
        language: Programming language (default: "python")

    Returns:
        ParseResult with symbols, or None if parsing fails

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If language not supported
    """
    # Implementation here
    pass
```

### Testing Style

- **Descriptive test names**: `test_parse_java_generic_with_multiple_bounds`
- **Arrange-Act-Assert** pattern
- **One assertion per test** (when possible)
- **Use fixtures** for setup

**Example**:

```python
def test_parse_java_class_with_extends():
    """Test parsing Java class with extends keyword."""
    # Arrange
    code = "class Child extends Parent {}"

    # Act
    result = parse_java_code(code)

    # Assert
    assert len(result.inheritances) == 1
    assert result.inheritances[0].child == "Child"
    assert result.inheritances[0].parent == "Parent"
```

---

## 📖 Documentation

### When to Update Documentation

| Change | Update |
|--------|--------|
| New feature | README.md, CHANGELOG.md, relevant guide |
| Bug fix | CHANGELOG.md |
| Config change | docs/guides/configuration.md, CHANGELOG.md |
| API change | README.md, docstrings |
| New language | README.md, CHANGELOG.md |

### Docstring Style (Google Format)

```python
def complex_function(param1: str, param2: int = 10) -> dict:
    """One-line summary.

    Longer description if needed. Explain what the function does,
    not how it does it (that's what code is for).

    Args:
        param1: Description of first parameter
        param2: Description with default value (default: 10)

    Returns:
        Dictionary containing result data with keys:
        - 'status': Operation status
        - 'data': Processed data

    Raises:
        ValueError: If param1 is empty
        TypeError: If param2 is not an integer

    Example:
        >>> result = complex_function("test", 20)
        >>> result['status']
        'success'
    """
    pass
```

---

## 🔄 Pull Request Process

### 1. Prepare Your PR

```bash
# Ensure all tests pass
pytest -v

# Ensure code is clean
ruff check src/

# Update documentation if needed
vim README.md CHANGELOG.md

# Commit your changes
git add .
git commit -m "feat(scope): description

Closes #N"

# Push to your fork
git push origin feature/my-feature
```

### 2. Create Pull Request

Use the GitHub web interface or `gh` CLI:

```bash
gh pr create \
  --title "feat: My awesome feature" \
  --body "Closes #N

## Changes
- Added feature X
- Updated documentation

## Testing
- 25 new tests (95% coverage)
- All tests passing ✅"
```

### 3. PR Review Checklist

Your PR should:
- [ ] Have descriptive title and description
- [ ] Reference related issues (`Closes #N`)
- [ ] Include tests for new features
- [ ] Pass all CI checks
- [ ] Update documentation if needed
- [ ] Follow code style guidelines
- [ ] Have meaningful commit messages

### 4. After Review

- Address reviewer feedback promptly
- Push updates to the same branch
- Mark conversations as resolved
- Request re-review when ready

---

## 🌍 Adding Language Support

See the detailed guide in [CLAUDE.md](CLAUDE.md) Part 4.

**Quick steps**:
1. Add tree-sitter parser dependency
2. Implement symbol extraction
3. Write comprehensive tests (90-120 tests)
4. Update documentation
5. Add examples

**Languages priority**: See [ROADMAP.md](docs/planning/ROADMAP.md).

---

## 🤝 Getting Help

- **Documentation**: Start with [CLAUDE.md](CLAUDE.md)
- **Guides**: Check [docs/guides/](docs/guides/)
- **Questions**: Open a [Discussion](https://github.com/dreamlx/codeindex/discussions)
- **Bugs**: Create an [Issue](https://github.com/dreamlx/codeindex/issues)

---

## 📜 Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to providing a welcoming and inclusive environment.

---

## 🎓 Learning Resources

**For contributors new to**:
- **TDD**: [Test-Driven Development Guide](https://docs.python-guide.org/writing/tests/)
- **Git workflow**: [docs/guides/git-commit-guide.md](docs/guides/git-commit-guide.md)
- **Tree-sitter**: [Tree-sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
- **Conventional Commits**: [conventionalcommits.org](https://www.conventionalcommits.org/)

---

## 🏆 Recognition

Contributors are recognized in:
- CHANGELOG.md (for each release)
- GitHub contributors page
- Release notes for significant contributions

Thank you for making codeindex better! 🚀

---

**Questions?** Read [CLAUDE.md](CLAUDE.md) or open a discussion.

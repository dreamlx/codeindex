# Contributing to codeindex

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.9+
- pipx (recommended) or pip
- git

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/codeindex.git
cd codeindex

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Or create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Verify Installation

```bash
codeindex --version
pytest
```

## Development Workflow

We follow **Agile Development** with **TDD (Test-Driven Development)**:

### 1. Planning Phase
- Review [Roadmap](../planning/roadmap/2025-Q1.md)
- Pick an Epic/Feature/Story
- Create a task in `docs/planning/tasks/`

### 2. Design Phase
- Write tests first (TDD Red-Green-Refactor)
- Update/create ADR if architectural decision is needed

### 3. Development Phase

#### Create a Feature Branch

```bash
# Fetch latest
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name
```

#### Write Tests First (TDD)

```python
# tests/test_your_feature.py
def test_new_functionality():
    """Test description"""
    # Arrange
    input_data = ...

    # Act
    result = your_function(input_data)

    # Assert
    assert result == expected_output
```

Run tests (they should fail):
```bash
pytest tests/test_your_feature.py -v
```

#### Implement the Feature

Write the minimum code to pass the test:

```python
# src/codeindex/your_module.py
def your_function(input_data):
    """Implementation"""
    return result
```

#### Refactor

Improve code quality while keeping tests green:
```bash
pytest  # Ensure all tests pass
ruff check src/  # Lint
ruff format src/  # Format
```

### 4. Validation Phase

#### Run Full Test Suite

```bash
# All tests
pytest

# With coverage
pytest --cov=src/codeindex --cov-report=html

# Open coverage report
open htmlcov/index.html
```

Coverage requirements:
- Core modules: ≥ 90%
- Overall: ≥ 80%

#### Performance Testing

For performance-critical changes:
```bash
pytest tests/test_performance.py --benchmark
```

### 5. Submission Phase

#### Commit Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>(<scope>): <description>

# Examples:
git commit -m "feat(parser): add TypeScript support"
git commit -m "fix(cli): handle empty directories"
git commit -m "docs(readme): update installation steps"
git commit -m "test(scanner): add edge case tests"
git commit -m "refactor(writer): simplify prompt generation"
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding/updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance tasks

#### Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub:
- Title: Same as commit message
- Description: What, why, how
- Link to related issue/epic
- Screenshots if UI changes

#### PR Checklist

- [ ] Tests pass (`pytest`)
- [ ] Linting passes (`ruff check src/`)
- [ ] Coverage meets requirements
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commits follow conventional format

## Code Style

### Python Style

We use **Ruff** for linting and formatting:

```bash
# Check
ruff check src/

# Format
ruff format src/
```

### Type Hints

Use type hints for all public APIs:

```python
def parse_file(file_path: Path) -> ParseResult:
    """Parse a source file."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
    """
    ...
```

## Testing Guidelines

### Test Structure

```
tests/
├── test_scanner.py      # Unit tests for scanner
├── test_parser.py       # Unit tests for parser
├── test_cli.py          # CLI integration tests
├── test_integration.py  # End-to-end tests
└── fixtures/            # Test data
    └── sample_project/
```

### Test Naming

```python
def test_<what>_<when>_<expected>():
    """Test that <what> <expected> when <when>"""
```

Examples:
- `test_scanner_excludes_hidden_directories()`
- `test_parser_handles_syntax_errors_gracefully()`
- `test_cli_shows_help_when_no_arguments()`

### Fixtures

Use pytest fixtures for reusable test data:

```python
@pytest.fixture
def sample_python_file(tmp_path):
    """Create a sample Python file."""
    file_path = tmp_path / "sample.py"
    file_path.write_text("def hello(): pass")
    return file_path
```

## Adding New Languages

To add support for a new language:

1. **Add tree-sitter grammar**:
   ```toml
   # pyproject.toml
   dependencies = [
       "tree-sitter-python",
       "tree-sitter-typescript",  # Add this
   ]
   ```

2. **Create query file**:
   ```scheme
   ; src/codeindex/queries/typescript.scm
   (function_declaration
     name: (identifier) @function.name)
   ```

3. **Update parser**:
   ```python
   # src/codeindex/parser.py
   LANGUAGE_QUERIES = {
       'python': 'queries/python.scm',
       'typescript': 'queries/typescript.scm',  # Add this
   }
   ```

4. **Add tests**:
   ```python
   # tests/test_parser_typescript.py
   def test_parse_typescript_function():
       ...
   ```

5. **Update documentation**:
   - README.md
   - docs/guides/configuration.md
   - CHANGELOG.md

## Documentation

### When to Update Docs

- Adding new features → Update getting-started.md, configuration.md
- Changing behavior → Update relevant guides
- Architectural decisions → Create new ADR
- API changes → Update API docs (future)

### Documentation Structure

```
docs/
├── planning/          # Roadmap, epics, features
├── architecture/      # ADR, design docs
├── guides/           # User guides
├── development/      # Development docs
└── api/              # API reference (future)
```

## Release Process

1. **Update version**:
   ```bash
   # pyproject.toml
   version = "0.2.0"
   ```

2. **Update CHANGELOG.md**:
   ```markdown
   ## [0.2.0] - 2025-01-20
   ### Added
   - Feature X
   ```

3. **Create release commit**:
   ```bash
   git commit -m "chore: bump version to 0.2.0"
   ```

4. **Tag and push**:
   ```bash
   git tag v0.2.0
   git push origin develop --tags
   ```

5. **Merge to main** (via PR)

6. **Publish to PyPI**:
   ```bash
   python -m build
   twine upload dist/*
   ```

## Getting Help

- **Questions**: [GitHub Discussions](https://github.com/yourusername/codeindex/discussions)
- **Bugs**: [GitHub Issues](https://github.com/yourusername/codeindex/issues)
- **Chat**: [Discord](https://discord.gg/...) (future)

## Code of Conduct

Be respectful, inclusive, and collaborative. See [CODE_OF_CONDUCT.md](../../CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

# Development Setup

## Prerequisites

- Python 3.9+
- Git
- pip or pipx

## Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/codeindex.git
cd codeindex

# Create virtual environment
python -m venv .venv

# Activate (Unix/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

## Verify Installation

```bash
# Check CLI is available
codeindex --version

# Run tests
pytest

# Check linting
ruff check src/
```

## Project Structure

```
codeindex/
├── src/codeindex/       # Main package
│   ├── scanner.py       # Directory scanning
│   ├── parser.py        # Tree-sitter parsing
│   ├── writer.py        # Prompt generation & output
│   ├── invoker.py       # AI CLI execution
│   ├── cli.py           # Click CLI interface
│   └── queries/         # Tree-sitter query files
│       └── python.scm
├── tests/               # Test suite
│   ├── test_scanner.py
│   ├── test_parser.py
│   ├── test_cli.py
│   └── fixtures/        # Test data
├── docs/                # Documentation
├── examples/            # Example configs
├── pyproject.toml       # Package config
└── README.md
```

## Development Tools

### Ruff (Linting & Formatting)

```bash
# Check code
ruff check src/

# Format code
ruff format src/

# Fix auto-fixable issues
ruff check --fix src/
```

### Pytest (Testing)

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::test_parse_simple_function

# With coverage
pytest --cov=src/codeindex --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Type Checking (mypy)

```bash
# Future: type checking
mypy src/
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### 2. Make Changes (TDD)

Write test first:
```python
# tests/test_your_feature.py
def test_new_functionality():
    result = your_function(input_data)
    assert result == expected
```

Run test (should fail):
```bash
pytest tests/test_your_feature.py -v
```

Implement feature:
```python
# src/codeindex/your_module.py
def your_function(input_data):
    return result
```

Run test (should pass):
```bash
pytest tests/test_your_feature.py -v
```

### 3. Lint and Format

```bash
ruff check src/
ruff format src/
```

### 4. Run Full Test Suite

```bash
pytest
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `perf:` - Performance
- `chore:` - Maintenance

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

## Testing

### Running Tests

```bash
# All tests
pytest

# With verbose output
pytest -v

# Stop on first failure
pytest -x

# Run tests matching pattern
pytest -k "parser"

# Parallel execution
pytest -n auto
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=src/codeindex --cov-report=term-missing

# HTML report
pytest --cov=src/codeindex --cov-report=html
open htmlcov/index.html
```

### Writing Tests

Use pytest fixtures:
```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_python_file(tmp_path):
    """Create a sample Python file."""
    file_path = tmp_path / "sample.py"
    file_path.write_text("""
def hello():
    return "world"
    """)
    return file_path

def test_parse_function(sample_python_file):
    result = parse_file(sample_python_file)
    assert len(result.symbols) == 1
    assert result.symbols[0].name == "hello"
```

## Debugging

### Using pdb

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or Python 3.7+
breakpoint()
```

### Using pytest with pdb

```bash
# Drop into pdb on failure
pytest --pdb

# Drop into pdb on first failure
pytest -x --pdb
```

### Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## IDE Setup

### VS Code

Install extensions:
- Python
- Ruff
- Pytest

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true
    }
  }
}
```

### PyCharm

1. Mark `src/` as Sources Root
2. Enable pytest in Settings → Tools → Python Integrated Tools
3. Configure Ruff as external tool

## Environment Variables

```bash
# Set AI command for testing
export CODEINDEX_AI_COMMAND='echo "Mock AI response"'

# Disable AI for tests
export CODEINDEX_NO_AI=1

# Debug mode
export CODEINDEX_DEBUG=1
```

## Building Package

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Check package
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Documentation

### Building Docs (Future)

```bash
# Install doc dependencies
pip install -e ".[docs]"

# Build docs
cd docs
make html

# Open docs
open _build/html/index.html
```

## Troubleshooting

### "tree-sitter not found"

```bash
pip install --force-reinstall tree-sitter
```

### "pytest command not found"

```bash
# Ensure dev dependencies are installed
pip install -e ".[dev]"

# Or activate venv
source .venv/bin/activate
```

### "Import errors"

```bash
# Reinstall in development mode
pip install -e .
```

## Tips

1. **Always activate venv** before development
2. **Run tests before committing** - `pytest`
3. **Format before committing** - `ruff format src/`
4. **Write tests first** (TDD approach)
5. **Keep commits small and focused**
6. **Update CHANGELOG.md** for user-facing changes

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [tree-sitter documentation](https://tree-sitter.github.io/)
- [Click documentation](https://click.palletsprojects.com/)

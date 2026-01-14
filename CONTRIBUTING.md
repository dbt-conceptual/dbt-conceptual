# Contributing to dbt-conceptual

First off, thank you for considering contributing to dbt-conceptual! 🎉

## Code of Conduct

Be excellent to each other. Don't be an asshole. Ship good code.

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating a bug report, please check existing issues. When creating a bug report, include:

- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs what actually happened
- **Environment details**: Python version, dbt version, OS
- **Sample files** (model.yml, schema.yml) if relevant — sanitize any sensitive data

### 💡 Suggesting Features

Feature requests are welcome! Please:

- **Check existing issues** first
- **Describe the problem** you're trying to solve
- **Describe your proposed solution**
- **Consider alternatives** you've thought about

### 🔧 Pull Requests

1. **Fork the repo** and create your branch from `main`
2. **Install dev dependencies**: `pip install -e ".[dev]"`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Run the test suite**: `pytest`
6. **Run linting**: `ruff check . && black --check .`
7. **Update documentation** if needed
8. **Submit PR** with clear description

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/dbt-conceptual.git
cd dbt-conceptual

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=dbt_conceptual

# Run linting
ruff check .
black --check .

# Auto-fix linting issues
ruff check . --fix
black .
```

## Project Structure

```
dbt-conceptual/
├── src/dbt_conceptual/
│   ├── cli.py           # Click CLI commands
│   ├── config.py        # Configuration loading
│   ├── scanner.py       # dbt project scanner
│   ├── parser.py        # YAML parsing
│   ├── validator.py     # Validation logic
│   ├── state.py         # State model
│   ├── exporter/        # Export formats
│   └── viewer/          # Web viewer
├── tests/
│   ├── fixtures/        # Sample dbt projects
│   └── test_*.py        # Test files
└── docs/                # Documentation
```

## Testing Guidelines

- **Unit tests** for parsers, validators, state builders
- **Integration tests** with sample dbt projects in `tests/fixtures/`
- **Snapshot tests** for export formats
- Aim for **80%+ coverage** on new code

```python
# Example test
def test_concept_reference_validation():
    """meta.concept must reference existing concept."""
    model_yml = {...}
    schema_yml = {...}  # references non-existent concept
    
    errors = validate(model_yml, schema_yml)
    
    assert len(errors) == 1
    assert "does not exist" in errors[0].message
```

## Style Guide

- **Python**: Follow PEP 8, enforced by `ruff` and `black`
- **Commits**: Use conventional commits (`feat:`, `fix:`, `docs:`, etc.)
- **Documentation**: Update docstrings for public APIs

## Release Process

Maintainers handle releases. The process:

1. Update `CHANGELOG.md`
2. Bump version in `pyproject.toml`
3. Create GitHub release
4. CI publishes to PyPI

## Questions?

- Open a [Discussion](https://github.com/YOUR_USERNAME/dbt-conceptual/discussions)
- Tag maintainers in issues if stuck

---

Thank you for contributing! 🚀

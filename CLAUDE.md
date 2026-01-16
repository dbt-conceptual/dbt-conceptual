# Claude Code Guidelines for dbt-conceptual

## Pre-Commit Checklist

Before committing ANY code changes, ALWAYS run these checks locally:

```bash
# Run ALL checks in order - do not skip any
python3 -m pytest tests/ -q           # Tests must pass
python3 -m ruff check src/ tests/     # Linting must pass
python3 -m black --check src/ tests/  # Formatting must pass
python3 -m mypy src/                  # Type checking must pass
```

If ANY check fails:
1. Fix the issue
2. Re-run ALL checks
3. Only then commit

## Common CI/Local Drift Issues

### mypy Version Differences
- Local and CI may have different mypy versions with different behaviors
- `warn_unused_ignores = false` is set to avoid cross-version issues
- When adding `# type: ignore` comments, they may be needed locally but not in CI (or vice versa)

### Optional Dependencies
- `flask` and `PIL` are optional dependencies
- Both have `ignore_missing_imports = true` in pyproject.toml
- Don't assume they're installed when running type checks

### Python Version
- Code must support Python 3.9+
- Don't use Python 3.10+ syntax (like `match` statements or `|` union types outside of `from __future__ import annotations`)

## Project Structure

```
src/dbt_conceptual/
├── cli.py           # Click CLI commands
├── config.py        # Configuration (including ValidationConfig)
├── scanner.py       # dbt project scanner
├── parser.py        # YAML parsing & state building
├── validator.py     # Validation rules (configurable severities)
├── state.py         # State dataclasses (ConceptState, ProjectState, etc.)
├── server.py        # Flask web server (optional)
└── exporter/        # Export formats (mermaid, excalidraw, png, coverage, bus_matrix)
```

## Key Design Decisions

### Validation Configuration
- Validation rules are configured in `dbt_project.yml` under `vars.dbt_conceptual.validation`
- Severity options: `error`, `warn`, `ignore`
- Unknown refs (E002) are ALWAYS errors - not configurable
- See `ValidationConfig` in config.py

### State Management
- `ProjectState` is the single source of truth for the conceptual model
- `OrphanModel` tracks models not linked to concepts
- `ConceptState` includes both definition (markdown) and implementation tracking

### CLI Output Formats
- `--format human` (default): Rich terminal output
- `--format github`: GitHub Actions annotations (::error, ::warning, ::notice)

## Testing Guidelines

- Use `tempfile.TemporaryDirectory()` for tests that need file system
- Test configuration loading with and without `dbt_project.yml`
- Validator tests should cover both default and configured severities

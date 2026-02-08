# DBC-51: Config Refactor Handoff

**Agent**: Grunt
**Ticket**: DBC-51
**Branch**: `herd/grunt/DBC-51-config-refactor`

## What Changed

### Part A: Config Loading from dbt_project.yml

`Config.load()` now reads configuration from `dbt_project.yml` under `vars.dbt_conceptual`:

```yaml
# dbt_project.yml
vars:
  dbt_conceptual:
    scan:
      gold: ["models/marts/**/*.yml"]
    validation:
      orphan_models: warn
      unimplemented_concepts: warn
      missing_definitions: ignore
    validation_overrides:
      gold:
        orphan_models: error
```

**Precedence**: CLI flags > dbt_project.yml vars > legacy conceptual.yml config > defaults

**Legacy fallback**: If `vars.dbt_conceptual` is absent but `conceptual.yml` has a `config:` section, it loads from there with a `DeprecationWarning`.

### Part B: Schema Validation

- **Unknown keys**: Emit `UserWarning` (forward compatibility)
- **Invalid values**: Raise `ConfigError` with clear message listing valid options
- **Invalid rule names**: `ConfigError` listing valid rule names
- **Invalid severity values**: `ConfigError` listing valid severities
- **Invalid layer names** in `validation_overrides`: `ConfigError` listing valid layers

New public symbols exported from `config.py`:
- `ConfigError` exception class
- `_validate_config_schema()` function (used directly in tests)

### Part C: init Command Update

- `conceptual.yml` template is now clean (no `config:` section -- config lives in `dbt_project.yml`)
- `init` adds `vars.dbt_conceptual` block to `dbt_project.yml`, merging with existing vars
- `--force` flag allows overwriting existing `conceptual.yml`
- Never clobbers existing `vars.dbt_conceptual` in `dbt_project.yml`

### Other Changes

- Updated demo project (`demo.py`) to use new config format (`scan.gold` instead of `gold_paths`)
- Updated demo test (`test_demo.py`) to match new config keys

## Files Modified

| File | Change |
|------|--------|
| `src/dbt_conceptual/config.py` | Core refactor: new loading, schema validation, legacy fallback |
| `src/dbt_conceptual/cli.py` | Updated `init` command: --force flag, dual file scaffolding |
| `src/dbt_conceptual/demo.py` | Updated demo config to new format |
| `tests/test_config.py` | Complete rewrite: 37 tests covering all paths |
| `tests/test_cli.py` | Updated init tests + 4 new tests for init behavior |
| `tests/test_demo.py` | Updated assertion to match new config keys |

## Test Coverage

- Config defaults (no files, no vars, empty vars, dataclass defaults)
- Loading from dbt_project.yml vars (scan list, scan string, validation, overrides, empty block)
- Precedence: dbt_project.yml wins over legacy, CLI wins over dbt_project.yml
- Legacy fallback with DeprecationWarning
- Legacy without config section (no warning)
- Legacy with gold overrides, legacy scan string
- CLI overrides (over file, over defaults)
- Schema validation: 12 dedicated tests for unknown keys, invalid types, invalid values, invalid layers
- Schema validation integration: unknown key warns on load, invalid rule errors on load
- get_severity with and without layer overrides (4 tests)
- get_layer path matching (3 tests)
- Init: creates both files, --force overwrites, merges vars, skips existing dbt_conceptual

## Notes for Wardenstein

- The server tests emit expected DeprecationWarnings because their test fixtures use legacy config format
- No new dependencies added
- `ConfigError` is a new exception type; any code catching exceptions from `Config.load()` should be aware

## Checks

- pytest: 253 passed
- ruff: All checks passed
- black: All files formatted
- mypy: No issues found

# Configuration

All configuration options for dbt-conceptual.

---

## Configuration Location

Configuration lives in your `dbt_project.yml` under the `vars.dbt_conceptual` key:

```yaml
# dbt_project.yml
name: my_project
version: '1.0.0'

vars:
  dbt_conceptual:
    scan:
      gold:
        - models/marts/**/*.yml
    validation:
      orphan_models: warn
```

The conceptual model itself lives in `conceptual.yml` in your project root.

---

## Scan Configuration

### scan.gold

Which paths to scan for gold layer models. Supports glob patterns.

```yaml
vars:
  dbt_conceptual:
    scan:
      gold:
        - models/marts/**/*.yml     # default
```

You can specify multiple paths:

```yaml
vars:
  dbt_conceptual:
    scan:
      gold:
        - models/marts/**/*.yml
        - models/reporting/**/*.yml
```

Or a single path as a string:

```yaml
vars:
  dbt_conceptual:
    scan:
      gold: models/marts/**/*.yml
```

---

## Validation Settings

Control what gets validated and at what severity.

```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: warn              # Models without concept tags
      unimplemented_concepts: warn     # Concepts without implementing models
      missing_definitions: ignore      # Concepts without definitions
```

### Configurable Rules

| Rule | Default | What It Checks |
|------|---------|----------------|
| `orphan_models` | `warn` | Models in gold paths without `meta.concept` tags |
| `unimplemented_concepts` | `warn` | Concepts with no implementing models |
| `missing_definitions` | `ignore` | Non-stub concepts/relationships without definitions |

### Non-Configurable Rules

These are always active:

| Rule | Severity | What It Checks |
|------|----------|----------------|
| Unknown concept references (E002) | error | Relationships pointing to non-existent concepts |
| Unknown domain references (W001) | warning | Concepts referencing non-existent domains |

### Severity Levels

| Level | Behavior |
|-------|----------|
| `error` | Fails validation (exit code 1) |
| `warn` | Shows warning, passes validation |
| `ignore` | Not checked |

---

## Layer-Specific Validation Overrides

Override validation severities for the gold layer specifically:

```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: warn           # Default for all models
    validation_overrides:
      gold:
        orphan_models: error        # Stricter for gold layer
```

This lets you enforce strict coverage on gold while being lenient elsewhere.

---

## Server Settings

CLI options for `dbc serve`:

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `127.0.0.1` | Host to bind |
| `--port` | `8050` | Port to bind |
| `--demo` | false | Load sample data |

These are CLI arguments, not configuration file settings.

---

## Legacy Configuration

Configuration was previously supported in a `config` section within `conceptual.yml`. This is deprecated. If detected, the tool will issue a deprecation warning and recommend moving configuration to `dbt_project.yml`.

```yaml
# Deprecated format (in conceptual.yml):
config:
  scan:
    gold:
      - models/marts/**/*.yml
  validation:
    defaults:
      orphan_models: warn
    gold:
      orphan_models: error
```

Migrate to the `dbt_project.yml` format described above.

---

## Full Example

```yaml
# dbt_project.yml
name: my_analytics_project
version: '1.0.0'
config-version: 2

vars:
  dbt_conceptual:
    # Scan paths
    scan:
      gold:
        - models/marts/**/*.yml

    # Validation rules
    validation:
      orphan_models: warn
      unimplemented_concepts: warn
      missing_definitions: ignore

    # Layer-specific overrides
    validation_overrides:
      gold:
        orphan_models: error
```

---

## Defaults

If no configuration is provided, these defaults apply:

```yaml
vars:
  dbt_conceptual:
    scan:
      gold:
        - models/marts/**/*.yml
    validation:
      orphan_models: warn
      unimplemented_concepts: warn
      missing_definitions: ignore
```

The tool works out of the box with sensible defaults.

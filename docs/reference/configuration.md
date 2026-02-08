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
    conceptual_path: models/conceptual
    validation:
      orphan_models: warn
```

---

## Core Settings

### conceptual_path

Where the conceptual model lives.

```yaml
vars:
  dbt_conceptual:
    conceptual_path: models/conceptual  # default
```

The tool looks for `conceptual.yml` in this directory.

---

## Validation Settings

Control what gets validated and at what severity.

```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: warn              # Models without concept tags
      unimplemented_concepts: warn     # Concepts without implementing models
      missing_descriptions: ignore     # Concepts without descriptions
      invalid_references: error        # Relationships to undefined concepts
      invalid_domains: error           # Concepts referencing undefined domains
```

### Severity Levels

| Level | Behavior |
|-------|----------|
| `error` | Fails validation (exit code 1) |
| `warn` | Shows warning, passes validation |
| `ignore` | Not checked |

### Layer-Specific Validation

Different rules per layer:

```yaml
vars:
  dbt_conceptual:
    validation:
      gold:
        orphan_models: error      # Strict for gold
      silver:
        orphan_models: warn       # Lenient for silver
      bronze:
        orphan_models: ignore     # Don't check bronze
```

---

## Layer Configuration

### Custom Layer Definitions

Override default layer detection:

```yaml
vars:
  dbt_conceptual:
    layers:
      bronze:
        paths: ["models/staging", "models/raw"]
        prefixes: ["stg_", "raw_"]
      silver:
        paths: ["models/intermediate"]
        prefixes: ["int_", "prep_"]
      gold:
        paths: ["models/marts", "models/reporting"]
        prefixes: ["dim_", "fct_", "mart_", "rpt_"]
```

### Default Detection

If not configured, layers are detected by:

| Layer | Paths | Prefixes |
|-------|-------|----------|
| Gold | `marts`, `gold`, `reporting` | `dim_`, `fct_`, `mart_`, `rpt_` |
| Silver | `intermediate`, `silver`, `transform` | `int_`, `prep_`, `clean_` |
| Bronze | `staging`, `bronze`, `raw` | `stg_`, `raw_`, `src_` |

---

## Bus Matrix Configuration

### Explicit Fact/Dimension Lists

```yaml
vars:
  dbt_conceptual:
    bus_matrix:
      facts:
        - order
        - payment
        - return
      dimensions:
        - customer
        - product
        - date
        - store
```

### Pattern-Based Detection

```yaml
vars:
  dbt_conceptual:
    bus_matrix:
      fact_prefixes: ["fct_", "fact_"]
      dimension_prefixes: ["dim_", "dimension_"]
```

### Exclusions

```yaml
vars:
  dbt_conceptual:
    bus_matrix:
      exclude:
        - audit_log
        - system_config
```

---

## Governance Settings (Coming Soon)

```yaml
vars:
  dbt_conceptual:
    governance:
      require_steward: false
      require_maturity: false
      require_confidentiality: false
      enforce_taxonomy: false
      mention_stewards_on_change: true
```

See [Governance Features](../scaling-up/governance.md) for details.

---

## Server Settings

CLI options for `dbc serve`:

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `127.0.0.1` | Host to bind |
| `--port` | `8050` | Port to bind |
| `--demo` | false | Load sample data |

These aren't in `dbt_project.yml` — they're CLI arguments.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DBT_PROJECT_DIR` | Override project directory |
| `DCM_CONCEPTUAL_PATH` | Override conceptual path |

CLI flags take precedence over environment variables.

---

## Full Example

```yaml
# dbt_project.yml
name: my_analytics_project
version: '1.0.0'
config-version: 2

vars:
  dbt_conceptual:
    # Where the conceptual model lives
    conceptual_path: models/conceptual
    
    # Validation rules
    validation:
      orphan_models: warn
      unimplemented_concepts: warn
      missing_descriptions: ignore
      invalid_references: error
      
      # Layer-specific
      gold:
        orphan_models: error
      silver:
        orphan_models: warn
      bronze:
        orphan_models: ignore
    
    # Layer detection
    layers:
      gold:
        paths: ["models/marts"]
        prefixes: ["dim_", "fct_"]
      silver:
        paths: ["models/intermediate"]
        prefixes: ["int_"]
      bronze:
        paths: ["models/staging"]
        prefixes: ["stg_"]
    
    # Bus matrix
    bus_matrix:
      fact_prefixes: ["fct_"]
      dimension_prefixes: ["dim_"]
      exclude: ["util_date_spine"]
```

---

## Defaults

If no configuration is provided, these defaults apply:

```yaml
vars:
  dbt_conceptual:
    conceptual_path: models/conceptual
    validation:
      orphan_models: warn
      unimplemented_concepts: warn
      missing_descriptions: ignore
      invalid_references: error
      invalid_domains: error
```

The tool works out of the box with sensible defaults.

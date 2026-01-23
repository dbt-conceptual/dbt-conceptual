# Configuration

Configure dbt-conceptual in your `dbt_project.yml`.

## Configuration Location

Add settings under `vars.dbt_conceptual`:

```yaml
# dbt_project.yml
name: my_dbt_project
version: '1.0.0'

vars:
  dbt_conceptual:
    # settings go here
```

## Path Configuration

### conceptual_path

Location of the conceptual model YAML file.

```yaml
vars:
  dbt_conceptual:
    conceptual_path: models/conceptual  # default
```

The tool looks for `conceptual.yml` in this directory.

### silver_paths

Paths to silver layer models. Models here can use `meta.concept`.

```yaml
vars:
  dbt_conceptual:
    silver_paths:
      - models/staging      # default
      - models/silver       # default
      - models/intermediate
```

### gold_paths

Paths to gold layer models. Models here use `meta.concept` or `meta.realizes`.

```yaml
vars:
  dbt_conceptual:
    gold_paths:
      - models/marts   # default
      - models/gold    # default
      - models/presentation
```

## Validation Configuration

Configure validation rule severities under `validation`:

```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: warn           # default: warn
      unimplemented_concepts: warn  # default: warn
      unrealized_relationships: warn # default: warn
      missing_definitions: ignore   # default: ignore
      domain_mismatch: warn         # default: warn
```

### Severity Options

| Value | Behavior |
|-------|----------|
| `error` | Fails validation, exit code 1 |
| `warn` | Shows warning, passes validation |
| `ignore` | Suppressed, no output |

### Validation Rules

| Rule | Description |
|------|-------------|
| `orphan_models` | Models in silver/gold without concept tags |
| `unimplemented_concepts` | Concepts without implementing models |
| `unrealized_relationships` | N:M relationships without realization |
| `missing_definitions` | Concepts without definition text |
| `domain_mismatch` | Concepts with unknown domain references |

## Tag Validation

Enable tag drift detection:

```yaml
vars:
  dbt_conceptual:
    validation:
      tag_validation:
        enabled: true
        domains:
          allow_multiple: true    # Allow multiple domain tags
          format: standard        # "standard" or "databricks"
```

### Tag Formats

**Standard format** (default):
```yaml
models:
  - name: dim_customer
    config:
      tags:
        - "domain:party"
        - "owner:customer_team"
```

**Databricks Unity Catalog format**:
```yaml
models:
  - name: dim_customer
    config:
      databricks_tags:
        domain: party
        owner: customer_team
```

### Tag Validation Codes

| Code | Description |
|------|-------------|
| T001 | Missing domain tag |
| T002 | Wrong domain tag (doesn't match concept) |
| T003 | Multiple domain tags (when not allowed) |
| T004 | Missing owner tag |
| T005 | Wrong owner tag |

## Complete Example

```yaml
# dbt_project.yml
name: ecommerce_analytics
version: '1.0.0'

vars:
  dbt_conceptual:
    conceptual_path: models/conceptual

    silver_paths:
      - models/staging
      - models/intermediate

    gold_paths:
      - models/marts
      - models/reports

    validation:
      orphan_models: warn
      unimplemented_concepts: error  # strict
      unrealized_relationships: warn
      missing_definitions: warn
      domain_mismatch: error

      tag_validation:
        enabled: true
        domains:
          allow_multiple: false
          format: standard
```

## Default Values

If no configuration is provided:

| Setting | Default |
|---------|---------|
| `conceptual_path` | `models/conceptual` |
| `silver_paths` | `["models/staging", "models/silver"]` |
| `gold_paths` | `["models/marts", "models/gold"]` |
| All validation rules | `warn` (except `missing_definitions`: `ignore`) |
| `tag_validation.enabled` | `false` |

## Environment Variables

Currently, configuration is only supported via `dbt_project.yml`. Environment variable overrides are not supported.

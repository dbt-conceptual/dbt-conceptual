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

### bronze_paths

Paths to bronze/raw layer models. Models here are inferred via lineage.

```yaml
vars:
  dbt_conceptual:
    bronze_paths:
      - models/bronze   # default
      - models/raw
```

### silver_paths

Paths to silver layer models. Models here can use `meta.concept`.

```yaml
vars:
  dbt_conceptual:
    silver_paths:
      - models/silver       # default
      - models/staging
      - models/intermediate
```

### gold_paths

Paths to gold layer models. Models here use `meta.concept`.

```yaml
vars:
  dbt_conceptual:
    gold_paths:
      - models/gold    # default
      - models/marts
      - models/presentation
```

## Lineage Inference

Models are associated with concepts through two mechanisms:

1. **Explicit tagging**: Add `meta.concept: <concept_id>` to a model
2. **Lineage inference**: Models upstream/downstream of tagged models are automatically associated

When a model has `meta.concept`:
- **Upstream models** (bronze/silver) are inferred via refs
- **Downstream models** (gold) are inferred via dependents
- Inferred models appear with a lock icon in the UI

Explicit tags always take precedence over inference. If a downstream model has its own `meta.concept`, it belongs to that concept rather than being inferred.

```
hub_customer (silver, meta.concept: customer)  <- explicit
  |
  +-- stg_orders (bronze)                      <- inferred upstream
  +-- dim_customer (gold)                      <- inferred downstream
```

This enables flexible architectures:
- **Gold-centric**: Tag dims/facts, infer silver/bronze
- **Silver-centric**: Tag hubs/satellites (Data Vault), infer gold

### Multi-Concept Inference

A model can be inferred from multiple concepts when it's upstream or downstream of multiple tagged models:

```
stg_orders (bronze)                      <- inferred: customer, product
  |
  +-- hub_customer (silver, meta.concept: customer)
  +-- hub_product (silver, meta.concept: product)
  |
  +-- dim_customer_products (gold)       <- inferred: customer, product
```

This is intentional—shared staging or mart models naturally relate to multiple concepts. The UI shows all inferred concepts for such models.

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
| `unrealized_relationships` | Relationships not traced by any model |
| `missing_definitions` | Concepts without definition text |

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

    bronze_paths:
      - models/raw
      - models/landing

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
| `bronze_paths` | `["models/bronze", "models/raw"]` |
| `silver_paths` | `["models/silver"]` |
| `gold_paths` | `["models/gold"]` |
| All validation rules | `warn` (except `missing_definitions`: `ignore`) |
| `tag_validation.enabled` | `false` |

## Environment Variables

Currently, configuration is only supported via `dbt_project.yml`. Environment variable overrides are not supported.

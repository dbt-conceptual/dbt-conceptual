# Layers

dbt-conceptual focuses on the gold layer -- the business-facing models in your dbt project.

---

## The Medallion Pattern

Most dbt projects organize models into layers:

| Layer | Purpose | Typical Prefix |
|-------|---------|----------------|
| **Bronze** | Raw data, minimal transformation | `stg_`, `raw_` |
| **Silver** | Cleaned, conformed, business logic applied | `int_`, `prep_` |
| **Gold** | Business-ready, consumer-facing | `dim_`, `fct_`, `mart_` |

dbt-conceptual scans the gold layer for models and concept coverage. Bronze and silver layers are not scanned by default.

---

## Why Gold Layer Focus

Not all models need concept tags.

| Layer | Tag Priority | Why |
|-------|--------------|-----|
| Bronze | Low | These are raw sources, not business concepts |
| Silver | Medium | Intermediate transformations, rarely worth tagging |
| Gold | High | Business-facing, should map to concepts |

**The gold layer is where business vocabulary lives.** If a stakeholder asks "where's customer data?", they mean `dim_customer`, not `stg_salesforce__contacts`.

---

## Configuring Gold Layer Paths

By default, the tool scans `models/marts/**/*.yml` for gold layer models. You can customize this:

```yaml
# dbt_project.yml
vars:
  dbt_conceptual:
    scan:
      gold:
        - models/marts/**/*.yml
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

---

## Layer-Specific Validation

You can set stricter validation rules for the gold layer:

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

## Practical Guidance

| Situation | Recommendation |
|-----------|----------------|
| New project | Tag gold layer models first |
| Brownfield | Focus on gold, ignore bronze/silver |
| Strict governance | Enforce gold with `orphan_models: error` |
| Growing coverage | Expand scan paths as needed |

---

## Tagging Models Outside Gold

While the tool scans gold layer paths for orphan detection, you can tag models at any layer with `meta.concept`:

```yaml
# models/staging/schema.yml
models:
  - name: stg_salesforce__customers
    meta:
      concept: customer
```

These tags are recognized for coverage tracking even if the model isn't in a gold scan path. The difference is that orphan detection only applies to models within the configured gold paths.

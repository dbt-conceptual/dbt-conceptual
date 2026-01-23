# Layer Model

dbt-conceptual assumes a medallion architecture with Bronze, Silver, and Gold layers. This document explains how layers are detected and used.

## The Three Layers

### Bronze Layer

**Source data as-is.** Raw extracts, API responses, CDC streams. No transformation applied.

- **Detection**: Inferred from `manifest.json` lineage
- **Tagging**: Not required — automatically discovered
- **Visibility**: Read-only in the UI

Bronze models show which sources feed your concepts, helping trace data lineage back to origin.

### Silver Layer

**Cleaned and conformed.** Type casting, null handling, deduplication, business key generation.

- **Detection**: Path matches `silver_paths` configuration
- **Tagging**: `meta.concept` in model YAML
- **Visibility**: Editable in the UI

Silver models typically represent the first implementation of a concept — staging tables that prepare data for dimensional modeling.

### Gold Layer

**Business-ready.** Dimensions, facts, bridges. The models analysts query.

- **Detection**: Path matches `gold_paths` configuration
- **Tagging**: `meta.concept` (dimensions) or `meta.realizes` (facts/bridges)
- **Visibility**: Editable in the UI

Gold models are the primary implementation layer for your conceptual model.

## Configuration

Set layer paths in `dbt_project.yml`:

```yaml
vars:
  dbt_conceptual:
    silver_paths:
      - models/staging
      - models/silver
      - models/intermediate
    gold_paths:
      - models/marts
      - models/gold
      - models/presentation
```

## Model Type Detection

Within the Gold layer, model types are inferred from naming conventions:

| Prefix | Type |
|--------|------|
| `dim_` | Dimension |
| `fact_` | Fact |
| `bridge_` | Bridge |
| `ref_` | Reference |

## Coverage Tracking

The coverage report shows implementation status at each layer:

```
Domain: Party
├── customer
│   ├── Silver: stg_customer, stg_customer_address
│   └── Gold: dim_customer
└── employee
    ├── Silver: stg_employee
    └── Gold: (none) ← draft
```

A concept is `complete` when it has at least one implementing model. The layer breakdown shows depth of implementation.

## Relationship Realization

N:M relationships require explicit realization through fact or bridge tables:

```yaml
relationships:
  - name: contains
    from: order
    to: product
    cardinality: "N:M"

# Realized by:
models:
  - name: fact_order_lines
    meta:
      realizes:
        - order:contains:product
```

Without realization, N:M relationships remain in `draft` status.

## Best Practices

1. **Silver = one concept, one model** — Keep staging tables focused
2. **Gold = business questions** — Dimensions answer "what is X?", facts answer "what happened?"
3. **Don't tag Bronze** — Let lineage discovery handle source tracking
4. **Use meaningful prefixes** — `dim_`, `fact_`, `bridge_` make model intent clear

# Layers

dbt-conceptual understands the medallion architecture — bronze, silver, gold — and tracks coverage across layers.

---

## The Medallion Pattern

Most dbt projects organize models into layers:

| Layer | Purpose | Typical Prefix |
|-------|---------|----------------|
| **Bronze** | Raw data, minimal transformation | `stg_`, `raw_` |
| **Silver** | Cleaned, conformed, business logic applied | `int_`, `prep_` |
| **Gold** | Business-ready, consumer-facing | `dim_`, `fct_`, `mart_` |

dbt-conceptual uses this structure to focus attention where it matters most.

---

## Why Layers Matter for Conceptual Modeling

Not all models need concept tags.

| Layer | Tag Priority | Why |
|-------|--------------|-----|
| Bronze | Low | These are raw sources, not business concepts |
| Silver | Medium | Intermediate transformations, sometimes worth tagging |
| Gold | High | Business-facing, should map to concepts |

**The gold layer is where business vocabulary lives.** If a stakeholder asks "where's customer data?", they mean `dim_customer`, not `stg_salesforce__contacts`.

---

## Configuring Layers

dbt-conceptual auto-detects layers from folder paths and model prefixes, but you can configure them explicitly:

```yaml
# dbt_project.yml
vars:
  dbt_conceptual:
    layers:
      bronze:
        paths: ["models/staging"]
        prefixes: ["stg_", "raw_"]
      silver:
        paths: ["models/intermediate"]
        prefixes: ["int_", "prep_"]
      gold:
        paths: ["models/marts"]
        prefixes: ["dim_", "fct_", "mart_"]
```

---

## Layer-Aware Validation

You can set different validation rules per layer:

```yaml
vars:
  dbt_conceptual:
    validation:
      gold:
        orphan_models: error    # Gold models must be tagged
      silver:
        orphan_models: warn     # Silver models should be tagged
      bronze:
        orphan_models: ignore   # Bronze models don't need tags
```

This lets you enforce strict coverage on gold while being lenient on bronze.

---

## Coverage by Layer

The status command breaks down coverage by layer:

```bash
dbc status
```

```
Coverage Summary
────────────────────────────────────
Gold layer:    18/20 models   (90%)
Silver layer:  12/35 models   (34%)
Bronze layer:   0/50 models   (0%)

Overall:       30/105 models  (29%)
```

A project with 90% gold coverage and 0% bronze coverage is probably in good shape — the business-facing models are documented.

---

## Model Counts on Concept Cards

In the UI, concept cards show model counts per layer:

```
┌─────────────────────────────┐
│ Customer          complete  │
│ party                       │
├─────────────────────────────┤
│  🥉 3   🥈 2   🥇 1         │
│ bronze silver  gold         │
└─────────────────────────────┘
```

This tells you at a glance how a concept is implemented across layers.

---

## Practical Guidance

| Situation | Recommendation |
|-----------|----------------|
| New project | Tag gold first, expand to silver later |
| Brownfield | Focus on gold, ignore bronze |
| Data mesh | Each domain might have its own gold layer |
| Strict governance | Enforce gold, warn on silver |

---

## Layer Detection Logic

If you don't configure layers explicitly, dbt-conceptual uses these defaults:

**Gold (highest priority):**
- Paths containing `marts`, `gold`, `reporting`
- Prefixes: `dim_`, `fct_`, `mart_`, `rpt_`

**Silver:**
- Paths containing `intermediate`, `silver`, `transform`
- Prefixes: `int_`, `prep_`, `clean_`

**Bronze:**
- Paths containing `staging`, `bronze`, `raw`
- Prefixes: `stg_`, `raw_`, `src_`

Models that don't match any pattern are treated as silver by default.

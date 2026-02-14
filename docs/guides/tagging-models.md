# Tagging dbt Models

How to connect your dbt models to your conceptual model.

---

## The Concept Tag

The connection between a dbt model and a concept is a single tag:

```yaml
# models/marts/schema.yml
models:
  - name: dim_customer
    meta:
      concept: customer    # ← This links to the concept
```

That's it. This tag says: "This model implements the customer concept."

---

## Where to Add Tags

Tags go in your dbt schema YAML files, in the `meta` block:

```yaml
version: 2

models:
  - name: dim_customer
    description: "Customer dimension table"
    meta:
      concept: customer
    columns:
      - name: customer_key
        description: "Surrogate key"
```

You can add the tag to any model — staging, intermediate, or marts.

---

## Multiple Models, One Concept

A concept can have multiple implementing models:

```yaml
models:
  - name: stg_salesforce__customers
    meta:
      concept: customer    # Bronze/staging
      
  - name: int_customer_dedupe
    meta:
      concept: customer    # Silver/intermediate
      
  - name: dim_customer
    meta:
      concept: customer    # Gold/mart
```

This is normal — a concept represents a business entity, and that entity might appear at multiple layers of your transformation pipeline.

---

## What to Tag

### Tag: Business-Meaningful Models

| Model | Tag? | Why |
|-------|------|-----|
| `dim_customer` | ✅ | Core business dimension |
| `fct_orders` | ✅ | Core business fact |
| `mart_revenue` | ✅ | Business-facing mart |

### Skip: Utility Models

| Model | Tag? | Why |
|-------|------|-----|
| `util_date_spine` | ❌ | Technical utility, not a business concept |
| `int_dedupe_helper` | ❌ | Intermediate plumbing |
| `stg_raw__load_audit` | ❌ | System metadata |

### Judgment: Staging Models

Staging models are borderline. Tag them if:
- You want full lineage from source to mart
- The staging model represents a meaningful business entity

Skip them if:
- You're focused on gold-layer coverage first
- The staging model is pure transformation plumbing

---

## Concept Must Exist

The concept you reference must exist in `conceptual.yml`:

```yaml
# conceptual.yml
concepts:
  customer:
    name: "Customer"
    domain: party
```

If you tag a model with a concept that doesn't exist, run `dbc sync` to create a stub for it automatically.

### Creating Stubs Automatically

If you have models tagged with concepts that don't exist yet:

```bash
dbc sync
```

This creates stub entries in `conceptual.yml` for any orphan models automatically.

---

## Validating Tags

Check that all tags are valid:

```bash
dbc validate
```

This catches:
- Relationships referencing undefined concepts
- Models without tags (orphans, if configured to warn or error)
- Unknown domain references

---

## Orphan Detection

Find models without concept tags:

```bash
dbc orphans
```

```
Orphan models (no meta.concept tag):
  - mart_revenue_summary
  - dim_date
```

Not every orphan is a problem — utility models don't need tags. But orphans in your gold layer often indicate gaps.

---

## Tag via Properties File

If you prefer keeping tags separate from descriptions:

```yaml
# models/marts/_properties.yml
models:
  - name: dim_customer
    meta:
      concept: customer
      
  - name: fct_orders
    meta:
      concept: order
```

dbt merges properties from multiple files, so this works alongside your main schema.yml.

---

## Common Patterns

### Dimensional Model

```yaml
models:
  # Dimensions
  - name: dim_customer
    meta:
      concept: customer
      
  - name: dim_product
    meta:
      concept: product
      
  - name: dim_date
    meta:
      concept: date

  # Facts
  - name: fct_orders
    meta:
      concept: order
      
  - name: fct_payments
    meta:
      concept: payment
```

### One Big Table (OBT)

Even wide tables can be tagged:

```yaml
models:
  - name: obt_customer_360
    meta:
      concept: customer
      # This model combines customer with their orders, 
      # but the primary entity is customer
```

### Bridge Tables

Bridge tables that represent many-to-many relationships:

```yaml
models:
  - name: bridge_order_product
    meta:
      concept: order_line
      # The bridge represents the order_line concept
```

---

## Adding to Existing Projects

If you have many models without tags:

1. **Start with gold layer** — Tag your mart/dimension/fact models first
2. **Use sync** — `dbc sync` creates concepts for orphan models automatically
3. **Work backward** — Add silver layer tags later if desired

See [Adopting in Existing Projects](adoption.md) for a full guide.

---

## Checklist

When tagging models:

- [ ] Concept exists in `conceptual.yml`
- [ ] Concept name is spelled correctly
- [ ] Business-meaningful models are tagged
- [ ] Utility models are intentionally skipped
- [ ] `dbc validate` passes

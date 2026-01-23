# Tagging dbt Models

How to link your dbt models to conceptual model definitions.

## The Two Tags

### meta.concept

Use for dimension models — tables that implement a single concept.

```yaml
models:
  - name: dim_customer
    meta:
      concept: customer
```

### meta.realizes

Use for fact and bridge models — tables that implement relationships between concepts.

```yaml
models:
  - name: fact_orders
    meta:
      realizes:
        - customer:places:order
```

## Tag Placement

Tags go in your model's YAML file, typically `schema.yml` or a dedicated model YAML.

```yaml
# models/gold/schema.yml
version: 2

models:
  - name: dim_customer
    description: "Customer dimension"
    meta:
      concept: customer
    columns:
      - name: customer_key
        description: "Surrogate key"
```

## Dimensions

Dimensions implement a single concept. They answer "What is X?"

```yaml
# dim_customer implements the customer concept
- name: dim_customer
  meta:
    concept: customer

# dim_product implements the product concept
- name: dim_product
  meta:
    concept: product
```

One concept can have multiple implementing dimensions:

```yaml
# Both implement customer
- name: dim_customer
  meta:
    concept: customer

- name: dim_customer_snapshot
  meta:
    concept: customer
```

## Facts

Facts implement relationships. They answer "What happened?"

```yaml
# fact_orders implements the customer:places:order relationship
- name: fact_orders
  meta:
    realizes:
      - customer:places:order
```

Facts often implement multiple relationships:

```yaml
# fact_order_lines implements multiple relationships
- name: fact_order_lines
  meta:
    realizes:
      - customer:places:order
      - order:contains:product
```

## Bridge Tables

N:M relationships typically require bridge tables:

```yaml
# Relationship definition
relationships:
  - name: contains
    from: order
    to: product
    cardinality: "N:M"

# Bridge table realization
models:
  - name: bridge_order_product
    meta:
      realizes:
        - order:contains:product
```

## Silver Layer

Silver models can also be tagged:

```yaml
# models/silver/schema.yml
models:
  - name: stg_customers
    meta:
      concept: customer

  - name: stg_orders
    meta:
      concept: order
```

This shows which concepts have staging implementations.

## Relationship Reference Format

The `realizes` tag uses the format: `from_concept:verb:to_concept`

```yaml
customer:places:order      # customer places order
order:contains:product     # order contains product
employee:manages:employee  # employee manages employee (self-referential)
```

The reference must match a defined relationship in your conceptual model.

## Validation

After tagging, validate your model:

```bash
dcm validate
```

Common issues:
- **Unknown concept reference** — Concept doesn't exist in conceptual.yml
- **Unknown relationship reference** — Relationship doesn't exist
- **Orphan model** — Model in silver/gold path without tags

## Best Practices

1. **Tag early** — Add meta tags when creating new models
2. **One concept per dimension** — Keep dimensions focused
3. **Multiple realizes are OK** — Facts often join many concepts
4. **Use stubs for discovery** — `dcm sync --create-stubs` finds untagged models

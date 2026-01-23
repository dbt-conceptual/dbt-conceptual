# Quick Start

This guide walks you through creating your first conceptual model in an existing dbt project.

## 1. Initialize

Navigate to your dbt project root and run:

```bash
dcm init
```

This creates `models/conceptual/conceptual.yml` with a starter template.

## 2. Define Concepts

Edit `models/conceptual/conceptual.yml`:

```yaml
version: 1

domains:
  party:
    name: "Party"
  transaction:
    name: "Transaction"

concepts:
  customer:
    name: "Customer"
    domain: party
    owner: customer_team
    definition: "A person or company that purchases products"

  order:
    name: "Order"
    domain: transaction
    owner: orders_team
    definition: "A confirmed purchase by a customer"

relationships:
  - name: places
    from: customer
    to: order
    cardinality: "1:N"
```

## 3. Tag dbt Models

Add `meta.concept` to your existing dbt models:

```yaml
# models/gold/dim_customer.yml
models:
  - name: dim_customer
    meta:
      concept: customer
```

For facts that join multiple concepts:

```yaml
# models/gold/fact_orders.yml
models:
  - name: fact_orders
    meta:
      realizes:
        - customer:places:order
```

## 4. Check Status

```bash
dcm status
```

See which concepts are implemented, which are drafts, and which are stubs.

## 5. Validate

```bash
dcm validate
```

Check for broken references, missing definitions, and other issues.

## 6. Explore the UI

```bash
dcm serve
```

Open your browser to visualize and edit your conceptual model interactively.

## Next Steps

- [How It Works](../concepts/how-it-works.md) — Understand the underlying model
- [Defining Concepts](../guides/defining-concepts.md) — Best practices for concept definitions
- [CI/CD Integration](../guides/ci-integration.md) — Add validation to your pipeline

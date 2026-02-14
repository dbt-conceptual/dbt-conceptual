# Quick Start

Get from zero to a working conceptual model in 5 minutes.

---

## 1. Install

```bash
pip install dbt-conceptual
```

---

## 2. Initialize

In your dbt project root:

```bash
dbc init
```

This creates `conceptual.yml` in your project root:

```yaml
domains: {}

concepts: {}

relationships: []
```

---

## 3. Add a Domain and Concept

Edit `conceptual.yml`:

```yaml
domains:
  party:
    display_name: "Party"
    owner: data-team

concepts:
  customer:
    name: "Customer"
    domain: party
    definition: |
      A person or company that purchases products.

relationships: []
```

---

## 4. Tag a dbt Model

In your dbt schema file (e.g., `models/marts/schema.yml`):

```yaml
models:
  - name: dim_customer
    meta:
      concept: customer
```

---

## 5. Sync and Check Status

```bash
dbc sync
dbc status
```

```
Concepts: 1 total
  - 1 complete ✓

Coverage: 100%
```

---

## 6. Launch the UI

```bash
dbc serve
```

Open `http://localhost:8050` to see your conceptual model.

---

## What's Next?

- [Tutorial](tutorial.md) — Build a complete e-commerce model step by step
- [Defining Concepts](../guides/defining-concepts.md) — Write better concept definitions
- [CI/CD Integration](../guides/ci-cd.md) — Validate in your pipeline

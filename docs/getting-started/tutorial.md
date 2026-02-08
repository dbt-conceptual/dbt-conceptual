# Tutorial: Your First Conceptual Model

Let's build a conceptual model for an e-commerce domain. This takes about 15 minutes and covers the core workflow: defining concepts, creating relationships, tagging dbt models, and checking coverage.

<figure>
  <img src="../assets/workflow-greenfield-top-down.svg" alt="Greenfield top-down workflow" />
</figure>

## What We're Building

A simple e-commerce domain with these concepts:

```
customer ──places──→ order ──contains──→ order_line ──references──→ product
                       │
                       └──paid_by──→ payment
```

By the end, you'll have:
- A `conceptual.yml` with 5 concepts and 4 relationships
- dbt models tagged with `meta.concept`
- A coverage report showing what's implemented

---

## Before You Start

You'll need:
- A dbt project (or create one with `dbt init`)
- dbt-conceptual installed: `pip install dbt-conceptual`

---

## Step 1: Initialize

In your dbt project root, run:

```bash
dbc init
```

This creates `models/conceptual/conceptual.yml` with a starter template:

```yaml
version: 1

domains: {}

concepts: {}

relationships: []
```

Think of this file as your shared vocabulary — it will grow as you add concepts.

---

## Step 2: Define Domains

Domains help organize related concepts. Let's add two:

```yaml
version: 1

domains:
  party:
    name: "Party"
    owner: commercial-analytics
    
  transaction:
    name: "Transaction"
    owner: orders-team

concepts: {}

relationships: []
```

**Party** covers people and organizations — customers, suppliers, employees.  
**Transaction** covers business events — orders, payments, shipments.

These groupings help when your model grows larger.

---

## Step 3: Add Your First Concept

Let's start with Customer:

```yaml
concepts:
  customer:
    name: "Customer"
    domain: party
    owner: commercial-analytics
    description: |
      A person or company that purchases products.
      
      Includes both B2C and B2B customers. 
      Internal test accounts are excluded.
```

You can check your progress anytime:

```bash
dbc status
```

```
Concepts: 1 total
  - 0 complete (no implementing models yet)
  - 1 draft

Domains:
  party: 1 concept (0 complete)
  transaction: 0 concepts
```

The concept shows as "draft" because there's no dbt model linked to it yet. That's expected — we'll add those links in a later step.

---

## Step 4: Add More Concepts

Let's fill out the rest of our domain:

```yaml
concepts:
  customer:
    name: "Customer"
    domain: party
    owner: commercial-analytics
    description: |
      A person or company that purchases products.

  order:
    name: "Order"
    domain: transaction
    owner: orders-team
    description: |
      A confirmed purchase by a customer.
      
      Created when payment is authorized. Draft carts 
      and abandoned checkouts are not orders.

  order_line:
    name: "Order Line"
    domain: transaction
    owner: orders-team
    description: |
      A line item within an order, linking to a specific product.
      
      Captures quantity, unit price, and discounts applied.

  product:
    name: "Product"
    domain: transaction
    owner: catalog-team
    description: |
      An item available for purchase.
      
      Products have SKUs. Variants (size, color) are 
      separate product records.

  payment:
    name: "Payment"
    domain: transaction
    owner: finance-team
    description: |
      A payment transaction against an order.
      
      An order may have multiple payments (split tender).
```

Notice how each description answers "what is this?" in business terms, not technical terms. That's intentional — these descriptions should make sense to someone who doesn't know SQL.

---

## Step 5: Define Relationships

Now let's connect the concepts:

```yaml
relationships:
  - name: places
    from: customer
    to: order
    cardinality: "1:N"
    description: "A customer places one or more orders"

  - name: contains
    from: order
    to: order_line
    cardinality: "1:N"
    description: "An order contains one or more line items"

  - name: references
    from: order_line
    to: product
    cardinality: "N:1"
    description: "Each line item references a product"

  - name: paid_by
    from: order
    to: payment
    cardinality: "1:N"
    description: "An order is paid by one or more payments"
```

A tip on naming: use verbs that read naturally. "customer places order" flows better than "customer order relationship."

---

## Step 6: See It Visually

Launch the web UI to see your model:

```bash
dbc serve
```

Open `http://localhost:8050` in your browser. You'll see your concepts as nodes and relationships as edges.

You can drag concepts around to arrange them however makes sense. Positions are saved automatically.

---

## Step 7: Tag Your dbt Models

Now let's connect the conceptual model to your actual dbt implementation.

In your dbt model YAML files, add `meta.concept`:

```yaml
# models/marts/schema.yml
version: 2

models:
  - name: dim_customer
    description: "Customer dimension"
    meta:
      concept: customer
    columns:
      - name: customer_key
        description: "Surrogate key"
      - name: customer_id
        description: "Business key"

  - name: fct_orders
    description: "Order fact table"
    meta:
      concept: order

  - name: bridge_order_line
    description: "Order line items"
    meta:
      concept: order_line

  - name: dim_product
    description: "Product dimension"
    meta:
      concept: product

  - name: fct_payments
    description: "Payment transactions"
    meta:
      concept: payment
```

The `meta.concept` tag is the link between your conceptual vocabulary and your implementation.

---

## Step 8: Sync and Check Coverage

Sync your conceptual model with your dbt project:

```bash
dbc sync
```

```
Scanning dbt project...
Found 5 models with meta.concept tags
Mapped:
  - dim_customer → customer
  - fct_orders → order
  - bridge_order_line → order_line
  - dim_product → product
  - fct_payments → payment
```

Now check coverage:

```bash
dbc status
```

```
Concepts: 5 total
  - 5 complete ✓

Coverage: 100%

Domains:
  party: 1/1 complete
  transaction: 4/4 complete
```

All concepts have implementing models.

---

## Step 9: Validate

Run validation to check for any issues:

```bash
dbc validate
```

```
✓ All concepts have implementing models
✓ All relationships are valid
✓ No orphan models in gold layer

Validation passed.
```

If there were problems — like a concept referenced by a model that doesn't exist — they'd show up here.

---

## Step 10: Add to CI

To catch drift automatically, add validation to your CI pipeline:

```yaml
# .github/workflows/ci.yml
- name: Validate conceptual model
  run: dbc validate

- name: Show coverage
  run: |
    echo "## Conceptual Model" >> $GITHUB_STEP_SUMMARY
    dbc export --type coverage --format markdown >> $GITHUB_STEP_SUMMARY
```

Now every PR shows conceptual model coverage. If someone adds a model without tagging it, or references a concept that doesn't exist, the CI run will flag it.

---

## The Complete File

Here's the full `conceptual.yml` for reference:

```yaml
version: 1

domains:
  party:
    name: "Party"
    owner: commercial-analytics
    
  transaction:
    name: "Transaction"
    owner: orders-team

concepts:
  customer:
    name: "Customer"
    domain: party
    owner: commercial-analytics
    description: |
      A person or company that purchases products.

  order:
    name: "Order"
    domain: transaction
    owner: orders-team
    description: |
      A confirmed purchase by a customer.

  order_line:
    name: "Order Line"
    domain: transaction
    owner: orders-team
    description: |
      A line item within an order, linking to a specific product.

  product:
    name: "Product"
    domain: transaction
    owner: catalog-team
    description: |
      An item available for purchase.

  payment:
    name: "Payment"
    domain: transaction
    owner: finance-team
    description: |
      A payment transaction against an order.

relationships:
  - name: places
    from: customer
    to: order
    cardinality: "1:N"
    description: "A customer places one or more orders"

  - name: contains
    from: order
    to: order_line
    cardinality: "1:N"
    description: "An order contains one or more line items"

  - name: references
    from: order_line
    to: product
    cardinality: "N:1"
    description: "Each line item references a product"

  - name: paid_by
    from: order
    to: payment
    cardinality: "1:N"
    description: "An order is paid by one or more payments"
```

---

## Where to Go Next

Now that you have the basics working:

- **Add more concepts** — warehouse, campaign, lead
- **Explore the UI** — Try the Coverage view and Bus Matrix
- **Adjust validation** — Enable stricter checks as your coverage improves
- **Read the guides** — [Defining Concepts](../guides/defining-concepts.md), [CI/CD Integration](../guides/ci-cd.md)

The model grows incrementally. Start small, see the value, expand from there.

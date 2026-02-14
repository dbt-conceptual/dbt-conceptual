# Defining Concepts

How to write good concept definitions that create shared understanding.

---

## The Basics

A concept definition lives in `conceptual.yml`:

```yaml
concepts:
  customer:
    name: "Customer"
    domain: party
    owner: commercial-analytics
    definition: |
      A person or company that purchases products.
      
      Includes both B2C and B2B customers.
      Internal test accounts are excluded.
```

That's the structure. The art is in writing definitions that actually help.

---

## Writing Good Definitions

### Answer "What Is This?"

A definition should answer: "If a business stakeholder asked what this is, what would I say?"

| Weak | Strong |
|------|--------|
| "Customer data" | "A person or company that purchases products" |
| "Order table" | "A confirmed purchase by a customer, created when payment is authorized" |
| "Product dimension" | "An item available for purchase, identified by SKU" |

### Include Boundaries

What's included? What's excluded? This prevents confusion later.

```yaml
customer:
  definition: |
    A person or company that purchases products.

    Includes:
    - B2C customers (individuals)
    - B2B customers (companies)

    Excludes:
    - Internal test accounts
    - Leads that never converted
    - Suppliers (see: supplier concept)
```

### Use Business Language

Write for someone who doesn't know SQL or dbt. Avoid:
- Table names
- Column names  
- Technical jargon
- Abbreviations (unless well-known in the business)

---

## Concept Naming

### Use Singular Nouns

| Good | Avoid |
|------|-------|
| `customer` | `customers` |
| `order` | `orders` |
| `product` | `products` |

### Use Business Terms

| Good | Avoid |
|------|-------|
| `customer` | `cust`, `cstmr` |
| `order` | `sales_transaction` |
| `product` | `sku_item` |

### Be Specific

| Generic | Specific |
|---------|----------|
| `transaction` | `order`, `payment`, `refund` |
| `entity` | `customer`, `supplier`, `employee` |
| `event` | `page_view`, `purchase`, `signup` |

---

## Using Domains

Every concept should belong to a domain:

```yaml
domains:
  party:
    display_name: "Party"
    owner: commercial-analytics

concepts:
  customer:
    domain: party      # ← Assign to domain
```

If you're not sure which domain, ask: "What business area owns this concept?"

Without a domain, a concept is considered a **stub** — incomplete and needing attention.

---

## Working with Stubs

When you run `dbc sync`, you get placeholder concepts for orphan models:

```yaml
concepts:
  mystery_concept:
    name: "mystery_concept"
    domain: null
    owner: null
```

These are starting points. Enrich them:

1. Set the `domain`
2. Set the `owner` (or let it inherit from domain)
3. Write a `definition`
4. Give it a proper `name`

Until a concept has a domain, it stays a stub.

---

## Concept Lifecycle

| Status | What to Do |
|--------|------------|
| **Stub** | Assign a domain, add definition |
| **Draft** | Tag models with `meta.concept` to implement it |
| **Complete** | Maintain, update definition if meaning changes |

---

## Relationships

After defining concepts, connect them with relationships:

```yaml
relationships:
  - verb: places
    from: customer
    to: order
    cardinality: "1:N"
    definition: "A customer places one or more orders"
```

See [Concepts & Relationships](../core-concepts/concepts-and-relationships.md) for details.

---

## Checklist

When defining a concept, verify:

- [ ] Name is a singular noun in business language
- [ ] Domain is assigned
- [ ] Definition answers "what is this?"
- [ ] Definition states what's included/excluded
- [ ] Owner is set (or inherited from domain)
- [ ] Relationships to other concepts are defined

---

## Examples

### Good Example

```yaml
concepts:
  order:
    name: "Order"
    domain: transaction
    owner: orders-team
    definition: |
      A confirmed purchase by a customer.
      
      Created when payment is authorized. Contains one or more 
      order lines, each referencing a product.
      
      Excludes:
      - Abandoned carts (see: cart)
      - Draft orders pending payment
      - Cancelled orders (status = cancelled, still an Order)
```

### Minimal But Sufficient

```yaml
concepts:
  payment:
    name: "Payment"
    domain: transaction
    definition: |
      A payment transaction against an order.
      An order may have multiple payments (split tender).
```

### Too Sparse

```yaml
concepts:
  payment:
    name: "Payment"
    domain: transaction
    # No definition — what's a payment? What's included/excluded?
```

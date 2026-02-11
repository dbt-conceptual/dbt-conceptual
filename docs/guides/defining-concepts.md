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
    description: |
      A person or company that purchases products.
      
      Includes both B2C and B2B customers.
      Internal test accounts are excluded.
```

That's the structure. The art is in writing descriptions that actually help.

---

## Writing Good Descriptions

### Answer "What Is This?"

A description should answer: "If a business stakeholder asked what this is, what would I say?"

| Weak | Strong |
|------|--------|
| "Customer data" | "A person or company that purchases products" |
| "Order table" | "A confirmed purchase by a customer, created when payment is authorized" |
| "Product dimension" | "An item available for purchase, identified by SKU" |

### Include Boundaries

What's included? What's excluded? This prevents confusion later.

```yaml
customer:
  description: |
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
    name: "Party"
    owner: commercial-analytics

concepts:
  customer:
    domain: party      # ← Assign to domain
```

If you're not sure which domain, ask: "What business area owns this concept?"

Without a domain, a concept is considered a **stub** — incomplete and needing attention.

---

## Using Meta

The `meta` block is for your own properties — integrations, references, custom fields:

```yaml
concepts:
  customer:
    name: "Customer"
    domain: party
    description: |
      A person or company that purchases products.
    meta:
      source_system: "salesforce"
      jira_epic: "DATA-1234"
      last_reviewed: "2025-01-15"
```

Use `meta` for anything that's useful to your team but not part of the core schema.

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
3. Write a `description`
4. Give it a proper `name`

Until a concept has a domain, it stays a stub.

---

## Concept Lifecycle

| Status | What to Do |
|--------|------------|
| **Stub** | Assign a domain, add description |
| **Draft** | Tag models with `meta.concept` to implement it |
| **Complete** | Maintain, update description if meaning changes |
| **Deprecated** | Set `replaced_by`, update relationships |

### Deprecating Concepts

When a concept is replaced:

```yaml
concepts:
  legacy_customer:
    name: "Customer (Legacy)"
    domain: party
    replaced_by: customer
    description: |
      Deprecated. Use 'customer' instead.
      
      This concept was used in the old CRM system.
```

The `replaced_by` field marks it deprecated and points to the replacement.

---

## Relationships

After defining concepts, connect them with relationships:

```yaml
relationships:
  - name: places
    from: customer
    to: order
    cardinality: "1:N"
    description: "A customer places one or more orders"
```

See [Concepts & Relationships](../core-concepts/concepts-and-relationships.md) for details.

---

## Checklist

When defining a concept, verify:

- [ ] Name is a singular noun in business language
- [ ] Domain is assigned
- [ ] Description answers "what is this?"
- [ ] Description states what's included/excluded
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
    description: |
      A confirmed purchase by a customer.
      
      Created when payment is authorized. Contains one or more 
      order lines, each referencing a product.
      
      Excludes:
      - Abandoned carts (see: cart)
      - Draft orders pending payment
      - Cancelled orders (status = cancelled, still an Order)
    meta:
      source_system: "shopify"
```

### Minimal But Sufficient

```yaml
concepts:
  payment:
    name: "Payment"
    domain: transaction
    description: |
      A payment transaction against an order.
      An order may have multiple payments (split tender).
```

### Too Sparse

```yaml
concepts:
  payment:
    name: "Payment"
    domain: transaction
    # No description — what's a payment? What's included/excluded?
```

# Domains

Domains group related concepts together. They're organizational buckets — a way to structure your conceptual model as it grows.

---

## What's a Domain?

A domain is a business area. Party. Transaction. Catalog. Marketing. Logistics.

```yaml
domains:
  party:
    display_name: "Party"
    owner: commercial-analytics
    
  transaction:
    display_name: "Transaction"
    owner: orders-team
    
  catalog:
    display_name: "Catalog"
    owner: catalog-team
```

Domains answer: **"What part of the business does this belong to?"**

### Why Domains Matter

| Without Domains | With Domains |
|-----------------|--------------|
| 50 concepts in a flat list | 50 concepts organized into 5 domains |
| "Who owns customer?" | "Party domain → commercial-analytics" |
| Everything looks the same | Visual grouping by color |
| Governance reviews everything | Governance reviews by domain |

---

## Assigning Concepts to Domains

Every concept should belong to a domain:

```yaml
concepts:
  customer:
    domain: party        # ← Assigned to party domain
    
  order:
    domain: transaction  # ← Assigned to transaction domain
    
  product:
    domain: catalog      # ← Assigned to catalog domain
```

If a concept doesn't have a domain, it's considered a **stub** — incomplete, needs attention.

---

## Inheritance

Domains provide defaults that concepts inherit:

```yaml
domains:
  party:
    owner: commercial-analytics  # Default owner

concepts:
  customer:
    domain: party
    # owner inherited: commercial-analytics
    
  lead:
    domain: party
    owner: marketing-team  # Override the default
```

This reduces repetition. Define the owner once at the domain level, override only where needed.

**What inherits from domain:**
- `owner` (if not specified on concept)

---

## Domain Fields

| Field | Required | Description |
|-------|----------|-------------|
| `display_name` | No | Human-readable name (falls back to domain key) |
| `owner` | No | Default owner for concepts in this domain |
| `color` | No | Hex color for UI visualization (e.g., `#4a9eff`) |

---

## Choosing Domains

There's no single right way to structure domains. Here are common patterns:

### By Business Function

```yaml
domains:
  sales:
    display_name: "Sales"
  marketing:
    display_name: "Marketing"
  finance:
    display_name: "Finance"
  operations:
    display_name: "Operations"
```

### By Data Mesh Domain

```yaml
domains:
  customer-360:
    display_name: "Customer 360"
  order-management:
    display_name: "Order Management"
  product-catalog:
    display_name: "Product Catalog"
```

### By Entity Type (Kimball-ish)

```yaml
domains:
  party:
    display_name: "Party"       # People and organizations
  transaction:
    display_name: "Transaction" # Business events
  reference:
    display_name: "Reference"   # Lookup data
```

### Practical Advice

| Guideline | Why |
|-----------|-----|
| Start with 3-5 domains | Easier to expand than consolidate |
| Align with team ownership | Makes governance natural |
| Use business language | Stakeholders should recognize the terms |
| Don't over-engineer | A flat list is fine for small projects |

---

## Domains in the UI

The canvas view uses domain colors to visually group concepts:

- Each domain gets a distinct color
- Concepts inherit their domain's color
- You can filter the canvas by domain
- Coverage reports break down by domain

---

## Multi-Domain Architecture

As your project grows, you might need more sophisticated domain structures:

- **Shared concepts** — Some concepts (like Customer) might be used across domains
- **Domain dependencies** — Marketing domain might depend on Party domain
- **Federated ownership** — Different teams own different domains

These patterns are covered in [Scaling Up → Multi-Domain Architecture](../scaling-up/multi-domain.md).

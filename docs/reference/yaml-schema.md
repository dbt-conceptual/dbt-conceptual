# YAML Schema

This is the reference for the `conceptual.yml` file format.

---

## Where It Lives

The `conceptual.yml` file lives in your dbt project root, alongside `dbt_project.yml`.

```
my_project/
├── dbt_project.yml
├── conceptual.yml        ← here
├── models/
│   └── ...
```

---

## Overall Structure

A conceptual model file has three sections:

```yaml
domains:
  # Groups of related concepts

concepts:
  # The business entities

relationships:
  # How concepts connect
```

All three sections are optional. You can start with just concepts and add domains and relationships as the model matures.

---

## Domains

Domains group related concepts together. They're useful for organizing larger models and tracking ownership.

```yaml
domains:
  party:
    display_name: "Party"
    owner: commercial-analytics
    color: "#3498db"

  transaction:
    display_name: "Transaction"
    owner: orders-team
    color: "#e67e22"
```

| Field | Required | Description |
|-------|----------|-------------|
| `display_name` | No | Human-readable name (falls back to domain key) |
| `owner` | No | Default owner for concepts in this domain |
| `color` | No | Hex color for the UI (e.g., `#3498db`) |

### Owner Inheritance

Concepts inherit `owner` from their domain if they don't specify their own. This reduces repetition -- define the owner once at the domain level, override only where needed.

---

## Concepts

Concepts are the core of your model -- the business entities you're describing.

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

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name |
| `domain` | No | Which domain this belongs to |
| `owner` | No | Team responsible (overrides domain owner if set) |
| `definition` | No | What this concept means, in business terms |
| `color` | No | Override the domain's color in the UI |

### Owner Inheritance

If a concept doesn't specify `owner`, it inherits from its domain:

```yaml
domains:
  party:
    display_name: "Party"
    owner: commercial-analytics    # Default

concepts:
  customer:
    domain: party                  # Inherits owner: commercial-analytics

  lead:
    domain: party
    owner: marketing-team          # Overrides to marketing-team
```

### Status

The tool calculates status automatically based on the concept's state:

| Status | When |
|--------|------|
| `stub` | No `domain` assigned |
| `draft` | Has `domain`, but no dbt models tagged with it |
| `complete` | Has `domain` and at least one tagged model |

Status is derived -- you never set it manually. A concept progresses from stub to draft to complete as you enrich it and tag models.

---

## Relationships

Relationships describe how concepts connect to each other.

```yaml
relationships:
  - verb: places
    from: customer
    to: order
    cardinality: "1:N"
    definition: "A customer places one or more orders"

  - verb: contains
    from: order
    to: order_line
    cardinality: "1:N"
    definition: "An order contains line items"

  - verb: references
    from: order_line
    to: product
    cardinality: "1:1"
    definition: "Each line item references a product"
```

| Field | Required | Description |
|-------|----------|-------------|
| `verb` | No | A verb describing the relationship (defaults to `relates_to`) |
| `from` | Yes | Source concept |
| `to` | Yes | Target concept |
| `cardinality` | No | `1:1` or `1:N` (defaults to `1:N`) |
| `definition` | No | What this relationship means |
| `owner` | No | Team responsible |

### Naming Tip

Use verbs that read naturally as sentences: "customer **places** order", "order **contains** order_line". This makes the model easier to understand at a glance.

### Relationship Identifiers

The tool generates identifiers automatically in the format `{from}:{verb}:{to}`:
- `customer:places:order`
- `order:contains:order_line`
- `order_line:references:product`

### Cardinality

| Value | Meaning |
|-------|---------|
| `1:1` | One-to-one |
| `1:N` | One-to-many |

Only `1:1` and `1:N` are supported. For many-to-many relationships, use a bridge concept with two `1:N` relationships. See the example below.

---

## Complete Example

Here's a full example using the e-commerce domain:

```yaml
domains:
  party:
    display_name: "Party"
    owner: commercial-analytics
    color: "#3498db"

  transaction:
    display_name: "Transaction"
    owner: orders-team
    color: "#e67e22"

  catalog:
    display_name: "Catalog"
    owner: catalog-team
    color: "#2ecc71"

  marketing:
    display_name: "Marketing"
    owner: marketing-team
    color: "#9b59b6"

concepts:
  customer:
    name: "Customer"
    domain: party
    definition: |
      A person or company that purchases products.

  order:
    name: "Order"
    domain: transaction
    definition: |
      A confirmed purchase by a customer.

  order_line:
    name: "Order Line"
    domain: transaction
    definition: |
      A line item within an order, linking to a product.

  product:
    name: "Product"
    domain: catalog
    definition: |
      An item available for purchase.

  payment:
    name: "Payment"
    domain: transaction
    owner: finance-team              # Overrides transaction domain owner
    definition: |
      A payment transaction against an order.

  warehouse:
    name: "Warehouse"
    domain: catalog
    owner: logistics-team            # Overrides catalog domain owner
    definition: |
      A physical location where products are stored.

  campaign:
    name: "Campaign"
    domain: marketing
    definition: |
      A marketing campaign targeting potential customers.

  lead:
    name: "Lead"
    domain: marketing
    definition: |
      A potential customer generated by marketing activities.

relationships:
  - verb: places
    from: customer
    to: order
    cardinality: "1:N"
    definition: "A customer places one or more orders"

  - verb: contains
    from: order
    to: order_line
    cardinality: "1:N"
    definition: "An order contains line items"

  - verb: references
    from: order_line
    to: product
    cardinality: "1:1"
    definition: "Each line item references a product"

  - verb: paid_by
    from: order
    to: payment
    cardinality: "1:N"
    definition: "An order is paid by one or more payments"

  - verb: stored_in
    from: product
    to: warehouse
    cardinality: "1:N"
    definition: "Products are stored in warehouses"

  - verb: generates
    from: campaign
    to: lead
    cardinality: "1:N"
    definition: "A campaign generates leads"

  - verb: converts_to
    from: lead
    to: customer
    cardinality: "1:N"
    definition: "Leads convert to customers"
```

---

## Many-to-Many Relationships

If you have a true many-to-many relationship (products can be in many warehouses, warehouses can have many products), model it with a bridge concept:

```yaml
concepts:
  inventory:
    name: "Inventory"
    domain: catalog
    definition: |
      Stock level of a product at a specific warehouse.

relationships:
  - verb: has_inventory
    from: product
    to: inventory
    cardinality: "1:N"

  - verb: located_at
    from: inventory
    to: warehouse
    cardinality: "1:N"
```

This makes the bridge visible as a real concept with its own meaning, rather than hiding it as just an implementation detail.

---

## Validation

The file is validated when loaded. Common issues:

| Error | What It Means |
|-------|---------------|
| `Unknown domain reference` | A concept references a domain that doesn't exist |
| `Unknown concept reference` | A relationship references a concept that doesn't exist |

Run validation anytime with:

```bash
dbc validate
```

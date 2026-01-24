# Defining Concepts

A guide to writing clear, useful concept definitions in your conceptual model.

## What Makes a Good Concept

### Clear Boundaries

A concept should answer: **"What is this thing?"** not **"How is it stored?"**

```yaml
# Good — describes business meaning
customer:
  name: "Customer"
  definition: "A person or company that purchases products from us"

# Avoid — describes implementation
customer:
  name: "Customer"
  definition: "Primary key is customer_id, stored in dim_customer table"
```

### Business Language

Use terms your business stakeholders would recognize. If they wouldn't use the word, consider whether it's the right concept name.

```yaml
# Good — business term
order:
  definition: "A confirmed purchase by a customer"

# Avoid — technical jargon
order:
  definition: "A transactional entity representing the order header record"
```

## Structure of a Concept

```yaml
concepts:
  customer:
    name: "Customer"           # Display name (required)
    domain: party              # Domain grouping (recommended)
    owner: customer_team       # Responsible team (recommended)
    definition: |              # Business definition (recommended)
      A person or company that purchases products.

      Includes both B2C and B2B customers. Internal test accounts
      are excluded.
```

### Required Fields

- **name**: Human-readable display name

### Recommended Fields

- **domain**: Groups related concepts, enables filtering
- **owner**: Team responsible for this concept's implementation
- **definition**: Markdown text explaining what the concept means

### Optional Fields

- **color**: Override the domain's default color in the UI
- **replaced_by**: Points to successor concept when deprecated

## Writing Definitions

### Include

- What the concept represents
- Key business rules that define scope
- Examples when helpful

### Exclude

- Implementation details (table names, column names)
- Technical jargon (unless domain-specific)
- Duplicate information already in other concepts

### Examples

```yaml
order:
  definition: |
    A confirmed purchase by a customer.

    An order is created when payment is authorized. Draft carts and
    abandoned checkouts are not orders. Returns create separate refund
    records, not modifications to the original order.

product:
  definition: |
    An item available for purchase in our catalog.

    Products have SKUs and can be physical goods or digital downloads.
    Product variants (size, color) are separate product records.
```

## Relationships

Relationships connect concepts with verbs that describe the connection.

```yaml
relationships:
  - name: places           # The verb
    from: customer         # Subject
    to: order             # Object
    cardinality: "1:N"    # How many
    definition: "A customer places one or more orders"
```

### Naming Convention

Use active verbs that read naturally: `customer places order`, `order contains product`.

### Cardinality Options

| Value | Meaning |
|-------|---------|
| `1:1` | Exactly one on each side |
| `1:N` | One-to-many |

### Many-to-Many Relationships

For many-to-many relationships, create a bridge concept:

```yaml
concepts:
  order_line:
    name: "Order Line"
    domain: transaction
    definition: "Line item linking orders to products"

relationships:
  - name: contains
    from: order
    to: order_line
    cardinality: "1:N"
  - name: includes
    from: order_line
    to: product
    cardinality: "1:1"
```

This surfaces the bridge as a first-class concept with its own definition and tagging.

## Domains

Domains group related concepts and provide defaults.

```yaml
domains:
  party:
    name: "Party"
    owner: party_team      # Default owner for concepts in this domain
    color: "#3498db"       # Color in UI visualizations
```

### When to Create a Domain

- Group of 3+ related concepts
- Distinct ownership boundary
- Logical separation in business thinking

Common domains: Party, Transaction, Catalog, Location, Time

## Status Progression

New concepts typically progress through states:

1. **stub** — Created from sync, needs domain
2. **draft** — Has domain, no implementing models yet
3. **complete** — Has domain and implementing models

Track status with `dcm status` to see which concepts need attention.

# Concepts & Relationships

The two building blocks of a conceptual model.

---

## Concepts

A concept is a business entity — something the organization talks about and cares about. Customer. Order. Product. Payment.

Concepts are not tables. They're not even models. They're vocabulary — the words you use when discussing your data with stakeholders.

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

A concept answers: **"What is this thing, in business terms?"**

### What Makes a Good Concept

| Good | Why |
|------|-----|
| Customer | Clear business meaning, stakeholders use this word |
| Order | Specific, well-understood event |
| Product | Concrete entity with attributes |

| Less Good | Why |
|------------|-----|
| stg_customers | Implementation detail, not business vocabulary |
| dim_customer_v2 | Version numbers are technical, not conceptual |
| fact_table_1 | Generic, meaningless to stakeholders |

### Concept Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name |
| `domain` | No | Which domain this belongs to |
| `owner` | No | Team responsible (inherits from domain if not set) |
| `definition` | No | What this concept means in business terms |
| `color` | No | Override the domain's color in the UI |

---

## Relationships

Relationships connect concepts. They describe how business entities relate to each other.

```yaml
relationships:
  - verb: places
    from: customer
    to: order
    cardinality: "1:N"
    definition: "A customer places one or more orders"
```

A relationship answers: **"How do these things connect?"**

### Naming Relationships

Use verbs that read as natural sentences:

| Relationship | Reads As |
|--------------|----------|
| customer **places** order | "A customer places an order" |
| order **contains** order_line | "An order contains order lines" |
| order_line **references** product | "An order line references a product" |
| campaign **generates** lead | "A campaign generates leads" |

Avoid generic names like "has" or "relates_to" — they don't convey meaning.

### Cardinality

| Value | Meaning | Example |
|-------|---------|---------|
| `1:1` | One-to-one | person **has** passport |
| `1:N` | One-to-many | customer **places** orders |

Only `1:1` and `1:N` are supported. For many-to-many, use a bridge concept (see below).

### Many-to-Many

For true many-to-many relationships, use a bridge concept:

```yaml
concepts:
  product:
    name: "Product"
    domain: catalog
    
  warehouse:
    name: "Warehouse"
    domain: logistics
    
  inventory:
    name: "Inventory"
    domain: logistics
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

The bridge concept (inventory) is visible and meaningful — it's not hidden as an implementation detail.

### Relationship Fields

| Field | Required | Description |
|-------|----------|-------------|
| `verb` | No | Verb describing the relationship (defaults to `relates_to`) |
| `from` | Yes | Source concept |
| `to` | Yes | Target concept |
| `cardinality` | No | `1:1` or `1:N` (defaults to `1:N`) |
| `definition` | No | What this relationship means |
| `owner` | No | Team responsible |

---

## How They Connect to dbt

Concepts and relationships live in `conceptual.yml`. They describe the business vocabulary.

dbt models live in your project. They implement that vocabulary.

The connection is the `meta.concept` tag:

```yaml
# In your dbt schema.yml
models:
  - name: dim_customer
    meta:
      concept: customer  # Links to the concept
```

This tag says: "This model implements the customer concept."

Multiple models can implement the same concept (staging, dimension, fact). The concept is the shared vocabulary; the models are implementations.

---

## Visualization

In the canvas view, concepts appear as nodes and relationships appear as edges:

<figure>
  <img src="../assets/ui-screenshot.svg" alt="Canvas showing concepts and relationships" />
</figure>

- Node color indicates domain
- Node border indicates status (complete, draft, stub)
- Edge labels show relationship name and cardinality

# YAML Schema

Complete reference for the `conceptual.yml` file format.

## File Location

Default: `models/conceptual/conceptual.yml`

Configurable via `dbt_project.yml`:
```yaml
vars:
  dbt_conceptual:
    conceptual_path: models/conceptual
```

## Top-Level Structure

```yaml
version: 1

metadata:
  # Optional metadata

domains:
  # Domain definitions

concepts:
  # Concept definitions

relationships:
  # Relationship definitions

groups:
  # Optional relationship groups
```

## Version

Required. Currently only version `1` is supported.

```yaml
version: 1
```

## Metadata

Optional key-value pairs for documentation.

```yaml
metadata:
  author: "Data Architecture Team"
  last_reviewed: "2024-01-15"
```

## Domains

Domains group related concepts.

```yaml
domains:
  party:
    name: "Party"           # Display name (required)
    owner: party_team       # Optional default owner
    color: "#3498db"        # Optional color (hex)

  transaction:
    name: "Transaction"
    owner: orders_team
```

### Domain Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name |
| `owner` | No | Default owner for concepts |
| `color` | No | Hex color code for UI |

## Concepts

Concepts represent business entities.

```yaml
concepts:
  customer:
    name: "Customer"        # Display name (required)
    domain: party           # Domain reference
    owner: customer_team    # Responsible team
    definition: |           # Markdown definition
      A person or company that purchases products.
    color: "#e74c3c"        # Override domain color
    replaced_by: new_customer  # Deprecation pointer
```

### Concept Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name |
| `domain` | No | Domain reference (key) |
| `owner` | No | Responsible team |
| `definition` | No | Markdown text |
| `color` | No | Override domain color |
| `replaced_by` | No | Successor concept (marks as deprecated) |

### Concept Status (Derived)

| Status | Condition |
|--------|-----------|
| `deprecated` | `replaced_by` is set |
| `stub` | No `domain` |
| `draft` | Has `domain`, no implementing models |
| `complete` | Has `domain` AND implementing models |

## Relationships

Relationships connect concepts with verbs.

```yaml
relationships:
  - name: places            # Verb (required)
    from: customer          # Source concept (required)
    to: order               # Target concept (required)
    cardinality: "1:N"      # Optional cardinality
    definition: "A customer places orders"
    domains:                # Optional domain list
      - transaction
    owner: orders_team
    custom_name: "Customer Orders"  # Override display name
```

### Relationship Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Verb describing the relationship |
| `from` | Yes | Source concept (key) |
| `to` | Yes | Target concept (key) |
| `cardinality` | No | `1:1` or `1:N` (use bridge concepts for many-to-many) |
| `definition` | No | Markdown text |
| `domains` | No | List of domain references |
| `owner` | No | Responsible team |
| `custom_name` | No | Override auto-generated name |

### Relationship Identifier

Auto-generated as `{from}:{name}:{to}`, e.g., `customer:places:order`.

### Relationship Status (Derived)

| Status | Condition |
|--------|-----------|
| `stub` | Missing `name` |
| `draft` | No `domains` |
| `complete` | Has `domains` |

## Groups

Optional groupings of relationships for UI organization.

```yaml
groups:
  order_flow:
    - customer:places:order
    - order:contains:product
  inventory:
    - product:stored_in:warehouse
```

## Complete Example

```yaml
version: 1

metadata:
  author: "Data Team"

domains:
  party:
    name: "Party"
    owner: party_team
    color: "#3498db"
  transaction:
    name: "Transaction"
    owner: orders_team
    color: "#e67e22"
  catalog:
    name: "Catalog"
    owner: catalog_team
    color: "#2ecc71"

concepts:
  customer:
    name: "Customer"
    domain: party
    owner: customer_team
    definition: |
      A person or company that purchases products.

  order:
    name: "Order"
    domain: transaction
    definition: |
      A confirmed purchase by a customer.

  product:
    name: "Product"
    domain: catalog
    definition: |
      An item available for purchase.

  order_line:
    name: "Order Line"
    domain: transaction
    definition: |
      A line item linking an order to a product.

relationships:
  - name: places
    from: customer
    to: order
    cardinality: "1:N"
    domains:
      - transaction

  - name: contains
    from: order
    to: order_line
    cardinality: "1:N"
    domains:
      - transaction

  - name: includes
    from: order_line
    to: product
    cardinality: "1:1"
    domains:
      - transaction
```

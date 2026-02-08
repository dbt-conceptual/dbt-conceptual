# YAML Schema

This is the reference for the `conceptual.yml` file format.

---

## Where It Lives

By default, dbt-conceptual looks for `models/conceptual/conceptual.yml` in your dbt project.

You can change this in `dbt_project.yml`:

```yaml
vars:
  dbt_conceptual:
    conceptual_path: models/conceptual
```

---

## Overall Structure

A conceptual model file looks like this:

```yaml
version: 1

meta:
  # Optional user-defined properties

domains:
  # Groups of related concepts

concepts:
  # The business entities

relationships:
  # How concepts connect
```

---

## Version

Currently only version `1` is supported.

```yaml
version: 1
```

---

## Meta (File-Level)

Optional key-value pairs for your own use — tracking authorship, review dates, links to external systems, etc.

```yaml
meta:
  author: "Data Architecture Team"
  last_reviewed: "2025-01-15"
  confluence_page: "https://wiki.example.com/data-model"
```

This follows the same pattern as dbt's `meta` block. These properties aren't used by the tool — they're for humans and external integrations.

---

## Domains

Domains group related concepts together. They're useful for organizing larger models and setting defaults.

```yaml
domains:
  party:
    name: "Party"
    owner: commercial-analytics
    color: "#3498db"
    meta:
      slack_channel: "#party-domain"

  transaction:
    name: "Transaction"
    owner: orders-team
    color: "#e67e22"
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name |
| `owner` | No | Default owner for concepts in this domain |
| `color` | No | Hex color for the UI (e.g., `#3498db`) |
| `meta` | No | User-defined properties |

### Inheritance

Concepts inherit `owner` from their domain if they don't specify their own. This reduces repetition — define the owner once at the domain level, override only where needed.

---

## Concepts

Concepts are the core of your model — the business entities you're describing.

```yaml
concepts:
  customer:
    name: "Customer"
    domain: party
    description: |
      A person or company that purchases products.
      
      Includes both B2C and B2B customers.
      Internal test accounts are excluded.
    meta:
      source_system: "salesforce"
      erwin_entity_id: "E-00142"
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name |
| `domain` | No | Which domain this belongs to |
| `owner` | No | Team responsible (overrides domain owner if set) |
| `description` | No | What this concept means, in business terms |
| `color` | No | Override the domain's color in the UI |
| `replaced_by` | No | If deprecated, which concept replaces it |
| `meta` | No | User-defined properties |

### Inheritance

If a concept doesn't specify `owner`, it inherits from its domain:

```yaml
domains:
  party:
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

<figure>
  <img src="../assets/concept-states.svg" alt="Concept states: complete, draft, stub, ghost" />
</figure>

| Status | When |
|--------|------|
| `deprecated` | `replaced_by` is set |
| `stub` | No `domain` assigned |
| `draft` | Has `domain`, but no dbt models tagged with it |
| `complete` | Has `domain` and at least one tagged model |

---

## Relationships

Relationships describe how concepts connect to each other.

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
    description: "An order contains line items"

  - name: references
    from: order_line
    to: product
    cardinality: "N:1"
    description: "Each line item references a product"
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | A verb describing the relationship |
| `from` | Yes | Source concept |
| `to` | Yes | Target concept |
| `cardinality` | No | `1:1`, `1:N`, or `N:1` |
| `description` | No | What this relationship means |
| `owner` | No | Team responsible |
| `meta` | No | User-defined properties |

### Naming Tip

Use verbs that read naturally as sentences: "customer **places** order", "order **contains** order_line". This makes the model easier to understand at a glance.

### Relationship Identifiers

The tool generates identifiers automatically in the format `{from}:{name}:{to}`:
- `customer:places:order`
- `order:contains:order_line`
- `order_line:references:product`

### Cardinality

| Value | Meaning |
|-------|---------|
| `1:1` | One-to-one |
| `1:N` | One-to-many |
| `N:1` | Many-to-one |

For many-to-many relationships, use a bridge concept with two relationships. See the example below.

---

## The Meta Block

The `meta` block is available at every level — file, domain, concept, and relationship. Use it for:

- **External references**: Links to ERwin entities, Confluence pages, Jira epics
- **Integration metadata**: Source system identifiers, API references
- **Team conventions**: Slack channels, on-call contacts, review cycles
- **Custom properties**: Anything specific to your organization

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
      erwin_entity_id: "E-00142"
      last_reviewed_by: "jane.smith"
      review_cycle: "quarterly"
```

The tool doesn't interpret these values — they're passed through to exports and available for your own automation.

---

## Governance Block (Coming Soon)

> **Note**: Governance features are in development. See [Governance Features](../scaling-up/governance.md) for details.

The `governance` block will provide a structured place for stewardship, maturity, and classification metadata:

```yaml
domains:
  party:
    name: "Party"
    owner: commercial-analytics
    governance:
      steward: "@data-governance-team"
      confidentiality: internal

concepts:
  customer:
    name: "Customer"
    domain: party
    governance:
      steward: "@sarah.chen@corp.com"   # Overrides domain steward
      maturity: high
      confidentiality: confidential      # Overrides domain confidentiality
      regulatory: [GDPR, CCPA]
```

Like `owner`, governance fields will inherit from domain to concept, with concept-level values taking precedence.

---

## Complete Example

Here's a full example using the e-commerce domain:

```yaml
version: 1

meta:
  author: "Data Team"
  last_reviewed: "2025-01-20"
  confluence: "https://wiki.example.com/ecommerce-model"

domains:
  party:
    name: "Party"
    owner: commercial-analytics
    color: "#3498db"
    meta:
      slack_channel: "#party-domain"
    
  transaction:
    name: "Transaction"
    owner: orders-team
    color: "#e67e22"
    
  catalog:
    name: "Catalog"
    owner: catalog-team
    color: "#2ecc71"
    
  marketing:
    name: "Marketing"
    owner: marketing-team
    color: "#9b59b6"

concepts:
  customer:
    name: "Customer"
    domain: party
    description: |
      A person or company that purchases products.
    meta:
      source_system: "salesforce"

  order:
    name: "Order"
    domain: transaction
    description: |
      A confirmed purchase by a customer.
    meta:
      source_system: "shopify"

  order_line:
    name: "Order Line"
    domain: transaction
    description: |
      A line item within an order, linking to a product.

  product:
    name: "Product"
    domain: catalog
    description: |
      An item available for purchase.
    meta:
      source_system: "pim"

  payment:
    name: "Payment"
    domain: transaction
    owner: finance-team              # Overrides transaction domain owner
    description: |
      A payment transaction against an order.
    meta:
      source_system: "stripe"

  warehouse:
    name: "Warehouse"
    domain: catalog
    owner: logistics-team            # Overrides catalog domain owner
    description: |
      A physical location where products are stored.

  campaign:
    name: "Campaign"
    domain: marketing
    description: |
      A marketing campaign targeting potential customers.
    meta:
      source_system: "hubspot"

  lead:
    name: "Lead"
    domain: marketing
    description: |
      A potential customer generated by marketing activities.
    meta:
      source_system: "hubspot"

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
    description: "An order contains line items"

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

  - name: stored_in
    from: product
    to: warehouse
    cardinality: "N:1"
    description: "Products are stored in warehouses"

  - name: generates
    from: campaign
    to: lead
    cardinality: "1:N"
    description: "A campaign generates leads"

  - name: converts_to
    from: lead
    to: customer
    cardinality: "N:1"
    description: "Leads convert to customers"
```

---

## Many-to-Many Relationships

If you have a true many-to-many relationship (products can be in many warehouses, warehouses can have many products), model it with a bridge concept:

```yaml
concepts:
  inventory:
    name: "Inventory"
    domain: catalog
    description: |
      Stock level of a product at a specific warehouse.

relationships:
  - name: has_inventory
    from: product
    to: inventory
    cardinality: "1:N"

  - name: located_at
    from: inventory
    to: warehouse
    cardinality: "N:1"
```

This makes the bridge visible as a real concept with its own meaning, rather than hiding it as just an implementation detail.

---

## Validation

The file is validated when loaded. Common issues:

| Error | What It Means |
|-------|---------------|
| `Unknown domain reference` | A concept references a domain that doesn't exist |
| `Unknown concept reference` | A relationship references a concept that doesn't exist |
| `Duplicate concept name` | Two concepts have the same key |
| `Duplicate relationship` | The same from/name/to combination appears twice |

Run validation anytime with:

```bash
dbc validate
```

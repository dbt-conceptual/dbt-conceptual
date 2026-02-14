# Multi-Domain Architecture

Patterns for organizing conceptual models as they grow.

---

## When You Need This

Single-domain projects are simple — everything belongs to one team, one owner.

Multi-domain becomes relevant when:
- Multiple teams own different parts of the data
- The conceptual model exceeds 30-40 concepts
- You need clear boundaries between business areas
- Different parts have different governance requirements

---

## Domain Design Patterns

### By Business Function

Organize around how the business operates:

```yaml
domains:
  sales:
    display_name: "Sales"
    owner: sales-analytics
    
  marketing:
    display_name: "Marketing"
    owner: marketing-analytics
    
  finance:
    display_name: "Finance"
    owner: finance-team
    
  operations:
    display_name: "Operations"
    owner: ops-team
```

**Works well for:** Traditional enterprise structures with clear departmental boundaries.

### By Data Product

Organize around data products or domains in a data mesh sense:

```yaml
domains:
  customer-360:
    display_name: "Customer 360"
    owner: customer-domain-team
    
  order-management:
    display_name: "Order Management"
    owner: orders-domain-team
    
  inventory:
    display_name: "Inventory"
    owner: supply-chain-team
```

**Works well for:** Data mesh architectures, product-oriented teams.

### By Entity Type

Organize around conceptual entity types:

```yaml
domains:
  party:
    display_name: "Party"           # People and organizations
    owner: mdm-team
    
  transaction:
    display_name: "Transaction"     # Business events
    owner: core-data-team
    
  reference:
    display_name: "Reference"       # Lookup/configuration data
    owner: core-data-team
    
  metric:
    display_name: "Metric"          # Calculated measures
    owner: analytics-team
```

**Works well for:** Dimensional modeling, Kimball-style architectures.

---

## Shared Concepts

Some concepts are used across multiple domains. Customer is the classic example — Sales, Marketing, and Finance all care about customers.

### Option 1: Single Owner

One domain owns the concept, others reference it:

```yaml
domains:
  party:
    display_name: "Party"
    owner: mdm-team     # Master data team owns shared concepts

concepts:
  customer:
    domain: party       # Owned by party domain
    owner: mdm-team     # Single owner
```

Other domains reference but don't own the concept.

### Option 2: Federated Ownership

Different aspects owned by different teams:

```yaml
concepts:
  customer:
    domain: party
    owner: mdm-team
    definition: |
      Core customer entity.

      Owned by MDM team for core attributes.
      Marketing owns segmentation attributes.
      Finance owns credit attributes.
```

This requires coordination but reflects reality in large organizations.

---

## Cross-Domain Relationships

Relationships can span domains:

```yaml
domains:
  party:
    display_name: "Party"
  transaction:
    display_name: "Transaction"

concepts:
  customer:
    domain: party
  order:
    domain: transaction

relationships:
  - verb: places
    from: customer        # party domain
    to: order             # transaction domain
    cardinality: "1:N"
```

This is normal and expected — business entities relate across boundaries.

---

## Domain Dependencies

Some domains depend on others:

```
party (foundational)
  ↑
transaction (depends on party for customer, supplier)
  ↑
reporting (depends on transaction for orders, payments)
```

Consider documenting these dependencies:

Cross-domain relationships in your `conceptual.yml` make these dependencies visible. Use the diagram export to visualize them:

```bash
dbc export --type diagram --format svg -o model.svg
```

---

## File Organization

For large models, consider splitting across files:

```
my_project/
├── conceptual.yml          # Single file for now
```

> **Note:** Multi-file support is a planned feature. Currently, everything lives in a single `conceptual.yml` in your project root.

---

## Governance by Domain

Different domains might have different governance requirements:

Different domains may need different levels of care. Use domain ownership to assign responsibility:

```yaml
domains:
  party:
    display_name: "Party"
    owner: privacy-team              # PII lives here, needs careful ownership

  reference:
    display_name: "Reference"
    owner: data-governance           # Less sensitive
```

See [Governance Features](governance.md) for the future direction of governance features.

---

## Scaling Tips

| Concepts | Recommendation |
|----------|----------------|
| < 20 | Single domain might be fine |
| 20-50 | 3-5 domains, clear ownership |
| 50-100 | Consider domain hierarchies |
| 100+ | Federated model, multiple files |

### Signs You Need More Structure

- Concept list is hard to navigate
- Unclear who owns what
- Multiple teams editing same concepts
- Governance can't review everything

### Signs You've Over-Engineered

- Domains with 2-3 concepts each
- Excessive cross-domain relationships
- Team confusion about where things belong
- More time organizing than documenting

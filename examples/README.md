# dbt-conceptual Examples

This directory contains example dbt projects demonstrating dbt-conceptual usage.

## sample-dbt-project

A minimal e-commerce example showing:

- **Conceptual model** with 4 concepts across 3 domains
- **dbt models** linked via `meta.concept`
- **Relationships** between concepts (including bridge pattern for many-to-many)

### Try it out

```bash
cd sample-dbt-project

# View status
dcm status

# Validate (for CI)
dcm validate
```

### Structure

```
sample-dbt-project/
├── dbt_project.yml
└── models/
    ├── conceptual/
    │   ├── conceptual.yml    # Conceptual model definition
    │   └── layout.yml        # Visual positions
    ├── silver/
    │   └── dim_customer_crm.yml
    └── gold/
        ├── dim_customer.yml
        ├── dim_product.yml
        └── fact_orders.yml
```

### Expected Output

**Status command:**
- Shows coverage for each concept (silver and gold models)
- Lists relationships between concepts
- Flags stub concepts needing enrichment

**Validate command:**
- Checks all concepts are properly implemented
- Verifies relationship endpoints exist
- Warns about unusual patterns (gold-only concepts)
- Returns exit code 0 for CI integration

# Coverage View

The coverage view shows implementation status across your conceptual model.

## Overview

![Coverage dashboard](../assets/coverage-dashboard.png)

The coverage view displays:
- Concepts grouped by domain
- Status badges for each concept
- Implementing models at each layer

## Reading the View

### Domain Groups

Concepts are organized under their assigned domains. Concepts without domains appear under "Unassigned."

### Status Badges

| Badge | Meaning |
|-------|---------|
| Complete | Has implementing models |
| Draft | Defined but not implemented |
| Stub | Needs domain assignment |
| Deprecated | Replaced by another concept |

### Model Lists

Expand a concept to see implementing models:

```
customer
├── Silver: stg_customer, stg_customer_address
├── Gold: dim_customer
└── Bronze: raw_crm_customers (inferred)
```

## Filtering

### By Status

Filter to show only:
- All concepts
- Complete only
- Drafts and stubs (work needed)

### By Domain

Select a domain to filter the list.

## Metrics

The header shows summary metrics:
- Total concepts
- Complete count
- Draft count
- Stub count

## Coverage Calculation

Coverage percentage = (Complete concepts / Total concepts) × 100

A concept is "complete" when it has at least one implementing model in silver or gold.

## Export

Export coverage data for external reporting:

```bash
# HTML report
dcm export --type coverage --format html -o coverage.html

# Markdown (for CI summaries)
dcm export --type coverage --format markdown

# JSON (for automation)
dcm export --type coverage --format json
```

## Tracking Progress

Use coverage view to track conceptual model maturity:

1. **Initial state** — Many stubs after `sync --create-stubs`
2. **Definition phase** — Stubs become drafts as you add domains
3. **Implementation** — Drafts become complete as models are tagged
4. **Maintenance** — Monitor for new stubs from ongoing development

## Tips

- Review coverage weekly to catch drift
- Set coverage targets for mature domains
- Use `--no-drafts` in CI for strict enforcement
- Export JSON for dashboard integration

# Coverage View

A dashboard showing how much of your conceptual model is implemented.

---

## Overview

The Coverage view shows at a glance:
- How many concepts have implementing models
- Coverage by domain
- Coverage in the gold layer
- Gaps that need attention

Access it by clicking **Coverage** in the tab bar, or run:

```bash
dbc status
```

---

## The Coverage Dashboard

### Summary Cards

At the top, you'll see high-level metrics:

| Metric | What It Shows |
|--------|---------------|
| **Total Coverage** | Percentage of concepts with implementing models |
| **Gold Coverage** | Percentage of gold-layer models with concept tags |
| **Concepts** | Total / Complete / Draft / Stub counts |
| **Orphans** | Models without concept tags |

### Domain Breakdown

A table showing coverage per domain:

| Domain | Concepts | Complete | Draft | Stub | Coverage |
|--------|----------|----------|-------|------|----------|
| party | 5 | 5 | 0 | 0 | 100% |
| transaction | 10 | 8 | 2 | 0 | 80% |
| catalog | 5 | 3 | 1 | 1 | 60% |

Click a domain row to see its concepts.

---

## Concept List

Below the summary, you'll see all concepts with their status:

| Concept | Domain | Status | Models |
|---------|--------|--------|--------|
| customer | party | ✅ complete | 3 |
| order | transaction | ✅ complete | 4 |
| refund | transaction | ⚪ draft | 0 |
| inventory | — | 🟡 stub | 0 |

Click a concept to see which models implement it.

---

## Orphan Models

The Orphans section lists models without `meta.concept` tags:

```
Orphan models (no meta.concept tag):
  • mart_revenue_summary
  • dim_date
```

These might indicate:
- Missing concept definitions
- Models that don't need concepts (utility models)
- Tags that were forgotten

---

## Filtering

### By Status

Show only:
- Complete concepts
- Incomplete concepts (draft + stub)
- Orphan models

### By Domain

Filter to a specific domain to focus your work.

---

## Export

Export coverage reports for sharing:

```bash
# Markdown (for GitHub, Slack, etc.)
dbc export --type coverage --format markdown

# HTML (standalone page)
dbc export --type coverage --format html -o report.html

# JSON (for automation)
dbc export --type coverage --format json
```

### Adding to CI

Include coverage in your GitHub Actions summary:

```yaml
- name: Coverage report
  run: |
    echo "## Conceptual Model Coverage" >> $GITHUB_STEP_SUMMARY
    dbc export --type coverage --format markdown >> $GITHUB_STEP_SUMMARY
```

---

## Interpreting Coverage

### What's "Good" Coverage?

| Layer | Target | Notes |
|-------|--------|-------|
| Gold | 80%+ | This is where business vocabulary lives |

### Red Flags

| Pattern | What It Might Mean |
|---------|-------------------|
| Gold < 50% | Core business concepts not documented |
| Many orphans in gold | New models being added without tags |
| Stubs piling up | Sync ran but nobody enriched the stubs |
| Domain at 0% | Entire business area undocumented |

### Good Signs

| Pattern | What It Indicates |
|---------|-------------------|
| Gold > 80% | Strong coverage of business vocabulary |
| Steady improvement | Team is adopting the practice |
| Few orphans | Tags being added as part of normal workflow |

---

## Tracking Over Time

Coverage should improve over time. If it's dropping, something's wrong — probably new models being added without concept tags.

Consider:
- Adding coverage checks to CI
- Setting a coverage threshold
- Reviewing coverage in sprint retrospectives

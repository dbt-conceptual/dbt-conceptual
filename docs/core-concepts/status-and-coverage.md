# Status & Coverage

Understanding what's complete, what's missing, and where to focus.

---

## Concept Status

Every concept has a status based on its completeness:

| Status | Meaning | Visual |
|--------|---------|--------|
| **Complete** | Has domain and implementing models | Solid border, green badge |
| **Draft** | Has domain, but no implementing models | Dashed border, gray badge |
| **Stub** | No domain assigned | Dashed orange border, warning badge |

### How Status Is Calculated

```
No domain?                 -> stub
Has domain, no models?     -> draft
Has domain and models?     -> complete
```

Status is derived -- you never set it manually. A concept progresses from stub to draft to complete as you enrich it and tag models.

---

## Coverage

Coverage measures how much of your conceptual model is implemented.

```bash
dbc status
```

```
Coverage Summary
------------------------------------
Concepts: 25 total
  - 20 complete
  - 3 draft
  - 2 stubs

Domains:
  party:       5/5 complete
  transaction: 8/10 complete (2 draft)
  catalog:     4/5 complete (1 stub)
  marketing:   3/5 complete
```

### What Gets Counted

**Concept coverage:** Percentage of concepts with at least one implementing model.

**Domain coverage:** Breakdown by domain.

---

## Orphan Models

An orphan model is a dbt model in the gold layer without a `meta.concept` tag.

```bash
dbc orphans
```

```
Orphan models (no meta.concept tag):
  - mart_revenue_summary
  - dim_date
```

Orphans aren't necessarily bad -- not every model needs a concept. But orphans in the gold layer often indicate gaps in your conceptual model.

---

## Validation

The validate command checks for issues:

```bash
dbc validate
```

See [Validation Codes](../reference/validation-codes.md) for the full list of codes and what they mean.

### Configurable Validation Rules

| Rule | Checks For |
|------|------------|
| `orphan_models` | Models without concept tags |
| `unimplemented_concepts` | Concepts without implementing models |
| `missing_definitions` | Concepts without definitions |

### Non-Configurable Rules

| Rule | Severity | Checks For |
|------|----------|------------|
| Unknown concept references (E002) | error | Relationships referencing undefined concepts |
| Unknown domain references (W001) | warning | Concepts referencing undefined domains |

### Configuring Severity

```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: error           # Fail CI
      unimplemented_concepts: warn   # Show warning
      missing_definitions: ignore    # Don't check
```

---

## Coverage Reports

Export coverage in various formats:

```bash
# Markdown (great for GitHub job summaries)
dbc export --type coverage --format markdown

# HTML (standalone report)
dbc export --type coverage --format html -o coverage.html

# JSON (for automation)
dbc export --type coverage --format json
```

### Markdown Output

```markdown
## Coverage Report

| Domain | Concepts | Complete | Draft | Coverage |
|--------|----------|----------|-------|----------|
| party | 5 | 5 | 0 | 100% |
| transaction | 10 | 8 | 2 | 80% |
| catalog | 5 | 4 | 1 | 80% |

**Overall: 85% coverage**
```

---

## Tracking Progress

Coverage improves over time. Track it in CI:

```yaml
# .github/workflows/ci.yml
- name: Coverage report
  run: |
    echo "## Conceptual Model Coverage" >> $GITHUB_STEP_SUMMARY
    dbc export --type coverage --format markdown >> $GITHUB_STEP_SUMMARY
```

This adds a coverage summary to every PR, making progress visible.

---

## Practical Targets

| Stage | Coverage Target | Focus |
|-------|-----------------|-------|
| Week 1 | Any | Get stubs created |
| Month 1 | 50% gold | Priority domains |
| Month 3 | 80% gold | All gold models |
| Ongoing | Maintain | Don't let it drift |

Don't aim for 100% immediately. 80% coverage that's maintained beats 100% coverage that decays.

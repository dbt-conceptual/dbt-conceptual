# Bus Matrix

A dimensional modeling view showing which dimensions participate in which facts.

---

## What's a Bus Matrix?

The bus matrix is a classic Kimball concept. It's a grid showing:
- **Rows:** Fact concepts (business events/transactions)
- **Columns:** Dimension concepts (descriptive entities)
- **Cells:** Which dimensions apply to which facts

```
              customer  product  date  store  campaign
              ────────  ───────  ────  ─────  ────────
fct_orders       ✓         ✓      ✓      ✓       
fct_returns      ✓         ✓      ✓      ✓       
fct_marketing    ✓                ✓             ✓
```

It's a powerful way to see:
- Shared dimensions across facts (conformance)
- Gaps where dimensions should apply but don't
- The overall shape of your dimensional model

---

## Accessing the Bus Matrix

Click **Bus Matrix** in the tab bar, or export directly:

```bash
dbc export --type bus-matrix --format html -o matrix.html
dbc export --type bus-matrix --format markdown
```

---

## How It's Built

dbt-conceptual infers the bus matrix from:

1. **Concept types** — Concepts prefixed with `dim_` or `fct_` (or configured patterns)
2. **Relationships** — Which dimensions connect to which facts
3. **dbt refs** — Which dimension models are referenced by fact models

### Automatic Detection

If your models follow naming conventions:

```yaml
models:
  - name: dim_customer    # Detected as dimension
  - name: dim_product     # Detected as dimension
  - name: fct_orders      # Detected as fact
```

Or configure explicitly:

```yaml
vars:
  dbt_conceptual:
    bus_matrix:
      fact_prefixes: ["fct_", "fact_"]
      dimension_prefixes: ["dim_", "dimension_"]
```

---

## Reading the Matrix

### Cell Values

| Symbol | Meaning |
|--------|---------|
| ✓ | Dimension applies to this fact |
| ○ | Dimension might apply (relationship exists but no ref) |
| — | Dimension doesn't apply |

### Conformance

A conformed dimension appears across multiple facts. In the matrix, look for columns with many checkmarks — those are your conformed dimensions.

```
              customer  date
              ────────  ────
fct_orders       ✓       ✓    ← customer and date are conformed
fct_returns      ✓       ✓    
fct_inventory            ✓    ← customer doesn't apply here
```

### Coverage Gaps

Look for:
- Facts with few dimensions (might be missing relationships)
- Dimensions that apply everywhere except one fact (conformance issue?)

---

## Export Formats

### Markdown

Great for documentation or PR summaries:

```bash
dbc export --type bus-matrix --format markdown >> $GITHUB_STEP_SUMMARY
```

### HTML

Standalone page with sortable columns:

```bash
dbc export --type bus-matrix --format html -o bus-matrix.html
```

### JSON

For automation or custom tooling:

```bash
dbc export --type bus-matrix --format json
```

---

## Configuration

### Specifying Fact/Dimension Concepts

If auto-detection doesn't work for your naming conventions:

```yaml
vars:
  dbt_conceptual:
    bus_matrix:
      facts:
        - order
        - return
        - marketing_event
      dimensions:
        - customer
        - product
        - date
        - store
        - campaign
```

### Excluding Concepts

Some concepts aren't facts or dimensions:

```yaml
vars:
  dbt_conceptual:
    bus_matrix:
      exclude:
        - audit_log
        - system_config
```

---

## Use Cases

### Architecture Review

The bus matrix reveals the shape of your dimensional model. Use it to:
- Verify conformed dimensions are truly conformed
- Identify missing relationships
- Spot facts that might be too isolated

### Stakeholder Communication

A bus matrix is readable by business users. It answers "what can I analyze together?" without technical details.

### Data Mesh Interop

If different teams own different facts, the bus matrix shows where they share dimensions — and where they might need to align.

---

## Limitations

The bus matrix assumes a dimensional modeling pattern. If your architecture is:
- Pure Data Vault → Bus matrix may not be meaningful
- Wide tables without clear fact/dimension split → Auto-detection won't work well
- Graph/document models → Not a good fit

For non-dimensional architectures, the canvas view and coverage reports are more useful.

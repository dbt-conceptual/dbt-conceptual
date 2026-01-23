# Bus Matrix

The bus matrix shows dimensional coverage in the Kimball style.

## Overview

![Bus matrix](../assets/bus-matrix.png)

The bus matrix displays:
- **Rows**: Fact tables
- **Columns**: Dimension concepts
- **Cells**: Check marks where dimensions participate in facts

## Reading the Matrix

### Row Headers

Each row represents a fact table — a model that `realizes` one or more relationships.

### Column Headers

Each column represents a dimension concept — concepts that have implementing `dim_` models.

### Check Marks

A check mark indicates the fact table joins to that dimension. This is derived from:
- The relationships the fact `realizes`
- The concepts those relationships connect

## Example

```
                  | Customer | Product | Time | Location |
------------------+----------+---------+------+----------|
fact_orders       |    ✓     |    ✓    |  ✓   |    ✓     |
fact_page_views   |    ✓     |         |  ✓   |          |
fact_inventory    |          |    ✓    |  ✓   |    ✓     |
```

This shows:
- `fact_orders` joins all four dimensions
- `fact_page_views` only joins Customer and Time
- `fact_inventory` doesn't include Customer

## Use Cases

### Conformance Check

Identify dimensions that should participate in more facts:
- If Customer should appear in inventory analysis, the empty cell reveals a gap

### Coverage Planning

See which dimensions are widely used vs. narrowly scoped:
- Heavily used dimensions (many checks) are conforming dimensions
- Single-fact dimensions may be degenerate or specialized

### Documentation

Export the matrix for data dictionaries and stakeholder communication.

## Export

```bash
# HTML (interactive)
dcm export --type bus-matrix --format html -o bus-matrix.html

# Markdown (documentation)
dcm export --type bus-matrix --format markdown

# JSON (automation)
dcm export --type bus-matrix --format json
```

## Relationship to Concepts

The bus matrix is derived from your conceptual model:

1. **Dimensions** come from concepts with `dim_` implementing models
2. **Facts** come from models with `meta.realizes` tags
3. **Intersections** come from the concepts connected by realized relationships

If a fact realizes `customer:places:order`, it gets check marks in both Customer and Order columns.

## Tips

- Use the bus matrix in design reviews
- Empty columns suggest underutilized dimensions
- Empty rows suggest facts without dimensional context
- Export HTML for interactive exploration in browsers

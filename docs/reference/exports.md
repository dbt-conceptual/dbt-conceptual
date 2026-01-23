# Export Formats

Reference for `dcm export` command output formats.

## Command Syntax

```bash
dcm export --type <type> --format <format> [-o <output-file>]
```

## Export Matrix

| Type | svg | html | markdown | json |
|------|-----|------|----------|------|
| diagram | Yes | — | — | — |
| coverage | — | Yes | Yes | Yes |
| bus-matrix | — | Yes | Yes | Yes |
| status | — | — | Yes | Yes |
| orphans | — | — | Yes | Yes |
| validation | — | — | Yes | Yes |
| diff | — | — | Yes | Yes |

## Export Types

### diagram

SVG visualization of the conceptual model.

```bash
dcm export --type diagram --format svg -o model.svg
```

Output: Self-contained SVG with embedded styles.

### coverage

Implementation coverage report.

```bash
# Interactive HTML
dcm export --type coverage --format html -o coverage.html

# Markdown table
dcm export --type coverage --format markdown

# Structured data
dcm export --type coverage --format json
```

**JSON structure:**
```json
{
  "summary": {
    "total_concepts": 12,
    "complete": 8,
    "draft": 3,
    "stub": 1,
    "coverage_percent": 66.7
  },
  "domains": [
    {
      "name": "party",
      "concepts": [
        {
          "name": "customer",
          "status": "complete",
          "silver_models": ["stg_customer"],
          "gold_models": ["dim_customer"]
        }
      ]
    }
  ]
}
```

### bus-matrix

Kimball-style dimensional coverage matrix.

```bash
dcm export --type bus-matrix --format html -o matrix.html
dcm export --type bus-matrix --format markdown
dcm export --type bus-matrix --format json
```

**Markdown output:**
```markdown
|              | Customer | Product | Time |
|--------------|----------|---------|------|
| fact_orders  |    X     |    X    |  X   |
| fact_returns |    X     |    X    |  X   |
```

### status

Summary status of the conceptual model.

```bash
dcm export --type status --format markdown
dcm export --type status --format json
```

**JSON structure:**
```json
{
  "concepts": {
    "total": 12,
    "complete": 8,
    "draft": 3,
    "stub": 1
  },
  "relationships": {
    "total": 8,
    "complete": 6,
    "draft": 2
  }
}
```

### orphans

Models without concept tags.

```bash
dcm export --type orphans --format markdown
dcm export --type orphans --format json
```

**JSON structure:**
```json
{
  "count": 3,
  "models": [
    {
      "name": "fct_page_views",
      "path": "models/marts/fct_page_views.sql",
      "layer": "gold"
    }
  ]
}
```

### validation

Validation results.

```bash
dcm export --type validation --format markdown
dcm export --type validation --format json
```

**JSON structure:**
```json
{
  "passed": false,
  "errors": 2,
  "warnings": 5,
  "info": 3,
  "issues": [
    {
      "severity": "error",
      "code": "E001",
      "message": "Concept 'refund' referenced but not defined",
      "context": {
        "relationship": "order:has:refund"
      }
    }
  ]
}
```

### diff

Changes compared to a base reference.

```bash
dcm export --type diff --format markdown --base main
dcm export --type diff --format json --base origin/main
```

**Options:**
- `--base <ref>`: Git reference to compare against (branch, tag, commit)

**JSON structure:**
```json
{
  "has_changes": true,
  "concepts": {
    "added": ["refund"],
    "removed": [],
    "modified": ["order"]
  },
  "relationships": {
    "added": ["order:has:refund"],
    "removed": [],
    "modified": []
  }
}
```

## Output Options

### File Output

Use `-o` or `--output` to write to a file:

```bash
dcm export --type coverage --format html -o coverage.html
```

### Stdout

Omit `-o` to write to stdout:

```bash
dcm export --type coverage --format markdown >> $GITHUB_STEP_SUMMARY
```

### Piping

JSON output works well with `jq`:

```bash
dcm export --type validation --format json | jq '.passed'
dcm export --type orphans --format json | jq '.count'
dcm export --type diff --format json --base main | jq '.has_changes'
```

## Common Recipes

### CI Job Summary

```bash
echo "## Conceptual Model Status" >> $GITHUB_STEP_SUMMARY
dcm export --type status --format markdown >> $GITHUB_STEP_SUMMARY
dcm export --type validation --format markdown >> $GITHUB_STEP_SUMMARY
```

### PR Diff Report

```bash
dcm export --type diff --format markdown --base origin/main >> $GITHUB_STEP_SUMMARY
```

### Coverage Dashboard

```bash
# Generate HTML for hosting
dcm export --type coverage --format html -o public/coverage.html
dcm export --type bus-matrix --format html -o public/bus-matrix.html
```

### Automation Checks

```bash
# Fail if validation errors
dcm export --type validation --format json | jq -e '.passed'

# Fail if orphan models exist
[ $(dcm export --type orphans --format json | jq '.count') -eq 0 ]

# Check for changes
dcm export --type diff --format json --base main | jq -e '.has_changes == false'
```

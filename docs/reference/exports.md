# Export Formats

All available export types and formats.

---

## Export Command

```bash
dbc export --type TYPE --format FORMAT [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--type` | What to export (required) |
| `--format` | Output format (required) |
| `-o, --output` | Write to file instead of stdout |
| `--no-drafts` | For validation: fail if incomplete |
| `--base REF` | For diff: git ref to compare against |

---

## Export Matrix

Not every format works with every type. Here's what's available:

| Type | svg | html | markdown | json |
|------|-----|------|----------|------|
| diagram | yes | -- | -- | -- |
| coverage | -- | yes | yes | yes |
| bus-matrix | -- | yes | yes | yes |
| status | -- | -- | yes | yes |
| orphans | -- | -- | yes | yes |
| validation | -- | -- | yes | yes |
| diff | -- | -- | yes | yes |

---

## Export Types

### coverage

Implementation coverage report.

```bash
dbc export --type coverage --format markdown
dbc export --type coverage --format html -o coverage.html
dbc export --type coverage --format json
```

**Formats:** `markdown`, `html`, `json`

**Contents:**
- Overall coverage percentage
- Coverage by domain
- Concept status breakdown

### status

Current status of the conceptual model.

```bash
dbc export --type status --format markdown
dbc export --type status --format json
```

**Formats:** `markdown`, `json`

**Contents:**
- Concept counts by status
- Domain summary

### orphans

Models without concept tags.

```bash
dbc export --type orphans --format markdown
dbc export --type orphans --format json
```

**Formats:** `markdown`, `json`

**Contents:**
- Orphan models
- Model paths

### validation

Validation results.

```bash
dbc export --type validation --format markdown
dbc export --type validation --format json
```

**Formats:** `markdown`, `json`

**Contents:**
- Errors and warnings
- Validation rule results

### diagram

Visual diagram of the conceptual model.

```bash
dbc export --type diagram --format svg -o model.svg
```

**Formats:** `svg`

**Contents:**
- Concepts as nodes
- Relationships as edges
- Domain coloring

### bus-matrix

Dimensional modeling bus matrix.

```bash
dbc export --type bus-matrix --format markdown
dbc export --type bus-matrix --format html -o matrix.html
dbc export --type bus-matrix --format json
```

**Formats:** `markdown`, `html`, `json`

**Contents:**
- Facts as rows
- Dimensions as columns
- Applicability indicators

### diff

Changes compared to a git reference.

```bash
dbc export --type diff --format markdown --base main
dbc export --type diff --format json --base HEAD~1
```

**Formats:** `markdown`, `json`

**Options:**
- `--base REF` -- Git reference to compare against (required for diff)

**Contents:**
- Added concepts
- Removed concepts
- Modified concepts
- Relationship changes

---

## Format Details

### markdown

Human-readable tables, suitable for:
- GitHub job summaries
- Slack messages
- Documentation

```bash
dbc export --type coverage --format markdown >> $GITHUB_STEP_SUMMARY
```

### html

Standalone HTML page with styling, suitable for:
- Sharing with stakeholders
- Embedding in wikis
- Archiving

```bash
dbc export --type coverage --format html -o report.html
```

### json

Machine-readable, suitable for:
- Automation scripts
- Catalog integrations
- Custom tooling

```bash
dbc export --type coverage --format json | jq '.coverage_percent'
```

### svg

Vector graphics for diagrams:

```bash
dbc export --type diagram --format svg -o model.svg
```

---

## Examples

### CI Job Summary

```yaml
- name: Report
  run: |
    echo "## Conceptual Model" >> $GITHUB_STEP_SUMMARY
    dbc export --type coverage --format markdown >> $GITHUB_STEP_SUMMARY
    echo "## Validation" >> $GITHUB_STEP_SUMMARY
    dbc export --type validation --format markdown >> $GITHUB_STEP_SUMMARY
```

### Coverage Badge

Extract coverage for a badge:

```bash
COVERAGE=$(dbc export --type coverage --format json | jq -r '.coverage_percent')
echo "Coverage: ${COVERAGE}%"
```

### Documentation

Generate diagram for docs:

```bash
dbc export --type diagram --format svg -o docs/assets/conceptual-model.svg
```

---

## Output to File

Use `-o` to write to a file instead of stdout:

```bash
dbc export --type coverage --format html -o coverage.html
dbc export --type diagram --format svg -o model.svg
```

Without `-o`, output goes to stdout (useful for piping).

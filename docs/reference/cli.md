# CLI Reference

This is the complete reference for the `dbt-conceptual` command-line interface.

---

## Global Options

```bash
dbt-conceptual [OPTIONS] COMMAND
```

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Show more detail (use `-vv` for debug output) |
| `-q, --quiet` | Show only errors |
| `--version` | Show version and exit |
| `--help` | Show help and exit |

You can also use `dbc` as a shorthand:

```bash
dbc status
dbc validate
dbc serve
```

---

## Commands

### init

Creates a starter `conceptual.yml` and adds configuration to `dbt_project.yml`.

```bash
dbc init [--project-dir PATH] [--force]
```

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project |
| `--force` | Overwrite existing conceptual.yml |

This creates `conceptual.yml` in your project root and adds a `vars.dbt_conceptual` block to `dbt_project.yml` with default settings.

---

### status

Shows coverage -- how many concepts have implementing models.

```bash
dbc status [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project |
| `--gold-paths TEXT` | Override gold layer paths (can repeat) |

---

### validate

Checks for issues in your conceptual model. Useful in CI.

```bash
dbc validate [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project |
| `--gold-paths TEXT` | Override gold layer paths |
| `--format FORMAT` | Output format: `human`, `github`, or `markdown` |
| `--no-drafts` | Fail if any concepts or relationships are incomplete |

Exit codes:
- `0` -- Everything looks good
- `1` -- There are validation errors

The `--no-drafts` flag is useful when you want to ensure everything is fully documented before merging. It treats stub and draft concepts as errors.

---

### sync

Discovers dbt models and creates stub concepts for orphans.

```bash
dbc sync [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project |
| `--model TEXT` | Sync only a specific model |

Sync always creates placeholder concepts for orphan models (models without `meta.concept` tags), giving you a starting point to enrich.

---

### orphans

Lists models that don't have `meta.concept` tags.

```bash
dbc orphans [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project |
| `--gold-paths TEXT` | Override gold layer paths |

---

### export

Exports reports in various formats.

```bash
dbc export --type TYPE --format FORMAT [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--type TYPE` | What to export (required) |
| `--format FORMAT` | Output format (required) |
| `-o, --output PATH` | Write to file instead of stdout |
| `--no-drafts` | For validation: fail if incomplete |
| `--base REF` | For diff: git ref to compare against |

**What you can export:**

| Type | Available Formats |
|------|-------------------|
| `diagram` | svg |
| `coverage` | html, markdown, json |
| `bus-matrix` | html, markdown, json |
| `status` | markdown, json |
| `orphans` | markdown, json |
| `validation` | markdown, json |
| `diff` | markdown, json |

Examples:

```bash
# Coverage as markdown (nice for CI job summaries)
dbc export --type coverage --format markdown

# Bus matrix as HTML
dbc export --type bus-matrix --format html -o matrix.html

# SVG diagram
dbc export --type diagram --format svg -o model.svg

# Diff against base branch
dbc export --type diff --format markdown --base main
```

---

### diff

Compares your conceptual model against a git reference.

```bash
dbc diff --base REF [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--base REF` | Git ref to compare against (required) |
| `--format FORMAT` | Output: `human`, `github`, `json`, or `markdown` |
| `--project-dir PATH` | Path to dbt project |

Examples:

```bash
# Compare against main branch
dbc diff --base main

# Markdown output for PR summaries
dbc diff --base origin/main --format markdown

# JSON for automation
dbc diff --base HEAD~1 --format json
```

---

### serve

Launches the web UI.

```bash
dbc serve [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project |
| `--host TEXT` | Host to bind to (default: `127.0.0.1`) |
| `--port INT` | Port to bind to (default: `8050`) |
| `--demo` | Launch with sample data (no project needed) |

The `--demo` flag is useful if you want to explore the UI without setting up a project first.

```bash
# Try it out
dbc serve --demo

# Normal usage
dbc serve

# Custom port
dbc serve --port 3000
```

---

## Exit Codes

| Command | Exit 0 | Exit 1 |
|---------|--------|--------|
| `validate` | No errors | Has errors |
| `validate --no-drafts` | All complete | Has drafts/stubs |
| `diff --format github` | No changes | Has changes |
| `diff` (other formats) | Always | -- |
| Other commands | Success | Error |

---

## Common Patterns

**CI validation:**
```bash
dbc validate --format markdown >> $GITHUB_STEP_SUMMARY
```

**Coverage in job summary:**
```bash
dbc export --type coverage --format markdown >> $GITHUB_STEP_SUMMARY
```

**PR diff:**
```bash
dbc diff --base origin/main --format markdown >> $GITHUB_STEP_SUMMARY
```

**Check for changes in automation:**
```bash
dbc diff --base main --format json | jq '.has_changes'
```

# dbt-conceptual - AI Assistant Guide

<!-- dbt-conceptual CLAUDE.md v2.0 -->

dbt-conceptual keeps conceptual data models synchronized with dbt implementations -- not as drifting documentation, but as operational artifacts that validate against your actual code. Define business entities and relationships in YAML, then the tool ensures your dbt models implement them correctly. The conceptual model becomes a living contract, not a forgotten diagram.

## Quick Reference

### File Locations
- **Conceptual model**: `conceptual.yml` (project root, alongside `dbt_project.yml`)
- **Configuration**: `dbt_project.yml` under `vars.dbt_conceptual`

### Key Commands
```bash
dbc status              # Show coverage and validation summary
dbc validate            # Run validation, exit 1 on errors
dbc orphans             # List models not linked to concepts
dbc sync                # Sync models and generate concept stubs for orphans
dbc serve               # Start web UI at http://localhost:8050
dbc diff --base main    # Show changes vs a git reference
dbc export --type TYPE --format FORMAT  # Export reports
```

---

## Working with dbt-conceptual (for AI Assistants)

When helping users:

1. **Conceptual model is source of truth** -- Changes start in `conceptual.yml`, then flow to model tags
2. **Validate after every change** -- Run `dbc validate` after any modification to conceptual.yml or model tags
3. **Status is derived, not set** -- Don't manually set status fields; they reflect actual state (has domain? has models?)
4. **One tag links everything** -- `meta.concept` is the only bridge between dbt models and concepts
5. **Gold layer focus** -- Only gold layer models are scanned for orphan detection
6. **Keys are identifiers** -- Concept keys must be valid YAML keys (lowercase, underscores, no spaces)
7. **No N:M relationships** -- Many-to-many requires a bridge concept (see Common Patterns)

### Workflow Direction

**Greenfield (new project)**: Define concepts first -> tag models -> validate

**Brownfield (existing project)**: `dbc sync` -> enrich stubs with domain/owner/definition -> validate

---

## YAML Schema Reference

### conceptual.yml Structure
```yaml
domains:
  <domain_key>:
    display_name: "Display Name"   # Optional (falls back to key)
    color: "#2196F3"               # Optional, hex color
    owner: team-name               # Optional

concepts:
  <concept_key>:
    name: "Display Name"           # Required
    domain: <domain_key>           # Required for non-stub status
    owner: team-name               # Optional (inherits from domain)
    definition: |                  # Optional
      Detailed business definition
    color: "#hex"                  # Optional, overrides domain color

relationships:
  - verb: places                   # Optional (defaults to "relates_to")
    from: <concept_key>            # Required
    to: <concept_key>              # Required
    cardinality: "1:N"             # Optional: 1:1 or 1:N (defaults to 1:N)
    definition: "Description"      # Optional
    owner: team-name               # Optional
```

### Concept Status (Derived Automatically)

Status is always derived from state -- it cannot be set manually:

| Status | Condition |
|--------|-----------|
| stub | No domain assigned |
| draft | Has domain, no implementing models |
| complete | Has domain AND implementing models |

### Tagging dbt Models

Link models to concepts using `meta.concept`:
```yaml
# models/marts/schema.yml
version: 2

models:
  - name: dim_customer
    meta:
      concept: customer    # Links to concepts.customer
```

That's it. One tag: `meta.concept`.

---

## Configuration (dbt_project.yml)
```yaml
name: your_project

vars:
  dbt_conceptual:
    # Scan paths for gold layer models
    scan:
      gold:
        - models/marts/**/*.yml    # Default

    # Validation rules (error | warn | ignore)
    validation:
      orphan_models: warn              # Models without concept tag
      unimplemented_concepts: warn     # Concepts with no models
      missing_definitions: ignore      # Concepts without definition

    # Layer-specific overrides
    validation_overrides:
      gold:
        orphan_models: error           # Stricter for gold layer
```

---

## CLI Commands

| Command | Purpose | Exit Codes |
|---------|---------|------------|
| `dbc init` | Create initial conceptual.yml | 0=success |
| `dbc status` | Show coverage summary | 0=success |
| `dbc validate` | Run validation checks | 0=pass, 1=errors |
| `dbc orphans` | List untagged models | 0=success |
| `dbc sync` | Sync project and create stubs for orphans | 0=success |
| `dbc export` | Export to various formats | 0=success |
| `dbc serve` | Start web UI | 0=success |
| `dbc diff` | Show changes vs a git ref | depends on format |

### Common Flags
- `-v, --verbose`: Increase verbosity (-vv for debug)
- `-q, --quiet`: Suppress non-error output
- `--format human|github|markdown`: Output format
- `--project-dir PATH`: Override project directory

---

## Validation Rules

### Errors (Always Active)

| Code | Description |
|------|-------------|
| E002 | Relationship references unknown concept '{concept}' |

### Warnings (Always Active)

| Code | Description |
|------|-------------|
| W001 | Concept references unknown domain '{domain}' |

### Configurable Rules

| Code | Rule Key | Default | Description |
|------|----------|---------|-------------|
| W101 | orphan_models | warn | Model is not linked to any concept |
| W102 | unimplemented_concepts | warn | Concept has no implementing models |
| W104 | missing_definitions | ignore | Concept/relationship missing definition |

### Informational

| Code | Description |
|------|-------------|
| I001 | Stub concept needs enrichment (missing domain, owner, definition) |
| I002 | Stub relationship needs enrichment |

### Strict Mode (--no-drafts)

| Code | Description |
|------|-------------|
| E201 | Incomplete concept (promoted from I001) |
| E202 | Incomplete relationship (promoted from I002) |

---

## Coverage

The tool scans gold layer paths (configurable via `scan.gold`) for models with `meta.concept` tags.

**Coverage** = concepts with implementing models / total concepts

---

## Common Patterns

### Adding a New Concept

1. Add to `conceptual.yml`:
```yaml
concepts:
  new_entity:
    name: "New Entity"
    domain: your_domain
    owner: your-team
    definition: |
      What this entity represents in business terms.
```

2. Tag implementing models:
```yaml
models:
  - name: dim_new_entity
    meta:
      concept: new_entity
```

3. Validate:
```bash
dbc validate
```

### Many-to-Many Relationships (Bridge Concepts)

Only 1:1 and 1:N cardinality are supported. Model many-to-many with a bridge concept:

```yaml
concepts:
  order:
    name: "Order"
    domain: transaction
  product:
    name: "Product"
    domain: catalog
  order_line:
    name: "Order Line"
    domain: transaction
    definition: |
      Line items linking orders to products.

relationships:
  - verb: contains
    from: order
    to: order_line
    cardinality: "1:N"
  - verb: includes
    from: order_line
    to: product
    cardinality: "1:1"
```

### Brownfield Adoption (Existing Project)
```bash
# 1. Generate stubs from existing orphan models
dbc sync

# 2. Check what needs enrichment
dbc status

# 3. Enrich priority concepts (add domain, owner, definition)

# 4. Enable CI warnings, then gradually enforce errors
```

### CI Integration
```yaml
# .github/workflows/pr.yml
- name: Validate conceptual model
  run: dbc validate --format github
```

---

## Export Types

| Type | Formats | Description |
|------|---------|-------------|
| diagram | svg | Visual conceptual model diagram |
| coverage | html, markdown, json | Implementation coverage report |
| bus-matrix | html, markdown, json | Dimensional bus matrix |
| status | markdown, json | Current status summary |
| orphans | markdown, json | Untagged models list |
| validation | markdown, json | Validation results |
| diff | markdown, json | Changes vs git ref |

---

## Web UI

Start with `dbc serve` (default: `http://localhost:8050`):

| View | Purpose |
|------|---------|
| Canvas | Visual entity-relationship diagram |
| Coverage | Implementation progress by domain |
| Bus Matrix | Concept x Model grid view |

---

## Key Constraints

1. **One tag**: Models link to concepts via `meta.concept` only
2. **Concept keys**: Must be valid YAML keys (lowercase, underscores, no spaces)
3. **Domain required**: Concepts need a domain to be "draft" or "complete"
4. **Unknown refs are errors**: Relationships referencing undefined concepts always fail (E002)
5. **Status is derived**: Never set status manually
6. **Only 1:1 and 1:N**: Use bridge concepts for many-to-many

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Model not linked to any concept" | Add `meta.concept: <key>` to model's schema.yml |
| "Concept has no implementing models" | Tag a model or accept as draft for now |
| "References unknown concept" | Check spelling of concept key in relationship |
| Coverage seems wrong | Check `scan.gold` paths in dbt_project.yml config |

---

## File Structure Example
```
my_project/
├── dbt_project.yml               # Configuration under vars.dbt_conceptual
├── conceptual.yml                 # Main conceptual model
├── models/
│   ├── staging/
│   │   └── schema.yml
│   └── marts/
│       └── schema.yml             # Models with meta.concept tags
```

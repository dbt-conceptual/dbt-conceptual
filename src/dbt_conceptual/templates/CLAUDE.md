# dbt-conceptual (DCM) - AI Assistant Guide

<!-- DCM CLAUDE.md v1.0 -->

dbt-conceptual (DCM) keeps conceptual data models synchronized with dbt implementations - not as drifting documentation, but as operational artifacts that validate against your actual code. Define business entities and relationships in YAML, then DCM ensures your dbt models implement them correctly. The conceptual model becomes a living contract, not a forgotten diagram.

## Quick Reference

### File Locations
- **Conceptual model**: `models/conceptual/conceptual.yml`
- **Canvas layout**: `models/conceptual/conceptual.layout.json`
- **Taxonomy** (optional): `models/conceptual/taxonomy.yml`
- **Configuration**: `dbt_project.yml` under `vars.dbt_conceptual`

### Key Commands
```bash
dcm status              # Show coverage and validation summary
dcm validate            # Run validation, exit 1 on errors
dcm orphans             # List models not linked to concepts
dcm sync --create-stubs # Generate concept stubs from model tags
dcm serve               # Start web UI at http://localhost:5050
```

---

## Working with DCM (for AI Assistants)

When helping users with DCM:

1. **Conceptual model is source of truth** - Changes start in `conceptual.yml`, then flow to model tags
2. **Validate after every change** - Run `dcm validate` after any modification to conceptual.yml or model tags
3. **Status is derived, not set** - Don't manually set status fields; they reflect actual state (has domain? has models?)
4. **One tag links everything** - `meta.concept` is the only bridge between dbt models and concepts
5. **Respect the layer model** - Bronze is ignored, Silver/Gold are where coverage matters
6. **Keys are identifiers** - Concept keys must be valid YAML keys (lowercase, underscores, no spaces)
7. **No N:M relationships** - Many-to-many requires a bridge concept (see Common Patterns)

### Workflow Direction

**Greenfield (new project)**: Define concepts first → tag models → validate

**Brownfield (existing project)**: `dcm sync --create-stubs` → enrich stubs with domain/owner/definition → validate

---

## YAML Schema Reference

### conceptual.yml Structure
```yaml
version: 1

metadata:
  name: "Project Name"           # Optional project title

domains:
  <domain_key>:
    name: "Display Name"         # Required
    color: "#2196F3"             # Optional, hex color
    owner: team-name             # Optional

concepts:
  <concept_key>:
    name: "Display Name"         # Required
    domain: <domain_key>         # Required for non-stub status
    owner: team-name             # Optional but recommended
    definition: |                # Optional markdown
      Detailed business definition
    status: complete             # stub | draft | complete | deprecated
    replaced_by: <concept_key>   # Only for deprecated concepts

relationships:
  - name: verb                   # Required, e.g., "places", "contains"
    from: <concept_key>          # Required
    to: <concept_key>            # Required
    cardinality: "1:N"           # Optional: 1:1, 1:N (no N:M - use bridge concepts)
```

### Concept Status (Derived Automatically)

Status is derived from state unless explicitly set to `deprecated`:

| Status | Condition |
|--------|-----------|
| stub | No domain assigned |
| draft | Has domain, no implementing models |
| complete | Has domain AND implementing models |
| deprecated | Has `replaced_by` set (manual) |

### Tagging dbt Models

Link models to concepts using `meta.concept`:
```yaml
# models/gold/schema.yml
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
    # Path configuration
    conceptual_path: models/conceptual  # Default
    silver_paths:
      - models/silver
      - models/intermediate
    gold_paths:
      - models/gold
      - models/marts

    # Validation rules (error | warn | ignore)
    validation:
      orphan_models: warn              # Models without concept tag
      unimplemented_concepts: warn     # Concepts with no models
      unrealized_relationships: warn   # Relationships not traced
      missing_definitions: ignore      # Concepts without definition
      domain_mismatch: warn            # Tag domain != concept domain

      # Tag validation (opt-in)
      tag_validation:
        enabled: false                 # Validate domain/owner tags
        domains_format: standard       # standard | databricks
```

---

## CLI Commands

| Command | Purpose | Exit Codes |
|---------|---------|------------|
| `dcm init` | Create initial conceptual.yml | 0=success |
| `dcm status` | Show coverage summary | 0=success |
| `dcm validate` | Run validation checks | 0=pass, 1=errors |
| `dcm orphans` | List untagged models | 0=success |
| `dcm sync` | Sync manifest to state | 0=success |
| `dcm apply` | Apply tags to Unity Catalog | 0=success |
| `dcm export` | Export to various formats | 0=success |
| `dcm serve` | Start web UI | 0=success |
| `dcm diff` | Show changes since last sync | 0=no changes, 1=changes |
| `dcm coverage` | Generate coverage report | 0=success |

### Common Flags
- `-v, --verbose`: Increase verbosity (-vv for debug)
- `-q, --quiet`: Suppress non-error output
- `--format human|github`: Output format (github for CI annotations)
- `--project-dir PATH`: Override project directory

---

## Validation Rules

### Errors (Always Fail)

| Code | Description |
|------|-------------|
| E001 | Concept '{name}' is missing required field '{field}' for status '{status}' |
| E002 | Relationship references unknown concept '{concept}' |
| E003 | Concept '{name}' references unknown domain '{domain}' |
| E004 | Domain/group name collision: '{name}' used as both |

### Warnings (Configurable via `vars.dbt_conceptual.validation`)

| Code | Rule Key | Description |
|------|----------|-------------|
| W101 | orphan_models | Model '{name}' is not linked to any concept |
| W102 | unimplemented_concepts | Concept '{name}' has no implementing models |
| W103 | unrealized_relationships | Relationship is not realized by any model |
| W104 | missing_definitions | Concept '{name}' is missing a definition |
| W105 | domain_mismatch | Model domain tag doesn't match concept domain |

### Informational

| Code | Description |
|------|-------------|
| I001 | Concept '{name}' only appears in gold layer |
| I002 | Concept '{name}' is a stub (needs enrichment) |

---

## Layers and Coverage

DCM uses configurable paths to determine which models count toward coverage:

- **silver_paths**: Models in these paths can have `meta.concept` tags (default: `models/silver`, `models/intermediate`)
- **gold_paths**: Models in these paths should have `meta.concept` tags (default: `models/gold`, `models/marts`)

Models without `meta.concept` are inferred from manifest.json - visible for lineage but not part of the conceptual model.

**Coverage** = (tagged models) / (total models in configured paths)

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
dcm validate
```

### Many-to-Many Relationships (Bridge Concepts)

DCM does not support N:M cardinality directly. Instead, model the bridge/junction/fact table as its own concept with 1:N relationships on each side:

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
      Each line represents one product in one order.

relationships:
  - name: contains
    from: order
    to: order_line
    cardinality: "1:N"
  - name: includes
    from: order_line
    to: product
    cardinality: "1:1"
```

This pattern:
- Makes the bridge table a first-class concept (it gets tagged, validated, documented)
- Uses only 1:1 and 1:N cardinalities
- Reflects how the data actually exists in your warehouse

### Brownfield Adoption (Existing Project)
```bash
# 1. Generate stubs from existing model tags
dcm sync --create-stubs

# 2. Check what needs enrichment
dcm status

# 3. Enrich priority concepts (add domain, owner, definition)

# 4. Enable CI warnings, then gradually enforce errors
```

### CI Integration
```yaml
# .github/workflows/pr.yml
- name: Validate conceptual model
  run: dcm validate --format github
```

---

## Taxonomy (Optional)

Define controlled vocabularies:
```yaml
# models/conceptual/taxonomy.yml
version: 1

confidentiality:
  - key: public
    brief: "No restrictions"
  - key: internal
    brief: "Employees only"
  - key: confidential
    brief: "Need-to-know basis"

maturity:
  - key: experimental
  - key: stable
  - key: deprecated
```

Use in concepts:
```yaml
concepts:
  customer:
    confidentiality: internal
    maturity: stable
```

---

## Web UI

Start with `dcm serve`:

| View | URL | Purpose |
|------|-----|---------|
| Canvas | `/` | Visual entity-relationship diagram |
| Coverage | `/coverage` | Implementation progress by domain |
| Bus Matrix | `/bus-matrix` | Concept × Model grid view |

---

## Key Constraints

1. **One tag**: Models link to concepts via `meta.concept` only
2. **Concept keys**: Must be valid YAML keys (lowercase, underscores, no spaces)
3. **Domain required**: Concepts need a domain to be "draft" or "complete"
4. **Unknown refs are errors**: Relationships referencing undefined concepts always fail
5. **Status is derived**: Don't manually set status unless deprecating
6. **No N:M cardinality**: Use bridge concepts with 1:N relationships instead

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Model not linked to any concept" | Add `meta.concept: <key>` to model's schema.yml |
| "Concept has no implementing models" | Either tag a model or set status to stub/draft |
| "References unknown concept" | Check spelling of concept key in relationship |
| "Missing required field" | Add required fields based on concept status |
| Coverage seems wrong | Check `silver_paths` and `gold_paths` in config |

---

## File Structure Example
```
models/
├── conceptual/
│   ├── conceptual.yml          # Main conceptual model
│   ├── conceptual.layout.json  # Canvas positions (auto-generated)
│   ├── taxonomy.yml            # Optional controlled vocabularies
│   └── CLAUDE.md               # This file
├── silver/
│   └── schema.yml              # Models with meta.concept tags
└── gold/
    └── schema.yml              # Models with meta.concept tags
```

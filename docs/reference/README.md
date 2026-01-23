# Reference

Technical reference documentation for dbt-conceptual.

## Contents

- **[CLI Commands](cli.md)** — Complete command reference
- **[YAML Schema](yaml-schema.md)** — conceptual.yml structure
- **[Configuration](configuration.md)** — dbt_project.yml settings
- **[Export Formats](exports.md)** — Output format specifications

## Quick Reference

### Common Commands

```bash
dcm init              # Initialize conceptual.yml
dcm status            # Show coverage by domain
dcm validate          # Validate model integrity
dcm sync              # Sync from dbt project
dcm serve             # Launch web UI
dcm export            # Export reports
dcm diff              # Show changes vs base
```

### Key Files

| File | Purpose |
|------|---------|
| `models/conceptual/conceptual.yml` | Conceptual model definitions |
| `models/conceptual/conceptual.layout.json` | Canvas positions |
| `dbt_project.yml` | Configuration (under `vars.dbt_conceptual`) |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success / No errors |
| `1` | Validation errors found |

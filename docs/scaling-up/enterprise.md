# Enterprise Patterns

Patterns for using dbt-conceptual in larger organizations.

---

## Integration with Data Catalogs

dbt-conceptual can feed enterprise data catalogs. The conceptual model stays in the codebase; metadata syncs to the catalog.

### Unity Catalog (Databricks)

Export coverage data and use it to tag assets:

```bash
dbc export --type coverage --format json -o coverage.json
```

Build a sync script to write domain and owner to Unity Catalog tags.

### Alation / Collibra / Purview

Export as JSON for catalog ingestion:

```bash
dbc export --type coverage --format json -o coverage.json
```

Build a sync script or use the catalog's API to import.

---

## Multi-Project Architectures

Large organizations often have multiple dbt projects.

### Shared Conceptual Model

One conceptual model shared across projects:

```
/shared/
  conceptual/
    conceptual.yml      # Shared vocabulary
    
/project-a/
  dbt_project.yml
  models/
  
/project-b/
  dbt_project.yml
  models/
```

Each project points to the shared `conceptual.yml` via symlink or by copying it in CI.

### Federated Models

Each project owns its domain, rolls up to enterprise view:

```
/enterprise/
  conceptual.yml        # Aggregated view
  
/sales-domain/
  conceptual.yml        # Sales concepts
  
/marketing-domain/
  conceptual.yml        # Marketing concepts
```

A build process merges domain models into the enterprise view.

---

## CI/CD at Scale

### Monorepo Pattern

All projects in one repo, single CI pipeline:

```yaml
# .github/workflows/ci.yml
jobs:
  validate-conceptual:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        project: [sales, marketing, finance]
    steps:
      - uses: actions/checkout@v4
      - run: |
          cd projects/${{ matrix.project }}
          dbc validate
```

### Multi-Repo Pattern

Shared conceptual model in its own repo:

```yaml
# conceptual-model/.github/workflows/ci.yml
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: dbc validate
      
  notify-downstream:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - run: |
          # Trigger dependent project pipelines
          curl -X POST ...
```

---

## Governance Integration

### Approval Workflows

Use PR reviews for concept changes:

```yaml
# .github/CODEOWNERS
/conceptual.yml @data-governance-team
```

Changes to `conceptual.yml` require governance approval.

### Change Notifications

Notify governance on concept changes:

```yaml
- name: Notify on changes
  if: steps.diff.outputs.has_changes == 'true'
  run: |
    dbc diff --base main --format markdown > changes.md
    # Post to Slack, email, etc.
```

### Audit Trail

Git history provides an audit trail:

```bash
git log --oneline -- conceptual.yml
```

For formal auditing, export to a compliance system.

---

## Performance at Scale

### Large Models

For models with 200+ concepts:

- Use domain filtering in the UI
- Export to HTML for faster viewing
- Consider splitting into multiple files (when supported)

### CI Optimization

Cache dependencies:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-dbt-conceptual
```

Run validation only on changes:

```yaml
- name: Check for changes
  id: changes
  run: |
    if git diff --name-only HEAD~1 | grep -q "conceptual.yml"; then
      echo "changed=true" >> $GITHUB_OUTPUT
    fi
    
- name: Validate
  if: steps.changes.outputs.changed == 'true'
  run: dbc validate
```

---

## Security Considerations

### Sensitive Metadata

If concept descriptions contain sensitive information:

- Use confidentiality classification
- Restrict access to `conceptual.yml` via CODEOWNERS
- Consider separate files for sensitive domains

### Access Control

The conceptual model is code — use standard code access controls:

- Branch protection
- Required reviews
- Signed commits (if required)

---

## Migration Patterns

### From Spreadsheets

Export spreadsheet to YAML:

```python
import pandas as pd
import yaml

df = pd.read_excel('data_dictionary.xlsx')
concepts = {}
for _, row in df.iterrows():
    concepts[row['name']] = {
        'name': row['display_name'],
        'domain': row['domain'],
        'definition': row['description']
    }

with open('conceptual.yml', 'w') as f:
    yaml.dump({'concepts': concepts}, f)
```

### From ERwin / ER/Studio

Export entities and relationships, transform to YAML format.

### From Data Catalog

Export concepts from existing catalog, enrich in dbt-conceptual, sync back.

---

## Support Channels

For enterprise support:

- GitHub Issues: Bug reports, feature requests
- Discussions: Questions, patterns, community help

---

## Roadmap Alignment

Enterprise features in development:

- Multi-file support
- Catalog integrations (native connectors)
- Role-based access in UI
- Audit logging

See [GitHub Issues](https://github.com/dbt-conceptual/dbt-conceptual/issues) for status.

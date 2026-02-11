# FAQ

Frequently asked questions.

---

## General

### What's the difference between dbt-conceptual and a data catalog?

A data catalog (Collibra, Alation, Purview) is an enterprise-wide inventory of data assets with access controls, lineage, and compliance features.

dbt-conceptual is lighter — it's a vocabulary layer that lives in your codebase. It defines what concepts mean and tracks which models implement them. It can *feed* a data catalog, but it doesn't replace one.

### Do I need dbt-conceptual if I already have a data catalog?

Maybe. If your catalog is well-maintained and current, you might not need another layer. But many teams find that catalog metadata drifts because it's disconnected from the development workflow.

dbt-conceptual keeps the conceptual model in git, validated in CI, updated as part of normal development. It can sync to your catalog to keep it current.

### Is this the same as dbt's documentation?

No. dbt docs describe *models* — what columns they have, how they're built. dbt-conceptual describes *concepts* — business vocabulary that exists independent of implementation.

A model is `dim_customer`. A concept is "Customer" — a person or company that purchases products. Multiple models might implement the same concept.

---

## Adoption

### How long does adoption take?

Depends on your project size:

| Size | Timeline |
|------|----------|
| Small (< 50 models) | Days |
| Medium (50-200 models) | Weeks |
| Large (200+ models) | Months |

Start with the gold layer. Don't try to cover everything at once.

### Should I tag every model?

No. Focus on business-meaningful models — typically your gold/mart layer. Staging and intermediate models often don't need tags.

### What if I don't know who owns a concept?

Use `UNKNOWN` as a placeholder:

```yaml
concepts:
  mystery_table:
    domain: party
    owner: UNKNOWN
```

This makes gaps visible. Fix them later.

---

## Technical

### Does dbt-conceptual slow down dbt runs?

No. The conceptual model is metadata only — it doesn't affect dbt build, test, or run commands.

### Can I use this with dbt Cloud?

Yes. The conceptual model is just files in your repo. CI validation works in dbt Cloud's CI jobs.

The web UI (`dbc serve`) is for local development — it's not hosted in dbt Cloud.

### What dbt versions are supported?

dbt-core 1.5 and higher.

### Can I split the conceptual model across multiple files?

Not yet. Multi-file support is planned. For now, everything lives in one `conceptual.yml`.

---

## Workflow

### How do I handle concepts that span multiple domains?

Assign to the primary domain and document the overlap:

```yaml
concepts:
  customer:
    domain: party
    description: |
      A person or company that purchases products.
      
      Used by: Sales, Marketing, Finance
```

Or use the `meta` block for co-owners.

### What if different teams define the same concept differently?

That's what dbt-conceptual helps prevent. One definition in `conceptual.yml` becomes the shared truth. Disagreements get resolved in PRs, not in meetings six months later.

### How do I deprecate a concept?

Use `replaced_by`:

```yaml
concepts:
  legacy_customer:
    domain: party
    replaced_by: customer
```

CI can warn or error when deprecated concepts are used.

---

## Integration

### Can I export to Confluence/Notion/etc?

Export to HTML or Markdown:

```bash
dbc export --type coverage --format html -o report.html
dbc export --type diagram --format svg -o model.svg
```

Upload to your wiki manually or automate it.

### Does it work with Unity Catalog?

Yes. Use `dbc apply --propagate-tags` to write domain and owner to dbt model tags, which flow to Unity Catalog.

### Can I import from an existing data dictionary?

There's no built-in import, but the YAML format is simple. Write a script to transform your spreadsheet/export into `conceptual.yml` format.

---

## Troubleshooting

### The UI shows no concepts

Run `dbc sync` to load from your dbt project. If you haven't defined any concepts yet, run `dbc init` first.

### Validation fails on everything

You probably have strict settings. Start with warnings:

```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: warn
      unimplemented_concepts: warn
```

### Changes aren't saving

Check file permissions on `conceptual.yml`. The UI needs write access.

### Ghost concepts appearing

A model references a concept that doesn't exist. Either:
- Define the concept in `conceptual.yml`
- Run `dbc sync` (creates stubs automatically)
- Fix the typo in `meta.concept`

---

## Getting Help

- **GitHub Issues:** Bug reports, feature requests
- **GitHub Discussions:** Questions, patterns, community help
- **Documentation:** You're reading it!

# Governance

{% hint style="info" %}
**Coming Soon** — Extended governance features are in development. See [GitHub Issue #22](https://github.com/dbt-conceptual/dbt-conceptual/issues/22) for progress.
{% endhint %}

## Governance-Ready, Not Governance-Replacement

A well-structured conceptual model provides the foundation for governance: domains, ownership, lineage, shared definitions. For many teams, this is more than they have today.

But dbt-conceptual is not a governance platform. It won't replace Collibra, Purview, or Alation. But it *can* feed them.

### What You Get

| Capability | dbt-conceptual | Full Governance Platform |
|------------|----------------|--------------------------|
| Domain ownership | ✓ | ✓ |
| Concept definitions | ✓ | ✓ |
| Lineage (conceptual → physical) | ✓ | ✓ |
| Approval workflows | — | ✓ |
| Policy enforcement | — | ✓ |
| Cross-platform catalog | — | ✓ |
| Compliance reporting | — | ✓ |

### Where It Fits

**For teams without formal governance:** This might be enough — and it's infinitely more than nothing. Domains, ownership, definitions, all versioned in git. That's a solid foundation.

**For teams on Databricks:** The metadata structure aligns with Unity Catalog. Domains and ownership can feed your ABAC policies directly. Might be all you need.

**For teams with enterprise governance:** dbt-conceptual becomes a feeder. Your conceptual model stays current in the codebase, then syncs to your catalog of record. Architecture that supports governance, not competes with it.

---

## Design Philosophy

**Default: everything open.** Want strictness? Be explicit.

No magic modes. Turn on the flags you care about. If you set nothing, everything works. Surfer-dude by default. Strict-nanny by choice.

dbt-conceptual stays in its lane:

- **Provides** high-level business context (domains, owners, maturity, glossary links)
- **Propagates** that context to models and Unity Catalog
- **Observes** governance-relevant tags teams apply at column level
- **Does not** own classification taxonomies, PII/PHI definitions, or enforcement

Collaborative. Bidirectional. A bridge, not a destination.

---

## Governance as a Design Concern

Most governance is retrofitted. Teams build first, then scramble to document ownership, classify data, and satisfy compliance. The metadata lives in spreadsheets, wikis, or a catalog that drifts from reality within weeks.

dbt-conceptual takes a different position: **basic governance belongs at design time** — at least at the entity level.

We're not solving governance. Column-level classification, policy enforcement, compliance reporting — that's your governance platform's job. But the fundamentals — who owns this concept, what domain it belongs to, how mature it is, where it's defined in your glossary — those decisions happen when you're modeling, whether you capture them or not.

This doesn't mean everything upfront. It means *enough* upfront, with a path to enrich as you mature.

### Progressive Enrichment

Every layer is optional. Every layer compounds.

| Stage | What you add | Who needs it |
|-------|--------------|--------------|
| **Day 1** | Domains, owners | Everyone. Basic accountability. |
| **Day 2** | Maturity, glossary refs | Growing teams. Traceability, catalog alignment. |
| **Day 3** | Taxonomy, stewardship, classification | Enterprise, regulated. Rigor without separate tooling. |

**Day 1** is already part of dbt-conceptual today. You're defining domains and ownership as part of modeling — governance metadata that propagates to your dbt models automatically.

**Day 2 and beyond** are the extended features described below. Same YAML. Same workflow. More fields when you're ready.

The power isn't in any single feature. It's that governance metadata lives where concepts are defined — not in a separate system that drifts, but in the layer that drives implementation. For teams in regulated industries, or mature data platforms, or anyone tired of governance as a spreadsheet exercise: this is unusually tight integration for something that stays completely optional.

---

## Planned Features

### Stewardship

Separate ownership (who builds it) from stewardship (who governs it):
```yaml
domains:
  party:
    owner: party_team
    steward: governance_team

concepts:
  customer:
    domain: party
    steward: customer_governance  # overrides domain steward
```

### Maturity Levels

Signal data trustworthiness, aligned with dbt exposure syntax:

| Level | Value | Meaning |
|-------|-------|---------|
| High | 3 | Production-ready, trusted, governed |
| Medium | 2 | Validated, some caveats |
| Low | 1 | Experimental, use with caution |
```yaml
concepts:
  customer:
    maturity: high

  experimental_metric:
    maturity: low
    deprecated: true  # warning when other concepts depend on it
```

**Domain maturity** is calculated automatically from its concepts:
```
domain_maturity = round(avg(concept_maturities))

3.0       → high
2.0 – 2.9 → medium
1.0 – 1.9 → low
```

Example: a domain with three high (3) and two low (1) concepts averages to 2.2 → **medium**.

### Glossary Integration

Connect concepts to your enterprise glossary:
```yaml
domains:
  party:
    glossary_ref: "alation://domain/party"

concepts:
  customer:
    glossary_ref: "alation://term/customer"
```

Support for Alation, Purview, Collibra, and custom formats.

### Classification Metadata

High-level classification at domain or concept level:
```yaml
domains:
  party:
    confidentiality: internal
    retention: standard
    regulatory: [GDPR]

concepts:
  customer:
    regulatory: [GDPR, CCPA]  # extends domain list
```

Column-level classification remains your governance platform's responsibility.

### Taxonomy Files

Centralize and validate allowed values:
```yaml
# models/conceptual/taxonomy.yml
version: 1

confidentiality:
  - key: public
    brief: "No restrictions"
  - key: internal
    brief: "Employees only"
  - key: confidential
    brief: "Need-to-know"

retention:
  - key: short
    brief: "90 days"
  - key: standard
    brief: "3 years"

regulatory:
  - key: GDPR
    brief: "EU data protection"
  - key: CCPA
    brief: "California privacy"
```

Optional by default. Enable `enforce_taxonomy_validation` for strict mode.

### Sensitive Tag Tracking

Passively observe governance-relevant tags applied at column level:
```yaml
vars:
  dbt_conceptual:
    governance:
      track_tags:
        - PII
        - PHI
        - sensitive
```

Surfaces in reports without enforcement: "Found 12 columns with tracked tags: PII (8), PHI (4)". Visibility for governance teams without burden on data teams.

### Configuration Flags

All optional, all false by default:
```yaml
vars:
  dbt_conceptual:
    governance:
      # Structural requirements
      require_steward: false
      require_maturity: false
      require_glossary_ref: false
      require_confidentiality: false
      require_retention: false
      
      # Behavioral constraints
      enforce_deprecated_as_error: false
      enforce_taxonomy_validation: false
```

Naming convention: `require_*` for mandatory fields, `enforce_*` for behavioral rules.

### Governance Report Export
```bash
dbt-conceptual export --type governance --format markdown
dbt-conceptual export --type governance --format json
dbt-conceptual export --type governance --format html
```

Coverage by domain, maturity rollups, gaps analysis, tracked tag summary.

---

## Two Perspectives

### For Data Teams

> "Governance wants metadata. You want to ship. dbt-conceptual gives you a lightweight way to provide what governance needs without maintaining separate documentation."

Add maturity and glossary refs to concepts you're already defining. Tag columns with PII/PHI as you normally would. Governance gets visibility without spreadsheets. You stay aligned without extra process.

### For Governance Office

> "dbt-conceptual gives you a head start on the high-level stuff — domains, ownership, maturity, glossary alignment. Your teams tag columns with classifications as normal. We surface what they've tagged so you have visibility."

**What you get:** Domain ownership mapped to implementations. Maturity levels from source code. Links to your glossary terms. Gaps report showing missing metadata.

**What you still own:** Column-level classification (PII/PHI/PCI definitions). Enforcement via RLS/ABAC. Pushing classifications downstream. Compliance and audit.

**The handoff:** dbt-conceptual handles business context and ownership. Your tooling handles granular classification and enforcement.

---

## The Bottom Line

If you need a full governance program, you need a full governance program.

But if you need shared vocabulary with clear ownership that actually stays current — and you're tired of the whiteboard being the last moment of truth — this gets you there.

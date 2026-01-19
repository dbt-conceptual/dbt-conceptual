# dbt-conceptual: Positioning Specification

> **Version:** 1.1  
> **Updated:** January 2026

---

## One-Line Summary

Continuous conceptual alignment for dbt projects.

---

## The Problem

### What Died

The traditional data architecture paradigm: architects design conceptual models in isolation, hand them to engineers, validate against implementation. This assumed waterfall delivery, quarterly releases, co-located teams. It produced beautiful diagrams that rotted the moment they were created.

### What Replaced It

Engineer autonomy. dbt democratized transformation. Teams ship daily. No gatekeepers, no handoffs.

### What That Created

Chaos. The whiteboard session on day one is the last moment of shared understanding. After that:

- Models proliferate without coherence
- Naming conventions drift
- Concepts duplicate across teams
- Tribal knowledge calcifies
- Nobody knows what "customer" means anymore

Business feels this pain. Data quality issues. Conflicting definitions. Reports that don't reconcile.

---

## The Synthesis

Conceptual models still have value. They communicate *meaning* across teams, onboard new engineers, explain to the business what we've actually built.

dbt-conceptual embeds conceptual thinking into modern data workflows:

- YAML alongside code, not diagrams in Confluence
- Evolves with the project via git
- Visibility through coverage reports, not enforcement through gates
- Feeds downstream catalogs, doesn't compete with them

Not a return to the old paradigm. A bridge between what worked then and what works now.

---

## Core Philosophy

### Continuous Conceptual Alignment

The conceptual layer tracks implementation as it evolves. No big-design-up-front. No phase gates. Just ongoing coherence between what we *mean* and what we *build*.

### Opinionated but Not Dogmatic

This tool works if you want lightweight conceptual modeling within a dbt project. It doesn't enforce coverage. It doesn't block deployments. It surfaces information and lets humans decide.

### Code-First, Conceptual-Aware

Engineers build. The conceptual layer documents. Both live in the same repo, evolve together, stay aligned by proximity rather than process.

---

## Key Capabilities

### YAML as Source of Truth

Everything lives in `conceptual.yml`. Human-readable, git-friendly, diff-able. No proprietary formats, no database to manage, no sync to maintain.

### Visual Interface

Optional browser-based canvas for those who think spatially. Whiteboard-style: boxes with concept names, verbs on relationship lines. Same YAML underneath — the canvas is just a view. Edit in the UI, changes write to YAML. Edit YAML directly, UI reflects it. No lock-in, no separate artifact.

### Bi-Directional Sync

The conceptual model and dbt project stay aligned through sync:

- **Top-down**: Define concepts in the UI or YAML, associate them with dbt models
- **Bottom-up**: Scan dbt project for `meta.concept` tags, create stubs for referenced but undefined concepts

Already have a dbt project? Sync creates stubs from existing tags. Enrich incrementally. No big-bang migration required.

### Domain-Aware

Concepts and relationships are tagged to domains. Supports data mesh patterns where each domain owns its semantic model. Cross-domain relationships are explicit — you see the boundaries.

### Medallion Layer Tracking

Track which concepts are implemented at each layer:

- **Gold**: Business-facing dimensions and facts (explicitly tagged)
- **Silver**: Cleaned/conformed staging models (explicitly tagged)  
- **Bronze**: Raw sources feeding silver (inferred from manifest.json lineage)

Bronze inference means you see upstream coverage without additional tagging burden.

### M:N Relationships Require Realization

Many-to-many relationships need at least one implementing model (fact/bridge table) to be considered complete. This reflects physical reality — an M:N relationship without a bridge is conceptually valid but not yet realized in the warehouse.

---

## Target User

### The Player-Coach Architect

Not the ivory tower architect who designs and hands off. Not the pure engineer who only thinks in SQL.

The player-coach:

- Writes code but thinks in systems
- Advises teams without blocking them
- Maintains context across a project
- Cares about longevity, not just delivery

This role exists in organizations that actually deliver. It's often informal — the senior engineer everyone consults, the one who notices drift. dbt-conceptual gives them legitimacy: coverage reports as evidence, conceptual models as artifacts they can point to.

### Secondary Users

- **Engineers**: Receive guidance, may contribute to conceptual layer with direction
- **Data governance teams**: Consume metadata for catalogs, lineage, documentation
- **Business stakeholders**: See what their data *means*, not just where it flows

---

## Scope

### What It Is

- Project-level conceptual modeling
- Coherence within a single deliverable
- Compatible with data mesh (each domain owns its model)
- Visual helper for the underlying YAML

### What It Isn't

- Enterprise-wide conceptual hegemony
- Replacement for data catalogs (Collibra, Alation, etc.)
- Enforcement engine or deployment gate
- A diagramming tool that happens to export YAML

---

## Key Differentiators

| Traditional Tooling | dbt-conceptual |
|---------------------|----------------|
| Separate from code | Lives in repo |
| Point-in-time snapshots | Evolves with project |
| Requires dedicated tooling | YAML + CLI + optional UI |
| Enforces compliance | Surfaces information |
| Architect-owned | Team-owned |
| Diagrams as artifacts | YAML as truth, diagrams as views |

---

## Messaging by Audience

### dbt Community

Lead with anti-dogma. "This isn't your enterprise architect's conceptual model." Show the YAML, show the coverage reports, show how it lives alongside `schema.yml`. Emphasize lightweight, code-first, no ceremony.

### Architecture Community

Lead with continuity. "Your conceptual models can finally keep pace with agile delivery." Position as evolution of the discipline, not rejection of it. The thinking still matters; the tooling needed to change.

### Leadership / Governance

Lead with visibility. "Know what your data *means*, not just where it flows." Domain boundaries, ownership metadata, documentation that matches implementation because it lives with it.

### Data Mesh Advocates

Lead with enablement. "This makes decentralization work." Each domain owns its conceptual model. Boundaries stay clean. Downstream consumers can read semantics. Mesh without conceptual clarity is just distributed chaos.

---

## Narrative Arc

*For talks, posts, documentation:*

1. **The Old World**: Conceptual models in Erwin/Visio. Architects owned them. Linear sequence: design → build → validate. Worked when releases were quarterly.

2. **The Disruption**: dbt democratized transformation. Daily shipping. Architect role fragmented. Whiteboard session on day one became the last shared understanding.

3. **The Chaos**: Entropy won. Models proliferate. Naming diverges. Business feels the pain but doesn't know why.

4. **The Insight**: Conceptual thinking still has value. Dogmatic enforcement doesn't scale. Need something that fits modern workflows.

5. **The Bridge**: dbt-conceptual. YAML in repo. Visual canvas as helper. Bi-directional sync. Coverage reports in CI. Feeds catalogs. Doesn't gate. Continuous alignment, not point-in-time validation.

---

## Voice and Tone

- **Pragmatic**: Built by a practitioner, for practitioners
- **Direct**: No enterprise architecture jargon
- **Honest**: Acknowledges limitations, doesn't oversell
- **Experienced**: 30 years of context, hard-won perspective

Avoid:

- Vendor-speak ("unlock value", "drive transformation")
- Absolutism ("you must", "always", "never")
- Defensiveness about the approach

---

## Origin Story

*Use selectively:*

Built from lived experience. Decades watching the old paradigm fail — beautiful models nobody used. Then watching the new paradigm fail differently — fast delivery, mounting chaos.

This tool encodes what actually works: embedded architectural thinking, lightweight enough to survive contact with reality, opinionated enough to provide value.

---

## Technical Positioning

- **Lightweight**: Minimal YAML schema. Concept, relationship, domain.
- **Automation-friendly**: YAML is trivially parseable. LLM tooling can generate/modify.
- **Non-invasive**: Doesn't require changes to existing dbt models beyond optional `meta` tags
- **Observable**: Coverage reports, bus matrix, surfacing of undocumented models
- **Visual**: Optional canvas UI — same data, spatial view

---

## Compatibility Notes

- Layer naming uses medallion terminology (bronze/silver/gold) by default
- Folder paths are configurable — staging/intermediate/marts works
- Bronze associations inferred from lineage, silver/gold explicit
- Works alongside existing dbt metadata (descriptions, tests)
- Exports to Excalidraw, Mermaid, PNG for external consumption

---

*This spec informs all documentation, examples, and generated content for dbt-conceptual. Tone should be consistent: practitioner-to-practitioner, direct, honest about scope and limitations.*

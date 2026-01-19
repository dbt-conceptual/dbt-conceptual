# dbt-conceptual: Positioning Specification

## One-Line Summary

Continuous conceptual alignment for dbt projects.

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

## The Synthesis

Conceptual models still have value. They communicate *meaning* across teams, onboard new engineers, explain to the business what we've actually built.

dbt-conceptual embeds conceptual thinking into modern data workflows:

- YAML alongside code, not diagrams in Confluence
- Evolves with the project via git
- Visibility through coverage reports, not enforcement through gates
- Feeds downstream catalogs, doesn't compete with them

Not a return to the old paradigm. A bridge between what worked then and what works now.

## Core Philosophy

### Continuous Conceptual Alignment

The conceptual layer tracks implementation as it evolves. No big-design-up-front. No phase gates. Just ongoing coherence between what we *mean* and what we *build*.

### Opinionated but Not Dogmatic

This tool works if you want lightweight conceptual modeling within a dbt project. It doesn't enforce coverage. It doesn't block deployments. It surfaces information and lets humans decide.

### Code-First, Conceptual-Aware

Engineers build. The conceptual layer documents. Both live in the same repo, evolve together, stay aligned by proximity rather than process.

### Visual When Helpful

Some people think in boxes and lines. The browser-based canvas is a view into the same YAML — edit visually, save to file. No separate artifact, no lock-in. The CLI and YAML remain the source of truth.

## Target User

### The Player-Coach Architect

Not the ivory tower architect who designs and hands off. Not the pure engineer who only thinks in SQL.

The player-coach:

- Writes code but thinks in systems
- Advises teams without blocking them
- Maintains context across a project
- Cares about longevity, not just delivery

This role exists in organizations that actually deliver. It's often informal - the senior engineer everyone consults, the one who notices drift. dbt-conceptual gives them legitimacy: coverage reports as evidence, conceptual models as artifacts they can point to.

### Secondary Users

- **Engineers**: Receive guidance, may contribute to conceptual layer with direction
- **Data governance teams**: Consume metadata for catalogs, lineage, documentation
- **Business stakeholders**: See what their data *means*, not just where it flows

## Scope

### What It Is

- Project-level conceptual modeling
- Coherence within a single deliverable
- Compatible with data mesh (each domain owns its model)

### What It Isn't

- Enterprise-wide conceptual hegemony
- Replacement for data catalogs (Collibra, Alation, etc.)
- Enforcement engine or deployment gate

## Key Capabilities

### Domain-Aware Modeling

Concepts and relationships are tagged to domains. Supports data mesh patterns where each domain owns its semantic model. Domains are configured per-project — no enterprise-wide taxonomy required.

### Bi-Directional Sync

The conceptual model and dbt project stay aligned through sync:

- **Outbound**: Associating a model writes `meta.concept` to the model's YAML
- **Inbound**: Scanning the project creates stubs for referenced but undefined concepts
- **Continuous**: Changes flow both directions. Edit in the UI or edit the YAML directly — they converge.

### Bottom-Up Adoption

Already have a dbt project? Run sync. It creates stubs from existing `meta.concept` tags in your model files. Enrich incrementally — add domains, descriptions, relationships. No big-bang migration required.

### Layered Coverage (Bronze/Silver/Gold)

Track which concepts are implemented at each medallion layer:

- **Gold**: Explicitly tagged dimensions, facts, bridges (`meta.concept` in model.yml)
- **Silver**: Explicitly tagged staging/cleaned models (`meta.concept` in model.yml)  
- **Bronze**: *Inferred* from manifest.json lineage — which sources feed your Silver models

Bronze requires no additional tagging. It surfaces automatically, showing the raw data foundations of each concept.

### Relationship Realization

Relationships between concepts can be *realized* by fact and bridge tables:

- 1:1 and 1:N relationships may exist without implementing models (the FK lives in a dimension)
- **M:N relationships require at least one implementing model** (bridge/associative table) to be considered complete

This reflects physical reality: many-to-many needs a resolver.

## Key Differentiators

| Traditional Tooling | dbt-conceptual |
|---------------------|----------------|
| Separate from code | Lives in repo |
| Point-in-time snapshots | Evolves with project |
| Requires dedicated tooling | YAML + CLI + optional UI |
| Enforces compliance | Surfaces information |
| Architect-owned | Team-owned |
| One-way documentation | Bi-directional sync |

## Messaging by Audience

### dbt Community

Lead with anti-dogma. "This isn't your enterprise architect's conceptual model." Show the YAML, show the coverage reports, show how it lives alongside `schema.yml`. Emphasize lightweight, code-first, no ceremony.

### Architecture Community

Lead with continuity. "Your conceptual models can finally keep pace with agile delivery." Position as evolution of the discipline, not rejection of it. The thinking still matters; the tooling needed to change.

### Leadership / Governance

Lead with visibility. "Know what your data *means*, not just where it flows." Domain boundaries, ownership metadata, documentation that matches implementation because it lives with it.

### Data Mesh Advocates

Lead with enablement. "This makes decentralization work." Each domain owns its conceptual model. Boundaries stay clean. Downstream consumers can read semantics. Mesh without conceptual clarity is just distributed chaos.

## Narrative Arc (for talks, posts, documentation)

1. **The Old World**: Conceptual models in Erwin/Visio. Architects owned them. Linear sequence: design → build → validate. Worked when releases were quarterly.

2. **The Disruption**: dbt democratized transformation. Daily shipping. Architect role fragmented. Whiteboard session on day one became the last shared understanding.

3. **The Chaos**: Entropy won. Models proliferate. Naming diverges. Business feels the pain but doesn't know why.

4. **The Insight**: Conceptual thinking still has value. Dogmatic enforcement doesn't scale. Need something that fits modern workflows.

5. **The Bridge**: dbt-conceptual. YAML in repo. Coverage reports in CI. Feeds catalogs. Doesn't gate. Continuous alignment, not point-in-time validation.

## Voice and Tone

- **Pragmatic**: Built by a practitioner, for practitioners
- **Direct**: No enterprise architecture jargon
- **Honest**: Acknowledges limitations, doesn't oversell
- **Experienced**: 30 years of context, hard-won perspective

Avoid:

- Vendor-speak ("unlock value", "drive transformation")
- Absolutism ("you must", "always", "never")
- Defensiveness about the approach

## Origin Story (use selectively)

Built from lived experience. Decades watching the old paradigm fail - beautiful models nobody used. Then watching the new paradigm fail differently - fast delivery, mounting chaos.

This tool encodes what actually works: embedded architectural thinking, lightweight enough to survive contact with reality, opinionated enough to provide value.

## Technical Positioning

- **Lightweight**: Minimal YAML schema. Concept, relationship, domain.
- **Automation-friendly**: YAML is trivially parseable. LLM tooling can generate/modify.
- **Non-invasive**: Doesn't require changes to existing dbt models beyond optional meta tags
- **Observable**: Coverage reports, bus matrix, surfacing of undocumented models
- **Visual**: Optional browser-based canvas for spatial thinkers

## Compatibility Notes

- Layer naming uses medallion terminology (bronze/silver/gold) by default
- Folder structure configurable — staging/intermediate/marts maps to silver/gold
- Bronze inferred from lineage, silver/gold explicitly tagged
- Works alongside existing dbt metadata (descriptions, tests)
- Exports to Excalidraw, Mermaid, PNG for documentation

---

*This spec informs all documentation, examples, and generated content for dbt-conceptual. Tone should be consistent: practitioner-to-practitioner, direct, honest about scope and limitations.*

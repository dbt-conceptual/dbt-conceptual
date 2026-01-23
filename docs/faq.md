# FAQ

## How is this different from dbt exposures?

Exposures document downstream consumers — "this dashboard uses these models." dbt-conceptual documents upstream meaning — "this model implements the Customer concept."

Exposures answer: "who uses this data?"
Concepts answer: "what does this data mean?"

They're complementary. Use exposures for lineage to BI tools and applications. Use dbt-conceptual for shared vocabulary and business definitions.

---

## Why not just use a data catalog?

Data catalogs (Atlan, Alation, Collibra, Purview) are systems of record for governance. dbt-conceptual is a system of capture — where concepts are defined alongside the code that implements them.

Catalogs drift because they're maintained separately from the codebase. Someone has to remember to update the catalog when the model changes. They usually don't.

dbt-conceptual stays current because it lives in the repo. Definitions travel with the code. CI surfaces drift before it ships.

The relationship: dbt-conceptual *feeds* catalogs, doesn't replace them. Define concepts at the source, push to your catalog of record.

---

## Isn't this just ERD tooling in git?

ERDs model structure — entities, attributes, relationships at the physical level. The goal is DDL generation and schema documentation.

dbt-conceptual models *meaning* — business concepts, ownership, shared vocabulary. No attribute-level detail. No logical→physical derivation. No DDL generation.

Think of it this way:
- ERD: "The `customers` table has columns `id`, `name`, `email`, `created_at`"
- dbt-conceptual: "Customer means a person or company that purchases products. Owned by the customer team. Implemented by `dim_customer`."

The boxes on the whiteboard, not the schema diagram.

---

## What about dbt Mesh and cross-project refs?

dbt Mesh solves project boundaries and contract enforcement — how do multiple dbt projects share models safely?

dbt-conceptual solves shared vocabulary — what do the concepts mean, and who owns them?

If you're using Mesh, dbt-conceptual helps ensure the concepts exposed across project boundaries have consistent definitions. The `customer` in Project A should mean the same thing as the `customer` referenced by Project B.

Complementary layers: Mesh handles the plumbing, dbt-conceptual handles the semantics.

---

## Why YAML instead of a visual-first tool?

Because YAML is what CI/CD, version control, and code review understand.

The visual UI exists — it's good for exploration, editing, and onboarding. But the source of truth is text that lives with your dbt project. That's what makes it *operational*:

- Changes go through pull requests
- Drift surfaces in CI
- History lives in git
- No separate system to keep in sync

Visual-first tools create beautiful diagrams that drift. dbt-conceptual gives you both: a visual canvas for exploration and editing, backed by YAML that lives in your repo. The UI is the interface; the code is what survives.

---

## How is this different from a semantic layer (dbt Semantic Layer, Cube, etc.)?

Semantic layers define metrics and dimensions for consumption — "revenue is sum of amount where status = 'completed'". They're query interfaces for BI tools.

dbt-conceptual defines business concepts for shared understanding — "Order means a confirmed purchase by a customer". It's vocabulary, not calculation.

| | Semantic Layer | dbt-conceptual |
|---|----------------|----------------|
| **Purpose** | Metrics for BI | Vocabulary for teams |
| **Granularity** | Measures, dimensions | Concepts, relationships |
| **Consumer** | Analysts, dashboards | Engineers, architects |
| **Output** | Query API | Documentation, validation |

You might use both: semantic layer for "how do I query revenue?", dbt-conceptual for "what does Customer mean across our organization?"

---

## Do I need an architect to use this?

No. But you need someone who cares about shared vocabulary.

That might be a principal engineer who's tired of answering "what does this table mean?" It might be a data lead who notices naming drift across teams. It might be an analytics engineer who wants to document the domain model they carry in their head.

The tool is lightweight enough for a single person to maintain. The value compounds when the whole team references it.

---

## What if nobody maintains the conceptual model?

Then it drifts and becomes useless — just like any documentation.

dbt-conceptual doesn't solve organizational problems. If nobody owns shared vocabulary today, this tool won't magically create ownership. That's a people problem.

What it *does* do: lower the barrier. If maintaining a conceptual model previously meant Erwin licenses and a formal review process, most teams skipped it. If it's a YAML file in the repo with CI validation, the friction drops enough that someone *might* actually do it.

---

## Can I use this without the medallion architecture?

The tool assumes Bronze → Silver → Gold layers because that's the most common pattern for dbt projects doing dimensional modeling.

If your architecture is different:
- **Different folder names?** Configurable via `silver_paths` and `gold_paths`
- **No medallion at all?** The layer tracking won't map cleanly, but concepts and relationships still work
- **Not doing dimensional modeling?** The bus matrix and fact/dimension semantics won't apply, but core coverage tracking still works

It's opinionated by design. If the opinions don't fit, the tool may not be for you — and that's fine.

---

## Is this ready for production?

It's ready for *use*. Whether it's ready for *your* production depends on your risk tolerance.

The core functionality — concepts, relationships, coverage tracking, validation, UI — is stable and tested. The extended governance features (maturity, glossary refs, taxonomy) are in development.

It's MIT licensed, open source, no telemetry. Worst case: you try it, it doesn't fit, you delete the YAML file. The only artifact is a file in your repo.

---

## What's "operational conceptual modeling"?

A term we're introducing to describe conceptual models that drive implementation rather than drift from it.

Traditional conceptual modeling: whiteboard → formal model → logical model → physical model → implementation. By the time code ships, the conceptual model is already stale.

Operational conceptual modeling: conceptual model lives in the repo, validated in CI, connected to the models it describes. It stays current because it's part of the development workflow, not a separate artifact.

The boxes on the whiteboard, operationalized.

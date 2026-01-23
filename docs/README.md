# dbt-conceptual

**Conceptual modeling without the ceremony. Shared vocabulary for data teams who don't have time for meetings.**

> If you've ever taken a photo of the whiteboard after a meeting to capture the model — this is for you.

## What is dbt-conceptual?

dbt-conceptual bridges the gap between conceptual data modeling and dbt implementation. It lets you:

- **Define concepts and relationships** in YAML alongside your dbt project
- **Tag dbt models** with `meta.concept` to link implementation to design
- **Track coverage** — see which concepts are implemented, which are drafts
- **Surface changes in CI** — know when someone introduces a new business concept
- **Visualize** with an interactive web UI

![Conceptual model canvas](assets/canvas-example.png)

## Quick Links

<table>
<tr>
<td width="50%">

### Get Started
- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quick-start.md)

### Learn
- [Why Conceptual Models Matter](concepts/README.md)
- [How It Works](concepts/how-it-works.md)

</td>
<td width="50%">

### Guides
- [Defining Concepts](guides/defining-concepts.md)
- [Tagging dbt Models](guides/tagging-models.md)
- [Validation](guides/validation.md)
- [CI/CD Integration](guides/ci-integration.md)

### Reference
- [CLI Commands](reference/cli.md)
- [YAML Schema](reference/yaml-schema.md)

</td>
</tr>
</table>

## Philosophy

The boxes on the whiteboard were never the problem. They still work. They still create shared understanding in five minutes.

The problem was everything *after* the boxes — the cascade into logical models, physical models, DDL generation, change management. That couldn't keep pace with modern delivery.

**dbt-conceptual stops at the boxes. But connects them to reality.**

No logical model. No physical derivation. Just shared vocabulary that lives with the code.

## Who This Is For

**For architects who write code and engineers who think in systems.**

- The player-coach who advises without blocking
- The senior engineer everyone asks "what does this table mean?"
- The data lead who notices drift before it compounds

## What This Isn't

- **Not an enterprise data catalog** — feeds Collibra/Purview/Alation, doesn't replace them
- **Not a deployment gate** — surfaces information, doesn't block PRs
- **Not Erwin-in-git** — no logical models, no DDL generation, no attribute-level detail

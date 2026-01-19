# dbt-conceptual

[![PyPI version](https://img.shields.io/pypi/v/dbt-conceptual.svg)](https://pypi.org/project/dbt-conceptual/)
[![Python ≥3.11](https://img.shields.io/badge/python-≥3.11-blue.svg)](https://pypi.org/project/dbt-conceptual/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/feriksen-personal/dbt-conceptual/actions/workflows/ci.yml/badge.svg)](https://github.com/feriksen-personal/dbt-conceptual/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/feriksen-personal/dbt-conceptual/branch/main/graph/badge.svg)](https://codecov.io/gh/feriksen-personal/dbt-conceptual)

**Continuous conceptual alignment for dbt projects.**

---

## What Died

The data architect would sit down with business stakeholders and SMEs, sketch boxes and lines on a whiteboard until everyone nodded. That whiteboard became a conceptual model in Erwin or PowerDesigner. From there, a logical model — normalized, pristine. From the logical, a physical model. Then down to the engineers: "We're building this."

Business would come back: "We need more." Back to the whiteboard. Back to the ivory tower. Update the conceptual, refresh the logical, derive an updated physical. Back to the engineers: "We're changing this, adding that."

Repeat ad infinitum. Or at least, repeat quarterly — because that's how fast this process could move.

It worked when releases shipped quarterly. It worked when teams were co-located. It worked when the data architect owned the timeline.

Then it stopped working.

## What Replaced It

Engineer autonomy. dbt democratized transformation. Teams ship daily. The architect who says "wait for the model" gets routed around. No gatekeepers, no handoffs, no time for the ivory tower round-trip.

## What That Created

The whiteboard session on day one is now the last moment of shared understanding. After that:

- Models proliferate without coherence
- Naming conventions drift
- Concepts duplicate across teams
- Tribal knowledge calcifies

Nobody knows what "customer" means anymore.

The conceptual→logical→physical cascade is gone. But nothing replaced the thinking it forced. We kept the speed, lost the shared vocabulary.

## The Bridge

Conceptual models still have value. They communicate meaning across teams, onboard new engineers, explain to the business what we've actually built.

**dbt-conceptual** embeds conceptual thinking into modern data workflows:

- YAML alongside code, not diagrams in Confluence
- Evolves with the project via git
- Visibility through coverage reports, not enforcement through gates
- Feeds downstream catalogs, doesn't compete with them

Not a return to the old paradigm. A bridge between what worked then and what works now.

---

## Installation

```bash
pip install dbt-conceptual
```

No signup required. No telemetry. No "please star this repo" popups.

---

## Quick Start

Define your business concepts in `models/conceptual/conceptual.yml`:

```yaml
version: 1

domains:
  party:
    name: Party
    color: "#E3F2FD"
  transaction:
    name: Transaction
    color: "#FFF3E0"

concepts:
  customer:
    name: Customer
    domain: party
    definition: "A person or entity that places orders"

  order:
    name: Order
    domain: transaction
    definition: "A purchase transaction made by a customer"

relationships:
  - verb: places
    from: customer
    to: order
    cardinality: "1:N"
```

Tag your dbt models:

```yaml
# models/customers.yml
models:
  - name: customers
    meta:
      concept: customer

# models/orders.yml
models:
  - name: orders
    meta:
      realizes:
        - customer:places:order
```

Track alignment:

```bash
# See what's implemented
dbt-conceptual status

# Validate in CI
dbt-conceptual validate

# Launch visual editor
dbt-conceptual serve
```

---

## How It Works

### YAML as Source of Truth

Everything lives in `conceptual.yml`. Human-readable, git-friendly, diff-able. No proprietary formats, no database to manage, no sync to maintain.

### Bi-Directional Sync

The conceptual model and dbt project stay aligned:

- **Top-down**: Define concepts, associate them with dbt models
- **Bottom-up**: Scan dbt project for `meta.concept` tags, create stubs for undefined references

Already have a dbt project? Run sync to create stubs from existing tags. Enrich incrementally. No big-bang migration required.

```bash
# Tag your existing models, then:
dbt-conceptual sync --create-stubs

# Output:
# Created 12 concept stubs
# Created 8 relationship stubs
```

### Domain-Aware

Concepts and relationships are tagged to domains. Supports data mesh patterns where each domain owns its semantic model. Cross-domain relationships are explicit — you see the boundaries.

### Medallion Layer Tracking

Track which concepts are implemented at each layer:

- **Gold**: Business-facing dimensions and facts (explicitly tagged via `meta.concept`)
- **Silver**: Cleaned/conformed staging models (explicitly tagged via `meta.concept`)
- **Bronze**: Raw sources feeding silver (inferred from manifest.json lineage)

Bronze inference means you see upstream coverage without additional tagging burden.

---

## Visual Interface

Launch a browser-based canvas for those who think spatially:

```bash
pip install dbt-conceptual[serve]
dbt-conceptual serve
```

Open your browser to <http://127.0.0.1:8050>

**Whiteboard-style canvas**:

- Drag concepts to position them
- Click concepts/relationships to edit properties
- Verb labels on relationship lines
- Domain-based coloring
- Auto-save to YAML

The canvas is just a view. Same YAML underneath. Edit in the UI, changes write to YAML. Edit YAML directly, UI reflects it. No lock-in, no separate artifact.

**Integrated reports**:

- Coverage tab: Which concepts are implemented, which layers have them
- Bus Matrix tab: Dimensional conformance across fact tables

---

## Coverage Tracking

See which concepts are implemented at each layer:

```text
$ dbt-conceptual status

Concepts by Domain
==================

party (1 concept)
  ✓ customer [complete]     [S:●●] [G:●]

transaction (2 concepts)
  ✓ order [complete]        [S:●]  [G:●]
  ⚠ shipment [stub]         [S:○]  [G:○]

catalog (1 concept)
  ✓ product [complete]      [S:●]  [G:●]
```

**Status meanings**:

- `complete`: Has domain AND has ≥1 associated model
- `draft`: Missing domain OR zero associated models
- `stub`: Created from sync, needs enrichment

---

## CI Validation

Catch drift before it ships:

```bash
$ dbt-conceptual validate

ERROR: dim_customer_legacy references concept 'client' which does not exist
       Did you mean: 'customer'?

ERROR: fact_returns realizes 'customer:returns:order'
       but relationship 'returns' does not exist
```

Configure which validations are errors, warnings, or ignored in `dbt_project.yml`:

```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: warn          # Models not linked to any concept
      unimplemented_concepts: warn # Concepts with no implementing models
      unrealized_relationships: warn # Relationships with no realizing models
      missing_definitions: ignore  # Concepts without definitions
```

Severity options: `error`, `warn`, `ignore`

Unknown references (e.g., `meta.concept: nonexistent`) are always errors and cannot be configured.

### GitHub Actions Integration

```yaml
# .github/workflows/ci.yml
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install dbt-core dbt-conceptual

      - name: Validate conceptual model
        run: dbt-conceptual validate --format github
```

Use `--format github` for native GitHub Actions annotations. Errors and warnings appear inline in PR diffs.

---

## Pull Request Integration

See what conceptual changes are introduced in each PR:

```bash
# Compare against target branch
$ dbt-conceptual diff --base main

Conceptual Changes
==================================================

Concepts:
--------------------------------------------------
  + refund (transaction) - draft
  + dispute (transaction) - stub
  ~ customer
      definition: 'A person...' → 'An individual or organization...'
      owner: None → '@customer-team'

Relationships:
--------------------------------------------------
  + customer:disputes:order (M:N) - draft
```

This surfaces conceptual drift without blocking merges. Someone notices. Someone cares.

### GitHub Actions Workflow

Automatically show conceptual changes in pull requests:

```yaml
# .github/workflows/conceptual-diff.yml
name: Conceptual Model Changes

on:
  pull_request:
    paths:
      - 'models/**/*.yml'
      - 'models/conceptual/conceptual.yml'

jobs:
  diff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Need full history for diff

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install dbt-core dbt-conceptual

      - name: Show conceptual changes
        run: dbt-conceptual diff --base ${{ github.base_ref }} --format github
```

The `--format github` output creates annotations that appear inline in the pull request:

```
::notice title=New Concept::refund (transaction) - draft
::warning title=New Concept Missing Description::dispute (transaction)
::notice title=Modified Concept::customer (definition, owner)
::notice title=New Relationship::customer:disputes:order (M:N) - draft
```

---

## Export Formats

```bash
# Excalidraw — editable diagrams
dbt-conceptual export --format excalidraw

# PNG — static diagram image (requires: pip install dbt-conceptual[png])
dbt-conceptual export --format png -o diagram.png

# Mermaid — for docs and GitHub
dbt-conceptual export --format mermaid

# Coverage report — HTML dashboard
dbt-conceptual export --format coverage

# Bus matrix — dimensions vs facts
dbt-conceptual export --format bus-matrix
```

---

## Configuration

Works out of the box. Override in `dbt_project.yml` if needed:

```yaml
vars:
  dbt_conceptual:
    conceptual_path: models/conceptual    # default
    silver_paths:
      - models/silver                     # default
      - models/staging                    # add custom paths
    gold_paths:
      - models/gold                       # default
      - models/marts                      # add custom paths
    bronze_paths:
      - models/bronze                     # default
```

Or via CLI:

```bash
dbt-conceptual validate --gold-paths models/marts
```

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

## Opinionated by Design

This tool works if you want lightweight conceptual modeling within a dbt project.

**What we're opinionated about**:

- YAML in repo (not diagrams in external tools)
- Medallion architecture (bronze/silver/gold layers)
- Dimensional modeling vocabulary (dims, facts, bridges)

**What we're flexible about**:

- Your specific folder names (configurable via paths)
- Whether you use dbt groups, tags, or other organizational features
- Whether you adopt top-down (design first) or bottom-up (sync from existing tags)

If this doesn't match your stack, this tool is not for you. No judgment — just not the target audience.

---

## Target User

The player-coach architect:

- Writes code but thinks in systems
- Advises teams without blocking them
- Maintains context across a project
- Cares about longevity, not just delivery

This role exists in organizations that actually deliver. It's often informal — the senior engineer everyone consults, the one who notices drift. dbt-conceptual gives them legitimacy: coverage reports as evidence, conceptual models as artifacts they can point to.

---

## CLI Reference

| Command | Description |
| ------- | ----------- |
| `dbt-conceptual init` | Create initial conceptual.yml |
| `dbt-conceptual serve` | Start web UI server |
| `dbt-conceptual status` | Show coverage status |
| `dbt-conceptual validate` | Validate conceptual model |
| `dbt-conceptual validate --no-drafts` | Fail if any draft/stub entities |
| `dbt-conceptual diff --base <ref>` | Compare conceptual model against git ref |
| `dbt-conceptual diff --base main --format github` | Show changes in GitHub Actions format |
| `dbt-conceptual sync` | Sync from dbt project |
| `dbt-conceptual sync --create-stubs` | Create stubs for undefined references |
| `dbt-conceptual export --format <fmt>` | Export diagram |
| `dbt-conceptual list concepts` | List all concepts |
| `dbt-conceptual list concepts --status draft` | List concepts by status |
| `dbt-conceptual list relationships` | List all relationships |

---

## Example: jaffle-shop

Try it with the [jaffle-shop](https://github.com/dbt-labs/jaffle-shop) demo project:

```bash
# Clone jaffle-shop
git clone https://github.com/dbt-labs/jaffle-shop.git
cd jaffle-shop

# Install dbt-conceptual
pip install dbt-conceptual[serve]

# Initialize conceptual model
dbt-conceptual init

# Define your business concepts (edit models/conceptual/conceptual.yml)
# Then tag your models (add meta.concept to schema.yml files)

# View coverage
dbt-conceptual status

# Launch interactive UI
dbt-conceptual serve
```

---

## Contributing

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

PRs that work > PRs with extensive documentation about why they might work.

```bash
# Development setup
git clone https://github.com/feriksen-personal/dbt-conceptual.git
cd dbt-conceptual
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
black --check .
mypy src/dbt_conceptual
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Origin Story

Built from lived experience. Decades watching the old paradigm fail — beautiful models nobody used. Then watching the new paradigm fail differently — fast delivery, mounting chaos.

This tool encodes what actually works: embedded architectural thinking, lightweight enough to survive contact with reality, opinionated enough to provide value.

---

<p align="center">
  <sub>Works on my machine. Might work on yours.</sub>
</p>

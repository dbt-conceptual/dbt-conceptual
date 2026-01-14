# dbt-conceptual

[![PyPI version](https://img.shields.io/pypi/v/dbt-conceptual.svg)](https://pypi.org/project/dbt-conceptual/)
[![Python versions](https://img.shields.io/pypi/pyversions/dbt-conceptual.svg)](https://pypi.org/project/dbt-conceptual/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/YOUR_USERNAME/dbt-conceptual/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/dbt-conceptual/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/dbt-conceptual/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/dbt-conceptual)
[![Downloads](https://img.shields.io/pypi/dm/dbt-conceptual.svg)](https://pypi.org/project/dbt-conceptual/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Bridge the gap between conceptual models and your lakehouse.**

---

## ⚠️ Opinionated by Design

This tool is built for a specific architecture. It expects:

- **dbt** — Your transformation layer
- **Medallion architecture** — Silver (cleaned/conformed) → Gold (business/integrated)
- **Dimensional modeling** — dims, facts, bridges in gold

If that's not your stack, this tool is not for you. No judgment — just not the target audience.

---

## The Problem

Every data team has a conceptual model — *"we have Customers, Orders, Products"* — but it lives in PowerPoint, Visio, or people's heads. Disconnected from code. Drifting. Stale.

```
CONCEPTUAL MODEL                          LAKEHOUSE
(slides, whiteboards, heads)              (dbt, Databricks, Snowflake)

  Customer ── Order ── Product    →→→     dim_customer_shopify, dim_customer_crm,
                                          dim_product, fact_order_lines,
        🤷 GAP 🤷                          bridge_customer_segment...
```

When someone asks *"Do we have Customer data?"* — you grep through 200 models hoping to find the answer.

## The Solution

**dbt-conceptual** tracks which business concepts your dbt models implement:

```yaml
# models/conceptual/model.yml
concepts:
  customer:
    domain: party
    owner: customer_team
    definition: "A person or company that purchases products"

  order:
    domain: transaction
    owner: orders_team
    definition: "A confirmed purchase by a customer"

relationships:
  - name: places
    from: customer
    to: order

  - name: contains
    from: order
    to: product
```

```yaml
# models/gold/dim_customer/dim_customer.yml
models:
  - name: dim_customer
    meta:
      concept: customer

# models/gold/fact_order_lines/fact_order_lines.yml
models:
  - name: fact_order_lines
    meta:
      realizes:
        - customer:places:order
        - order:contains:product
```

Then visualize, validate, and export:

```
┌──────────────────────┐         ┌──────────────────────┐         ┌──────────────────────┐
│      Customer        │         │        Order         │         │       Product        │
│                      │         │                      │         │                      │
│   [S:●●] [G:●]       │━places━▶│   [S:●]  [G:●]       │━contains▶│   [S:●]  [G:●]      │
└──────────────────────┘         └──────────────────────┘         └──────────────────────┘
```

---

## Installation

```bash
# No signup required. No telemetry. No "please star this repo" popups.
pip install dbt-conceptual
```

## Quick Start

```bash
# Initialize in your dbt project
cd my-dbt-project
dbt-conceptual init

# If you already have meta.concept tags, generate the conceptual model
dbt-conceptual sync --create-stubs

# View coverage
dbt-conceptual status

# Launch visual editor
dbt-conceptual serve

# Validate in CI
dbt-conceptual validate

# Export diagram
dbt-conceptual export --format excalidraw
```

---

## Features

### 📊 Coverage Tracking

See which concepts are implemented at each layer:

```
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

### 🎨 Visual Editor

Interactive viewer with hand-drawn Excalidraw aesthetic:

```bash
$ dbt-conceptual serve
Serving at http://localhost:8080
```

- Drag concepts to arrange
- Click to edit properties
- Draw new relationships
- Saves directly to YAML

### ✅ CI Validation

Catch drift before it ships:

```bash
$ dbt-conceptual validate

ERROR: dim_customer_legacy references concept 'client' which does not exist
       Did you mean: 'customer'?

ERROR: fact_returns realizes 'customer:returns:order' 
       but relationship 'returns' does not exist
```

### 📤 Export Formats

```bash
# Excalidraw — editable diagrams
dbt-conceptual export --format excalidraw

# Mermaid — for docs and GitHub
dbt-conceptual export --format mermaid

# Coverage report — HTML dashboard
dbt-conceptual export --format coverage

# Bus matrix — dimensions vs facts
dbt-conceptual export --format bus-matrix
```

---

## How It Works

### 1. Define Concepts

Create `models/conceptual/model.yml`:

```yaml
version: 1

domains:
  party:
    name: "Party"
    color: "#E3F2FD"
  transaction:
    name: "Transaction"
    color: "#FFF3E0"
  catalog:
    name: "Catalog"
    color: "#F1F8E9"

concepts:
  customer:
    name: "Customer"
    domain: party
    owner: customer_team
    definition: "A person or company that purchases products"
    status: complete

  order:
    name: "Order"
    domain: transaction
    owner: orders_team
    definition: "A confirmed purchase by a customer"
    status: complete

  product:
    name: "Product"
    domain: catalog
    owner: catalog_team
    definition: "An item available for purchase"
    status: complete

relationships:
  - name: places
    from: customer
    to: order
    cardinality: "1:N"

  - name: contains
    from: order
    to: product
    cardinality: "N:M"
```

### 2. Tag dbt Models

Add `meta.concept` to dimensions:

```yaml
# models/gold/dim_customer/dim_customer.yml
version: 2
models:
  - name: dim_customer
    description: "Customer dimension"
    meta:
      concept: customer
```

Add `meta.realizes` to facts and bridges:

```yaml
# models/gold/fact_order_lines/fact_order_lines.yml
version: 2
models:
  - name: fact_order_lines
    description: "Order line items fact"
    meta:
      realizes:
        - customer:places:order
        - order:contains:product
```

### 3. Validate & Visualize

```bash
# Check everything links up
dbt-conceptual validate

# See coverage
dbt-conceptual status

# Open visual editor
dbt-conceptual serve
```

---

## Bottom-Up Adoption

Already have a dbt project? Start tagging models, then generate the conceptual model:

```bash
# Add tags to your existing schema.yml files
# Then run:
dbt-conceptual sync --create-stubs

# Output:
# Created 12 concept stubs
# Created 8 relationship stubs
# 
# Run 'dbt-conceptual status' to see what needs enrichment
```

The tags ARE the adoption. The tool just makes them visible.

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
```

Or via CLI:

```bash
dbt-conceptual validate --gold-paths models/marts
```

---

## CI/CD Integration

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
        run: dbt-conceptual validate
```

---

## Documentation

- [Full Documentation](https://dbt-conceptual.readthedocs.io/)
- [Configuration Reference](docs/configuration.md)
- [CLI Reference](docs/cli.md)
- [Export Formats](docs/exports.md)

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

PRs that work > PRs with extensive documentation about why they might work.

```bash
# Development setup
git clone https://github.com/YOUR_USERNAME/dbt-conceptual.git
cd dbt-conceptual
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
black --check .
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built with frustration from years of conceptual models rotting in PowerPoint.

No mass emails were sent to coordinate this project.

---

<p align="center">
  <sub>Works on my machine. Might work on yours.</sub>
</p>

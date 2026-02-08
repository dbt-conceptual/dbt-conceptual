# Installation

Get dbt-conceptual installed and ready to use.

---

## Requirements

- Python 3.9 or higher
- A dbt project (dbt-core 1.5+)

---

## Install via pip

```bash
pip install dbt-conceptual
```

This installs the `dbt-conceptual` command (and the `dbc` alias).

### Verify Installation

```bash
dbc --version
```

---

## Install in a Virtual Environment

Recommended for project isolation:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install
pip install dbt-conceptual
```

---

## Install with dbt

If you're using a requirements.txt:

```text
dbt-core>=1.5
dbt-snowflake>=1.5  # or your adapter
dbt-conceptual
```

Then:

```bash
pip install -r requirements.txt
```

---

## Development Install

For contributing or running from source:

```bash
git clone https://github.com/dbt-conceptual/dbt-conceptual.git
cd dbt-conceptual
pip install -e ".[dev]"
```

---

## What Gets Installed

| Command | Description |
|---------|-------------|
| `dbt-conceptual` | Full command name |
| `dbc` | Short alias |

Both work identically:

```bash
dbt-conceptual serve
dbc serve
```

---

## Next Steps

- [Quick Start](quick-start.md) — Initialize your first conceptual model
- [Tutorial](tutorial.md) — Build a complete example step by step

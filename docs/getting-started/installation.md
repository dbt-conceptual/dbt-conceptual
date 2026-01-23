# Installation

## Requirements

- Python 3.11 or higher
- pip (Python package manager)

## Install via pip

```bash
pip install dbt-conceptual
```

That's it. No signup. No telemetry. No configuration required.

## Optional: Web UI

The interactive web UI requires additional dependencies:

```bash
pip install dbt-conceptual[serve]
```

This adds Flask and related packages for the local development server.

## Verify Installation

```bash
dcm --version
```

You should see the version number printed.

## Next Steps

- [Quick Start](quick-start.md) — Initialize your first conceptual model
- [Demo Mode](../ui/README.md) — Explore without a dbt project

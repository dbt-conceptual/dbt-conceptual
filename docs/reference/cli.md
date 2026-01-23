# dcm CLI Reference

## Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help message and exit |

## Commands

### `status` - Show conceptual model coverage status

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project root |
| `--format [human\|github]` | Output format (default: human) |

### `orphans` - List models without concept/realizes tags

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project root |
| `--format [human\|github]` | Output format (default: human) |

### `validate` - Validate conceptual model correspondence

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project root |
| `--format [human\|github]` | Output format (default: human) |

### `init` - Initialize dbt-conceptual in a project

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project root |
| `--force` | Overwrite existing files |

### `sync` - Discover dbt models and sync with conceptual model

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project root |
| `--dry-run` | Show what would be changed without modifying files |

### `export` - Export conceptual model to various formats

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project root |
| `--format FORMAT` | Export format: mermaid, excalidraw, png, coverage, bus-matrix |
| `--output PATH` | Output file path (default: stdout or format-specific) |
| `--domain TEXT` | Filter to specific domain(s), can be repeated |
| `--include-stubs` | Include stub concepts in export |
| `--include-deprecated` | Include deprecated concepts in export |

### `serve` - Launch interactive web UI

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project root |
| `--port INTEGER` | Port to run server on (default: 8741) |
| `--host TEXT` | Host to bind to (default: 127.0.0.1) |
| `--no-browser` | Don't open browser automatically |
| `--demo` | Run in demo mode with sample data |

### `diff` - Compare conceptual model against base git ref

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Path to dbt project root |
| `--base TEXT` | Base git ref to compare against (default: main) |
| `--format [human\|github]` | Output format (default: human) |

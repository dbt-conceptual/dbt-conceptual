# dbt-conceptual Diff Action

Generate conceptual model diffs for PR reviews. Automatically detects changes to your conceptual model and posts summaries to pull requests.

## Usage

```yaml
- uses: dbt-conceptual/dbt-conceptual/.github/actions/dbt-conceptual-diff@v1
  with:
    base: ${{ github.base_ref }}
    comment: true
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `base` | Base git ref to compare against (e.g., `main`, `origin/main`) | Yes | - |
| `format` | Output format: `markdown` or `json` | No | `markdown` |
| `comment` | Post diff as PR comment | No | `false` |
| `project-dir` | Path to dbt project directory | No | `.` |
| `python-version` | Python version to use | No | `3.11` |
| `version` | dbt-conceptual version to install | No | `latest` |

## Outputs

| Output | Description |
|--------|-------------|
| `has_changes` | Whether there are changes in the conceptual model (`true`/`false`) |
| `summary` | The diff summary in the specified format |

## Example Workflows

### Basic PR Review

```yaml
name: Conceptual Model Review
on:
  pull_request:
    paths:
      - 'models/**'
      - '**/conceptual.yml'

jobs:
  conceptual-diff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Required for git diff

      - uses: dbt-conceptual/dbt-conceptual/.github/actions/dbt-conceptual-diff@main
        with:
          base: ${{ github.base_ref }}
          comment: true
```

### Conditional Job

```yaml
jobs:
  conceptual-diff:
    runs-on: ubuntu-latest
    outputs:
      has_changes: ${{ steps.diff.outputs.has_changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - id: diff
        uses: dbt-conceptual/dbt-conceptual/.github/actions/dbt-conceptual-diff@main
        with:
          base: ${{ github.base_ref }}

  review-required:
    needs: conceptual-diff
    if: needs.conceptual-diff.outputs.has_changes == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Conceptual model changes require review!"
```

### JSON Output

```yaml
- id: diff
  uses: dbt-conceptual/dbt-conceptual/.github/actions/dbt-conceptual-diff@main
  with:
    base: main
    format: json

- name: Process diff
  run: |
    echo '${{ steps.diff.outputs.summary }}' | jq '.concepts.added'
```

## Features

- **Automatic job summary**: Writes diff to `$GITHUB_STEP_SUMMARY`
- **PR comments**: Updates or creates PR comment with changes
- **Change detection**: `has_changes` output for conditional workflows
- **Comment deduplication**: Uses marker to update existing comments instead of creating duplicates

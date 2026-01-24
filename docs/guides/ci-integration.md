# CI/CD Integration

Add dbt-conceptual validation to your continuous integration pipeline.

## Basic Validation

Add validation to your CI workflow:

```yaml
# .github/workflows/ci.yml
- name: Validate conceptual model
  run: dcm validate
```

Exit codes:
- `0` — No errors
- `1` — Validation errors found

## Strict Mode

Fail if any concepts or relationships are incomplete:

```yaml
- name: Validate (strict)
  run: dcm validate --no-drafts
```

The `--no-drafts` flag fails on:
- Concepts without implementing models
- Relationships without domain assignment
- Concepts missing domain assignment

## Job Summaries

Add formatted output to GitHub Actions job summaries:

```yaml
- name: Validate conceptual model
  run: |
    dcm validate --format markdown >> $GITHUB_STEP_SUMMARY
```

This renders validation results as formatted tables in the Actions UI.

## Conceptual Diff

Show what changed in pull requests:

```yaml
# .github/workflows/pr.yml
name: PR Validation

on:
  pull_request:
    branches: [main]

jobs:
  conceptual-diff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Required for diff

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dbt-conceptual
        run: pip install dbt-conceptual

      - name: Show conceptual changes
        run: |
          dcm diff --base origin/main --format markdown >> $GITHUB_STEP_SUMMARY
```

## Reusable GitHub Action

Use the official composite action:

```yaml
- name: Conceptual Model Diff
  uses: dbt-conceptual/dbt-conceptual/.github/actions/dbt-conceptual-diff@main
  with:
    base: origin/main
    format: markdown
    comment: true  # Post as PR comment
```

## Coverage Reports

Generate coverage reports in CI:

```yaml
- name: Generate coverage report
  run: |
    dcm export --type coverage --format markdown >> $GITHUB_STEP_SUMMARY
```

Or as an artifact:

```yaml
- name: Generate coverage HTML
  run: dcm export --type coverage --format html -o coverage.html

- name: Upload coverage report
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: coverage.html
```

## Pre-commit Hook

Add validation as a pre-commit hook:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-conceptual
        name: Validate conceptual model
        entry: dcm validate
        language: system
        pass_filenames: false
        files: conceptual\.yml$
```

## Example Complete Workflow

```yaml
name: Conceptual Model CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install dbt-conceptual

      - name: Validate conceptual model
        run: |
          echo "## Validation Results" >> $GITHUB_STEP_SUMMARY
          dcm validate --format markdown >> $GITHUB_STEP_SUMMARY

      - name: Show diff (PR only)
        if: github.event_name == 'pull_request'
        run: |
          echo "## Conceptual Changes" >> $GITHUB_STEP_SUMMARY
          dcm diff --base origin/main --format markdown >> $GITHUB_STEP_SUMMARY

      - name: Coverage report
        run: |
          echo "## Coverage" >> $GITHUB_STEP_SUMMARY
          dcm export --type coverage --format markdown >> $GITHUB_STEP_SUMMARY
```

## Exit Code Reference

| Command | Exit 0 | Exit 1 |
|---------|--------|--------|
| `dcm validate` | No errors | Has errors |
| `dcm validate --no-drafts` | Complete (no drafts/stubs) | Has drafts or errors |
| `dcm diff` | Always | Never |

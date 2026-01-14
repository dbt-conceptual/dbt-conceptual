# Branch Protection Rules

This document describes the recommended branch protection settings for the `main` branch.

## Required Status Checks

Configure these required status checks in GitHub Settings > Branches > Branch protection rules:

### Main Branch (`main`)

**Require status checks to pass before merging:**
- ✅ Require branches to be up to date before merging
- ✅ Status checks that are required:
  - `Required Checks`
  - `Lint & Type Check`
  - `Test (Python 3.9)`
  - `Test (Python 3.10)`
  - `Test (Python 3.11)`
  - `Test (Python 3.12)`

**Require pull request reviews before merging:**
- ✅ Require approvals: 1 (optional for solo projects)
- ✅ Dismiss stale pull request approvals when new commits are pushed

**Other Settings:**
- ✅ Require conversation resolution before merging
- ✅ Do not allow bypassing the above settings

## How to Configure

1. Go to: `https://github.com/feriksen-personal/dbt-conceptual/settings/branches`
2. Click "Add branch protection rule" or edit existing rule
3. Branch name pattern: `main`
4. Enable settings as documented above
5. Save changes

## CI/CD Workflows

The repository has two main workflows:

### 1. `ci.yml` - Continuous Integration
- Runs on: push to main, pull requests to main
- Jobs: test (matrix), lint

### 2. `pr.yml` - Pull Request Checks
- Runs on: pull request events (opened, synchronize, reopened)
- Jobs:
  - **changes**: Detect which files changed
  - **lint**: Ruff, Black, Mypy
  - **test**: Pytest across Python 3.9-3.12
  - **coverage-report**: Coverage comments on PR
  - **security**: Safety & Bandit scans
  - **pr-summary**: Summary comment on PR
  - **required-checks**: Gate for merge

## Features

### Automatic PR Comments
The PR workflow automatically posts comments with:
- ✅ Test results summary
- ✅ Coverage changes
- ✅ Check status table
- ✅ Updates on each push

### Security Scanning
- **safety**: Checks dependencies for known vulnerabilities
- **bandit**: Static analysis security testing for Python

### Optimizations
- **Concurrency control**: Cancels in-progress runs when new commits pushed
- **Path filters**: Only runs relevant checks based on changed files
- **Caching**: pip dependencies cached for faster runs

## Local Development

To run the same checks locally before pushing:

```bash
# Linting
ruff check .
black --check .
mypy src/dbt_conceptual

# Tests with coverage
pytest tests/ -v --cov

# Security (optional)
pip install safety bandit[toml]
safety check
bandit -r src/dbt_conceptual
```

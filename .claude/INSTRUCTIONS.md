# Claude Code Instructions

## Overview

This project uses a spec-driven development workflow. Specs define what to build, GitHub Issues track the work, and all changes go through PRs with human approval.

**Your working context is in `.claude/`** - specs, and this instructions file.

---

## First Time Setup

If the GitHub repo doesn't exist yet, run:
```bash
.claude/bootstrap.sh
```

This creates the repo, labels, milestones, and branch protection.

---

## Workflow Rules

### 0. CRITICAL: Never Commit to Main
- **NEVER commit directly to main branch**
- **ALWAYS create a feature branch first**
- **ALL changes must go through PR workflow**
- This applies to documentation, code, scripts - everything
- Exception: Only during initial bootstrap (before branch protection)

### 1. Issue-First Development
- **NEVER code without a GitHub Issue**
- Read the spec for the current phase
- Create Issues from the spec using `gh issue create`
- Reference spec section in issue body

### 2. Branch Strategy
```
main (protected)
  └── feature/<issue-number>-<short-description>
       └── fix/<issue-number>-<short-description>
```

Examples:
- `feature/1-add-pr-workflow`
- `feature/5-devcontainer`
- `fix/12-update-workflow-docs`

### 3. Pre-Commit Checklist
Before ANY commit:
```bash
# Lint shell scripts
shellcheck scripts/*.sh scripts/**/*.sh 2>/dev/null || true

# Lint YAML
yamllint .github/workflows/*.yml .yamllint.yml 2>/dev/null || true

# Check JSON
find . -name "*.json" -exec python -m json.tool {} \; >/dev/null

# Ensure scripts are executable
find . -name "*.sh" -exec chmod +x {} \;
```

### 4. Commit Messages
```
<type>(<scope>): <subject>

<body>

Closes #<issue-number>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(devcontainer): add GitHub Codespaces support`
- `docs(readme): add quick start guide`
- `chore(ci): add shellcheck to PR workflow`

### 5. Pull Request Process
```bash
# Create PR
gh pr create --title "feat: <description>" --body "Closes #<issue>"

# Check status
gh pr checks

# STOP - Wait for human approval
# NEVER merge without approval
```

### 6. Post-Merge Workflow
**IMMEDIATELY after PR is merged:**

See [POST_MERGE_CHECKLIST.md](.claude/POST_MERGE_CHECKLIST.md) for full details.

```bash
# 1. Pull latest changes
git checkout main
git pull

# 2. Update STATUS.md
# - Mark completed tasks with ✅
# - Update "Current Phase" if phase is complete
# - Update "Next Steps" section
# - Update "Last Updated" date

# 3. Commit status update
git add .claude/STATUS.md
git commit -m "docs(status): update progress after PR #<number>

Updates STATUS.md to reflect completion of <task description>."
git push

# This keeps STATUS.md in sync and provides continuity across sessions
```

---

## Working Through Phases

### Current Status
**Check STATUS.md first:** `cat .claude/STATUS.md` or run `.claude/check-status.sh`

Also check milestones: `gh issue list --milestone "Phase 00: Bootstrap"`

### Phase Order
1. `00_bootstrap.md` - Repo setup, CI, templates
2. `01_project_structure.md` - Devcontainer, common.sh
3. `02_azure_provisioning.md` - Azure CLI scripts
4. `03_database_configuration.md` - Schemas, users, CT
5. `04_seed_data.md` - Baseline data
6. `05_delta_scripts.md` - Change simulation
7. `06_utilities.md` - Reset, verify scripts
8. `07_databricks_integration.md` - Lakeflow setup
9. `08_documentation_polish.md` - Final docs

### Starting a Phase
```bash
# 0. Check current status
cat .claude/STATUS.md

# 1. Read the spec
cat .claude/specs/XX_name.md

# 2. Update STATUS.md - mark phase as "IN PROGRESS"
# Create a feature branch for the STATUS.md update
git checkout -b fix/<issue-num>-update-status
# Edit .claude/STATUS.md to update current phase
# Commit and create PR for status update

# 3. Create issues for that phase
gh issue create --title "..." --label "enhancement,phase-XX" --milestone "Phase XX: Name"

# 4. Work each issue - ALWAYS on a feature branch
git checkout -b feature/<issue-num>-<desc>
# ... implement ...
git add . && git commit -m "feat(scope): description

Closes #<issue>"
git push -u origin HEAD
gh pr create
# WAIT for approval

# 5. After PR merged - Update STATUS.md (see "Post-Merge Workflow")
```

---

## Quick Reference

```bash
# Check project status
cat .claude/STATUS.md
./.claude/check-status.sh

# List open issues
gh issue list

# List issues for current phase
gh issue list --milestone "Phase 00: Bootstrap"

# Create issue
gh issue create --title "Title" --body "Description" --label "enhancement"

# Create branch
git checkout -b feature/42-short-description

# Create PR
gh pr create --fill

# Check PR status
gh pr checks

# View PR
gh pr view --web
```

---

## Important Notes

- **NEVER commit directly to main** - always use feature/fix branches and PRs
- **Human (F) must approve all PRs** - never merge yourself
- **Always update STATUS.md after PR merge** - this ensures continuity across container rebuilds and sessions
- If unsure about spec details, ask via Issue comment
- Keep PRs focused - one issue per PR
- Write tests alongside implementation
- Document as you go

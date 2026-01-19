# Post-Merge Checklist

Run this checklist **IMMEDIATELY** after every PR merge to maintain project continuity.

## Steps

### 1. Pull Latest Changes
```bash
git checkout main
git pull
```

### 2. Update STATUS.md
Open [.claude/STATUS.md](.claude/STATUS.md) and update:

- [ ] Mark completed task with ✅
- [ ] Update "Last Updated" date to today
- [ ] If issue closes a phase, update "Current Phase" section
- [ ] Update "Next Steps" section with next tasks
- [ ] Add any relevant notes about the work completed

### 3. Commit Status Update
```bash
git add .claude/STATUS.md
git commit -m "docs(status): update progress after PR #<number>

Updates STATUS.md to reflect completion of <brief task description>."
git push
```

### 4. Verify Update
```bash
# Quick check that status is updated
cat .claude/STATUS.md
```

## Why This Matters

**STATUS.md provides continuity across:**
- Container rebuilds (local or Codespaces)
- Different Claude Code sessions
- Context switches (you leave and come back later)
- Handoffs between human and AI

Without this discipline, we lose track of progress and may duplicate work or miss tasks.

## Template for STATUS.md Updates

When marking a phase section:
```markdown
### Phase XX: Name ✅
- [x] Task description (#issue-number)
- [x] Another task (#issue-number)
```

When updating Next Steps:
```markdown
## Next Steps

### Phase XX: Name
Status: **IN PROGRESS** | **READY TO START** | **BLOCKED** (reason)

Tasks to create:
1. Description
2. Description
```

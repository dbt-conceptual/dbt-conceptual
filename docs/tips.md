# Tips & Best Practices

Practical advice from the field. These aren't rules — they're patterns that tend to work.

---

## Adoption

**Start with the domain that hurts most.**
Don't pick the easiest domain to prove the tool works. Pick the one that causes the most confusion, the most incidents, the most "who owns this?" questions. That's where the value is clearest.

**Use UNKNOWN explicitly.**
When you don't know the owner or domain, don't leave fields blank — use `UNKNOWN` as a placeholder. Gaps should be visible, not hidden. You can search for UNKNOWN later to find what needs attention.

```yaml
concepts:
  mystery_table:
    domain: UNKNOWN
    owner: UNKNOWN
    description: "TODO: needs documentation"
```

**Don't wait for 100% coverage.**
80% coverage that's maintained is better than 100% coverage that's planned but never finished. Ship what you have, iterate from there.

**Tag models as you touch them.**
Don't try to tag everything at once. When you're already in a model for other work, add the `meta.concept` tag. Coverage grows organically.

---

## Day-to-Day Workflow

**Run `dbc validate` locally before pushing.**
Faster feedback than waiting for CI. Catches issues before they become PR comments.

```bash
dbc validate
```

**Add "Concept tagged?" to your PR checklist.**
Make it part of the review process. Reviewers can check for `meta.concept` on new models the same way they check for tests.

**Export coverage to GitHub job summaries.**
Makes progress visible without extra tooling:

```yaml
- name: Coverage
  run: |
    echo "## Conceptual Model Coverage" >> $GITHUB_STEP_SUMMARY
    dbc export --type coverage --format markdown >> $GITHUB_STEP_SUMMARY
```

**Use `dbc serve --demo` to explore.**
Want to see the UI without setting up a project? The demo flag loads sample data:

```bash
dbc serve --demo
```

---

## Common Pitfalls

**Don't skip descriptions.**
A concept without a description is just a name. The description is where the shared understanding lives. Even a one-sentence description is better than none.

```yaml
# Not useful
concepts:
  customer:
    domain: party

# Useful
concepts:
  customer:
    domain: party
    description: |
      A person or company that purchases products.
      Internal test accounts are excluded.
```

**Don't let stubs pile up.**
Stubs are placeholders, not permanent residents. If you run `sync` and then ignore the stubs it creates, you're just accumulating debt. Set a cadence — maybe one domain per sprint — to convert stubs to complete concepts.

**Don't enforce too early.**
Start with warnings (`orphan_models: warn`), not errors. Let the team see the gaps, understand the tool, build coverage. Then tighten enforcement once you're past 60-70% coverage. Enforcement on day one just generates resentment.

**Don't model everything.**
Not every staging table needs a concept. Focus on the gold layer — the models that business users see and ask questions about. Silver and bronze can follow later if needed.

---

## Working with Governance

**Align taxonomy.yml with your governance office.**
If your organization has standard confidentiality levels, regulatory tags, or classification schemes, use them. Don't invent your own vocabulary — align with what already exists. This makes the handoff smoother and avoids "but we call it X, not Y" debates.

**Use @mentions to keep governance in the loop.**
When you update taxonomy.yml or make significant changes to concept ownership, add governance team members as PR reviewers or mention them in comments:

```yaml
# In your PR description or conceptual.yml comments
# cc: @data-governance-team
```

They stay informed without needing to attend meetings or check dashboards.

**Share coverage reports — visibility builds trust.**
Governance teams often feel blind to what's happening in the codebase. A weekly or monthly coverage report — even just a screenshot in Slack — shows progress and builds credibility. "We're at 72% coverage, up from 58% last month" is concrete.

**Invite early review, not late approval.**
Don't build your entire conceptual model and then ask governance to approve it. Share it when you have 5-10 concepts defined. Early feedback is easier to incorporate than late rework.

**Remember: governance owns policy, you own implementation.**
dbt-conceptual doesn't replace the governance office — it makes their job easier by capturing metadata at the source. They still own the taxonomy definitions, the classification policies, the compliance requirements. You're just making sure that information flows into the codebase where it can be validated automatically.

---

## Quick Reference

| Situation | Tip |
|-----------|-----|
| New project | Start with conceptual.yml before building models |
| Existing project | Tag models as you touch them, use stubs for the rest |
| Not sure who owns it | Use `UNKNOWN`, fix later |
| CI failing on everything | Switch to `warn` mode, fix incrementally |
| Governance asking questions | Share coverage reports, invite them to review PRs |
| Team not adopting | Add to PR checklist, make it visible |
| Too many stubs | One domain per sprint until caught up |
| Want to explore | `dbc serve --demo` |

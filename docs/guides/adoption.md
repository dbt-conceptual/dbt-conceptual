# Adopting in Existing Projects

If you have a dbt project with models already in place, you don't need to stop everything to add conceptual structure. Here's an approach that works incrementally.

<figure>
  <img src="../assets/workflow-brownfield-adoption.svg" alt="Progressive brownfield adoption timeline" />
</figure>

---

## The General Idea

Rather than trying to document everything at once:

1. **Tag some models** — Add `meta.concept` to models you know well
2. **Generate stubs** — Sync creates placeholders for referenced concepts
3. **Enrich the stubs** — Add domain, owner, description
4. **Expand gradually** — Tag more models, repeat
5. **Tighten slowly** — Increase CI enforcement as coverage improves

This takes weeks, not days — and that's fine. The goal is sustainable progress.

---

## Step 1: Tag Some Models

Start by adding `meta.concept` tags to a few existing models. Pick the ones you understand best:

```yaml
# models/marts/schema.yml
models:
  - name: dim_customer
    meta:
      concept: customer

  - name: fct_orders
    meta:
      concept: order

  - name: dim_product
    meta:
      concept: product
```

You're declaring: "this model implements the `customer` concept." The concept doesn't need to exist in `conceptual.yml` yet — that comes next.

---

## Step 2: Generate Stubs

Run sync to create placeholders for the concepts you've referenced:

```bash
dbc sync
```

```
Scanning dbt project...
Found 3 models with meta.concept tags

Created 3 concept stubs:
  - customer (referenced by dim_customer)
  - order (referenced by fct_orders)
  - product (referenced by dim_product)

Run 'dbc status' to see coverage
```

The tool creates stubs in `conceptual.yml` for any concept that's referenced in a `meta.concept` tag but not yet defined. These stubs need a domain and owner to be considered complete.

---

## Step 3: Check Your Status

```bash
dbc status
```

```
Coverage Summary
────────────────────────────────────
Gold layer:    3/50 models   (6%)
Silver layer:  0/80 models   (0%)

Concepts: 3 total
  - 0 complete (need domain assignment)
  - 3 stubs (need domain, owner)

Recommendations:
  - Add domain and owner to concept stubs
  - Tag more gold layer models with meta.concept
```

Don't be discouraged by low numbers — they'll improve as you work through the backlog. The point is: now you can see where you're starting from.

---

## Step 4: Pick Your First Focus

Not all models are equally important. Consider starting with:

| Priority | Why |
|----------|-----|
| Executive dashboards | High visibility, people ask questions about these |
| GDPR/PII-related data | Compliance exposure |
| Core dimensions (customer, product) | Foundation for everything else |
| Recent incidents | Areas where confusion caused problems |

**Pick one domain.** Maybe it's Customer. Maybe it's Order. Whatever has the most pressure or visibility right now.

---

## Step 5: Enrich the Stubs

Open `models/conceptual/conceptual.yml`. You'll see stubs like:

```yaml
concepts:
  customer:
    name: "customer"
    domain: null
    owner: null
```

Enrich them with real information:

```yaml
domains:
  party:
    name: "Party"
    owner: commercial-analytics

concepts:
  customer:
    name: "Customer"
    domain: party
    owner: commercial-analytics
    description: |
      A person or company that purchases products.
      
      Includes both B2C and B2B customers.
      Internal test accounts are excluded.
```

Check your progress:

```bash
dbc status
```

```
party: 1/1 complete ✓
```

One concept complete. That's real progress.

---

## Step 6: Enable CI (Gently)

Start with warnings rather than errors:

```yaml
# dbt_project.yml
vars:
  dbt_conceptual:
    validation:
      orphan_models: warn
      unimplemented_concepts: warn
```

Add validation to your CI pipeline:

```yaml
- name: Validate conceptual model
  run: dbc validate
  continue-on-error: true  # Don't block merges yet
```

This gives you visibility into gaps without disrupting the team's workflow.

---

## Step 7: Expand Week by Week

Set a sustainable pace. Tag more models, create more stubs, enrich them:

| Week | Focus | Coverage |
|------|-------|----------|
| 1 | customer, order, product | 3 concepts |
| 2 | payment, order_line | 5 concepts |
| 3 | warehouse, campaign | 7 concepts |
| 4 | lead, remaining gold models | 10+ concepts |

Track progress with:

```bash
dbc export --type coverage --format markdown
```

Share this with your team. Visible progress helps maintain momentum.

---

## Step 8: Tighten Enforcement Gradually

As coverage improves, you can increase strictness:

**Month 1: Just warnings**
```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: warn
```

**Month 2: Error on orphans in gold layer**
```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: error
```

**Month 3: Require descriptions too**
```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: error
      missing_descriptions: warn
```

This way, the team has time to adapt rather than facing a wall of failures on day one.

---

## Handling Unknowns

Sometimes you'll encounter models where you're not sure who owns them or what domain they belong to. Rather than leaving fields blank, consider using explicit placeholders:

```yaml
concepts:
  mystery_table:
    domain: party
    owner: UNKNOWN
    description: "TODO: needs documentation"
```

Why this helps:
- Gaps are visible, not hidden
- You can search for "UNKNOWN" to find what needs attention
- CI can be configured to warn on UNKNOWN values
- It's more honest than pretending something is documented when it isn't

---

## Making It Stick

A few things that help with team adoption:

**PR checklist** — Add "Concept tagged?" to your pull request template

**Code review** — Reviewers can check for `meta.concept` on new models

**Sprint goals** — "Party domain 100% covered by Friday" gives a concrete target

**Celebrate wins** — Share coverage milestones in your team channel

The goal is making it part of the normal workflow, not a separate documentation task.

---

## Realistic Timeline

| Timeframe | What to Expect |
|-----------|----------------|
| Day 1 | First few models tagged, stubs created |
| Week 1 | Priority domain enriched |
| Week 2 | CI warnings enabled |
| Month 1 | Gold layer 60% covered |
| Month 2 | CI errors enabled |
| Month 3 | 80%+ coverage |

This isn't fast, but it's sustainable. The alternative — a big-bang documentation effort — rarely succeeds.

---

## Common Challenges

| Challenge | What Helps |
|-----------|------------|
| "We can't cover everything" | You don't need to. One domain at a time. |
| "CI is failing on everything" | Start with warnings, not errors. |
| "UNKNOWN keeps piling up" | Set deadlines, track in sprints. |
| "Team isn't adopting" | Add it to the PR checklist, make it visible. |
| "Nobody has time" | 15 minutes per concept. It's less than you think. |

---

## What Success Looks Like

After a few months:

- New team members can read the concepts to understand the domain
- CI catches drift before it merges
- Coverage improves automatically as part of normal development
- The whiteboard photo in Confluence finally becomes irrelevant

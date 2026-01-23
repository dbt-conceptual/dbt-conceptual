# Validation & Messages Guide

dbt-conceptual validates your conceptual model against your dbt project, surfacing issues and drift in a unified Messages panel.

---

## How It Works

1. **Startup** — The UI loads `conceptual.yml` and renders your defined concepts and relationships. No validation runs yet.

2. **Sync** — Click the `↻` button to validate against your dbt project. This:
   - Re-parses `conceptual.yml`
   - Scans dbt project folders for models
   - Checks references and mappings
   - Creates ghost concepts for missing references
   - Populates the Messages panel

3. **Fix & Repeat** — Address issues in YAML or via the UI, then sync again.

### What's Persisted vs Transient

| Item | Persisted | Notes |
| ---- | --------- | ----- |
| Concepts | ✓ | Saved to `conceptual.yml` |
| Relationships | ✓ | Saved to `conceptual.yml` |
| Domains | ✓ | Saved to `conceptual.yml` |
| Ghost concepts | ✗ | Created fresh on each sync |
| Validation errors | ✗ | Recalculated on each sync |
| Messages | ✗ | Cleared and repopulated on sync |

**Key insight:** The canvas always reflects the current state of `conceptual.yml`. Ghost concepts and validation messages only appear after clicking sync — they're not saved to the file. Close and reopen the UI? You'll see your saved model, nothing more. Click sync? You'll see the current reality.

---

## The Messages Panel

The Messages panel lives on the left side of the canvas.

### Collapsed State

![Messages bar collapsed](assets/messages-bar-collapsed.png)

From top to bottom:
- `▶` Expand button
- `↻` Sync button
- Message count (if any)
- Status badge (only if errors or warnings)

**Badge logic:**
| State | Badge |
| ----- | ----- |
| Has errors | Red `!` |
| Warnings only | Amber `!` |
| Info only | No badge, just count |
| Empty | Nothing |

### Expanded State

![Messages panel expanded](assets/messages-panel.png)

- **Header** — "Messages" title, sync button, collapse button
- **Filters** — Three independent toggles (error, warning, info). Click to show/hide each type.
- **Message list** — Scrollable list of all messages matching active filters

---

## Message Types

### Errors ⊘

Critical issues that indicate broken references or invalid configuration.

| Issue | Message | Resolution |
| ----- | ------- | ---------- |
| Missing concept reference | "Relationship 'X' references non-existent concept 'Y'" | Define the concept in `conceptual.yml` or fix the relationship |
| Duplicate concept name | "Duplicate concept name 'customer'" | Concept names must be globally unique — rename one |
| Duplicate relationship | "Duplicate relationship 'customer:places:order'" | Remove the duplicate from `conceptual.yml` |
| YAML parse error | "Critical error: Unable to parse conceptual.yml" | Fix YAML syntax errors |

### Warnings ⚠

Issues that don't break the model but indicate potential problems.

| Issue | Message | Resolution |
| ----- | ------- | ---------- |
| Model not found | "Model 'dim_payment' not found in project" | Create the model or remove the reference |
| Stub created | "Stub created for concept 'product_erp'" | Enrich the stub with domain, owner, definition |
| Empty domain | "Domain 'product' has no concepts" | Add concepts to the domain or remove it |

### Info ℹ

Informational messages about successful operations.

| Event | Message |
| ----- | ------- |
| Sync complete | "Synced 12 concepts from conceptual.yml" |
| Model mapped | "Mapped 'dim_customer' → customer" |
| Relationship realized | "Mapped 'fact_orders' realizes customer:places:order" |

---

## Ghost Concepts

When a relationship references a concept that doesn't exist, a **ghost concept** appears on the canvas after sync.

![Ghost concept](assets/ghost-concept.png)

### Visual Treatment

- Dashed grey border
- Grey fill
- `?` prefix on name
- "undefined" as domain
- Red error badge

### Behavior

**Positioning:** Ghost appears near the first concept that references it (offset to the right).

**Selection:** Click to select. Property panel opens with editable fields.

**Editing:** Fill in name, domain, owner, definition. Click Save. Ghost becomes a real concept.

**Deletion:** Right-click → Delete. Ghost disappears from canvas. If you sync again without fixing the underlying relationship, the ghost reappears.

**Key insight:** Ghosts are persistent reminders. They keep coming back until you either:
- Define the concept (make it real)
- Remove the relationship that references it

---

## Property Panel for Invalid Items

### Ghost Concept Selected

![Property panel - ghost concept](assets/property-panel-ghost.png)

- Status indicator shows: "Undefined — referenced by N relationships"
- All fields are editable
- Save converts ghost to real concept (writes to `conceptual.yml`)
- Cancel closes panel without changes

### Invalid Relationship Selected

![Property panel - invalid relationship](assets/property-panel-invalid-rel.png)

- Status indicator shows: "Invalid — target concept not defined"
- Fields are editable
- `to` field shown in red if target doesn't exist
- Save validates first — fails if references still broken
- On save failure: error message "Unable to save", panel stays open

---

## Canvas Validation States

### Concept States

| State | Visual | Meaning |
| ----- | ------ | ------- |
| Valid | Solid border, model count badge | Fully defined with implementing models |
| Draft | Dashed grey border | Missing domain or zero implementing models |
| Stub | Dashed orange border, amber badge | Auto-generated, needs enrichment |
| Ghost | Dashed grey fill, `?` icon, red badge | Referenced but not defined |
| Error | Red border, red badge | Duplicate name or other error |
| Warning | Amber border, amber badge | Model not found in project |

![Concept states](assets/concept-states.png)

### Relationship States

| State | Visual | Meaning |
| ----- | ------ | ------- |
| Valid | Solid grey line | Both endpoints exist |
| Invalid | Red dashed line, red label | Points to ghost concept |

![Relationship states](assets/relationship-states.png)

---

## Workflow Examples

### Fixing a Missing Concept Reference

1. Run sync — ghost concept appears, error message in panel
2. Option A: Edit ghost in property panel → Save → becomes real concept
3. Option B: Add concept to `conceptual.yml` manually → Run sync → ghost disappears

### Resolving a Duplicate Name

1. Run sync — both concepts show red error badge
2. Rename one concept in `conceptual.yml` (names must be globally unique)
3. Run sync — error clears

### Cleaning Up After Model Rename

1. Run sync — warning: "Model 'old_name' not found"
2. Update `meta.concept` tag in your dbt model's YAML to point to new model
3. Run sync — warning clears, info message confirms mapping

---

## CLI Validation

The same validation logic runs via CLI:

```bash
# Basic validation
dcm validate

# Fail if any drafts or stubs exist
dcm validate --no-drafts

# Output as markdown (for CI summaries)
dcm validate --format markdown
```

**Exit codes:**
| Code | Meaning |
| ---- | ------- |
| 0 | Success (no errors) |
| 1 | Validation errors found |
| 2 | Drafts/stubs found (with `--no-drafts`) |

---

## Design Tokens

For UI customization or theming, these CSS variables control validation colors:

```css
:root {
  /* Validation status */
  --status-error: #dc2626;
  --status-error-light: #fef2f2;
  --status-warning: #d97706;
  --status-warning-light: #fffbeb;
  --status-info: #2563eb;
  --status-info-light: #eff6ff;
  
  /* Ghost concept */
  --ghost-bg: #f3f4f6;
  --ghost-border: #9ca3af;
  --ghost-text: #6b7280;
}
```

---

## Summary

| Action | Result |
| ------ | ------ |
| App startup | Canvas shows defined model, messages panel empty |
| Click sync | Validates, creates ghosts, populates messages |
| Edit ghost → Save | Ghost becomes real concept |
| Delete ghost | Disappears (reappears on next sync if not fixed) |
| Save invalid relationship | Fails with error message |
| Fix issue → Sync | Message clears |

The messages panel is your feedback loop. Sync early, sync often.

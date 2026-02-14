# Validation Codes

Reference for all validation messages.

---

## Overview

When you run `dbc validate`, the tool checks for issues and reports them with codes.

```bash
dbc validate
```

```
Validation Issues
════════════════════════════════════════════
✗ ERRORS
  [E002] Relationship 'order:contains:line_item' references non-existent concept 'line_item'

⚠ WARNINGS
  [W101] Model 'mart_revenue' is not linked to any concept
  [W102] Concept 'refund' has no implementing models

ℹ INFO
  [I001] Stub concept 'inventory' needs enrichment: missing domain, owner, definition

Summary: 1 errors, 2 warnings, 1 info
```

---

## Error Codes

### E002: Unknown Concept Reference

**Message:** `Relationship '{relationship}' references non-existent concept '{concept}'`

**Meaning:** A relationship points to a concept that doesn't exist in `conceptual.yml`.

**Fix:** Either:
- Define the missing concept
- Fix the typo in the relationship
- Remove the relationship

**Configure:** This is always an error (cannot be disabled).

---

### E201: Incomplete Concept (--no-drafts)

**Message:** `{Status} concept '{concept}' needs enrichment: missing {fields}`

**Meaning:** When `--no-drafts` is used, stub or draft concepts with missing domain, owner, or definition are treated as errors.

**Fix:** Add the missing fields to the concept in `conceptual.yml`.

**Configure:** Only active when `--no-drafts` flag is used.

---

### E202: Incomplete Relationship (--no-drafts)

**Message:** `Stub relationship '{relationship}' needs enrichment: missing {fields}`

**Meaning:** When `--no-drafts` is used, stub relationships are treated as errors.

**Fix:** Ensure both endpoint concepts are at least draft status.

**Configure:** Only active when `--no-drafts` flag is used.

---

## Warning Codes

### W001: Unknown Domain Reference

**Message:** `Concept '{concept}' references unknown domain '{domain}'`

**Meaning:** A concept belongs to a domain that doesn't exist in the `domains` section.

**Fix:** Either:
- Define the missing domain
- Fix the typo in the concept's domain field

**Configure:** This is always a warning.

---

### W101: Orphan Model

**Message:** `Model '{model}' is not linked to any concept`

**Meaning:** A dbt model in the gold layer doesn't have a `meta.concept` tag.

**Fix:** Add a concept tag to the model:

```yaml
models:
  - name: mart_revenue
    meta:
      concept: revenue
```

**Configure:**
```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: warn  # or error, or ignore
```

---

### W102: Unimplemented Concept

**Message:** `Concept '{concept}' has no implementing models`

**Meaning:** A concept is defined but no dbt models reference it via `meta.concept`.

**Fix:** Either:
- Tag a model with `meta.concept: {concept}`
- Remove the concept if it's not needed
- Accept it as a draft (concept defined before implementation)

**Configure:**
```yaml
vars:
  dbt_conceptual:
    validation:
      unimplemented_concepts: warn  # or error, or ignore
```

---

### W104: Missing Definition

**Message:** `Concept '{concept}' is missing a definition` or `Relationship '{relationship}' is missing a definition`

**Meaning:** A non-stub concept or relationship doesn't have a `definition` field.

**Fix:** Add a definition:

```yaml
concepts:
  customer:
    definition: |
      A person or company that purchases products.
```

**Configure:**
```yaml
vars:
  dbt_conceptual:
    validation:
      missing_definitions: warn  # or error, or ignore (default: ignore)
```

---

## Info Codes

### I001: Stub Concept

**Message:** `Stub concept '{concept}' needs enrichment: missing {fields}`

**Meaning:** A concept in stub or draft status is missing domain, owner, or definition.

**Fix:** Add the missing fields. A concept needs a domain to progress from stub to draft.

**Configure:** This is always informational (unless `--no-drafts` is used, which promotes it to E201).

---

### I002: Stub Relationship

**Message:** `Stub relationship '{relationship}' needs enrichment: missing {fields}` or `Stub relationship '{relationship}' has stub/ghost endpoint concepts`

**Meaning:** A relationship has endpoint concepts that are ghosts or stubs, or it is missing a definition.

**Fix:** Ensure both endpoint concepts exist and have domains assigned.

**Configure:** This is always informational (unless `--no-drafts` is used, which promotes it to E202).

---

## Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| 0 | Validation passed (no errors) |
| 1 | Validation failed (has errors) |

Warnings and info messages don't cause a non-zero exit code.

---

## Suppressing Specific Checks

To ignore specific rules:

```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: ignore
      missing_definitions: ignore
```

---

## Layer Overrides

You can set different severities for the gold layer:

```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: warn
    validation_overrides:
      gold:
        orphan_models: error    # Stricter for gold layer
```

---

## CI Usage

Fail CI on validation errors:

```yaml
- name: Validate
  run: dbc validate
```

Show warnings but don't fail:

```yaml
- name: Validate
  run: dbc validate
  continue-on-error: true
```

Strict mode (fail on drafts/stubs):

```yaml
- name: Validate (strict)
  run: dbc validate --no-drafts
```

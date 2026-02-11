# Validation Codes

Reference for all validation messages.

---

## Overview

When you run `dbc validate`, the tool checks for issues and reports them with codes.

```bash
dbc validate
```

```
Validation Results
────────────────────────────────────
✗ DCM001: Orphan model 'mart_revenue' in gold layer
✗ DCM002: Concept 'refund' has no implementing models
⚠ DCM003: Concept 'customer' missing description

Errors: 2
Warnings: 1
```

---

## Error Codes

### DCM001: Orphan Model

**Message:** `Orphan model '{model}' in {layer} layer`

**Meaning:** A dbt model doesn't have a `meta.concept` tag.

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
      orphan_models: warn  # or ignore
```

---

### DCM002: Unimplemented Concept

**Message:** `Concept '{concept}' has no implementing models`

**Meaning:** A concept is defined but no dbt models reference it.

**Fix:** Either:
- Tag a model with `meta.concept: {concept}`
- Remove the concept if it's not needed
- Accept it as a draft (concept defined before implementation)

**Configure:**
```yaml
vars:
  dbt_conceptual:
    validation:
      unimplemented_concepts: warn  # or ignore
```

---

### DCM003: Missing Description

**Message:** `Concept '{concept}' missing description`

**Meaning:** A concept doesn't have a description.

**Fix:** Add a description:

```yaml
concepts:
  customer:
    description: |
      A person or company that purchases products.
```

**Configure:**
```yaml
vars:
  dbt_conceptual:
    validation:
      missing_descriptions: warn  # or ignore
```

---

### DCM004: Invalid Concept Reference

**Message:** `Relationship '{relationship}' references undefined concept '{concept}'`

**Meaning:** A relationship points to a concept that doesn't exist.

**Fix:** Either:
- Define the missing concept
- Fix the typo in the relationship
- Remove the relationship

**Configure:** This is always an error (can't be disabled).

---

### DCM005: Invalid Domain Reference

**Message:** `Concept '{concept}' references undefined domain '{domain}'`

**Meaning:** A concept belongs to a domain that doesn't exist.

**Fix:** Either:
- Define the missing domain
- Fix the typo in the concept
- Change to a valid domain

**Configure:** This is always an error (can't be disabled).

---

### DCM006: Duplicate Concept

**Message:** `Duplicate concept key '{concept}'`

**Meaning:** Two concepts have the same key in `conceptual.yml`.

**Fix:** Rename one of the concepts.

**Configure:** This is always an error.

---

### DCM007: Duplicate Relationship

**Message:** `Duplicate relationship '{from}:{name}:{to}'`

**Meaning:** The same relationship is defined twice.

**Fix:** Remove the duplicate.

**Configure:** This is always an error.

---

### DCM008: Ghost Concept

**Message:** `Ghost concept '{concept}' referenced by model '{model}'`

**Meaning:** A model's `meta.concept` references a concept that doesn't exist.

**Fix:** Either:
- Define the concept in `conceptual.yml`
- Run `dbc sync` to create a stub automatically
- Fix the typo in the model

**Configure:** This is always an error.

---

### DCM009: Invalid Cardinality

**Message:** `Invalid cardinality '{value}' on relationship '{relationship}'`

**Meaning:** Cardinality must be `1:1`, `1:N`, or `N:1`.

**Fix:** Use a valid cardinality value.

**Configure:** This is always an error.

---

### DCM010: Circular Relationship

**Message:** `Circular relationship: concept '{concept}' relates to itself`

**Meaning:** A relationship has the same concept as `from` and `to`.

**Fix:** Self-referential relationships should use a different pattern (e.g., `employee reports_to manager` where both are different concepts).

**Configure:** This is a warning by default.

---

## Warning Codes

### DCM101: Stub Concept

**Message:** `Concept '{concept}' is a stub (no domain assigned)`

**Meaning:** A concept doesn't have a domain.

**Fix:** Assign a domain:

```yaml
concepts:
  mystery:
    domain: party  # Add this
```

**Configure:**
```yaml
vars:
  dbt_conceptual:
    validation:
      stub_concepts: warn  # or ignore
```

---

### DCM102: Draft Concept

**Message:** `Concept '{concept}' is a draft (no implementing models)`

**Meaning:** A concept has a domain but no models implement it.

**Fix:** Tag models or accept it as work in progress.

**Configure:** This is informational by default.

---

### DCM103: Deprecated Concept in Use

**Message:** `Model '{model}' references deprecated concept '{concept}'`

**Meaning:** A model references a concept marked with `replaced_by`.

**Fix:** Update the model to use the replacement concept.

**Configure:**
```yaml
vars:
  dbt_conceptual:
    validation:
      deprecated_usage: warn  # or error
```

---

## Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| 0 | Validation passed (no errors) |
| 1 | Validation failed (has errors) |

Warnings don't cause a non-zero exit code.

---

## Suppressing Specific Checks

To ignore specific rules:

```yaml
vars:
  dbt_conceptual:
    validation:
      orphan_models: ignore
      missing_descriptions: ignore
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

Strict mode (fail on warnings too):

```yaml
- name: Validate (strict)
  run: dbc validate --strict
```

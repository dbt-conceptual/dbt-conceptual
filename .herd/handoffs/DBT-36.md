# Handoff: DBT-36 — fix(parser): decompose validate_and_sync and add defensive parsing

## What was done
- **Decomposed `validate_and_sync`** (was 180+ lines) into 5 private methods:
  - `_make_msg()` — creates validation messages with proper `MessageSeverity` and `ElementType` typing (no more `# type: ignore`)
  - `_check_ghost_concepts()` — creates ghost concepts for missing relationship endpoints
  - `_check_duplicate_concepts()` — detects duplicate concept names
  - `_check_duplicate_relationships()` — detects duplicate relationships
  - `_check_empty_domains()` — warns about domains with no concepts
  - `_make_sync_summary()` — generates sync info message
- **Added defensive key access** in `ConceptualModelParser.parse()`:
  - Validates `relationships` is a list (not a dict)
  - Validates each relationship entry is a mapping (not a string)
  - Uses `.get()` for `from` and `to` keys with clear `ValueError` messages including the index
- **Removed `# type: ignore` comments** by importing `MessageSeverity` from `state.py` and defining `ElementType` as a module-level `Literal` alias
- **Added 6 edge case tests**:
  - `test_parse_relationships_as_dict_raises_error`
  - `test_parse_relationship_missing_from_key_raises_error`
  - `test_parse_relationship_missing_to_key_raises_error`
  - `test_parse_relationship_not_a_mapping_raises_error`
  - `test_parse_relationship_missing_both_keys_raises_error`
  - `test_parse_relationship_error_includes_index`

## What to verify (for Wardenstein)
- All 18 parser tests pass (12 existing + 6 new)
- Full test suite (224 tests) passes
- Parser coverage is 83% (above 80% gate)
- Error messages include: what went wrong, what was expected, and where to look (index)
- `validate_and_sync` still produces identical output (behavior-preserving refactor)

## What to document (for Shakesquill)
- No user-facing changes — this is an internal refactor
- Error messages for malformed `conceptual.yml` are now clearer (previously would crash with `KeyError`)

## Open questions for Architect
- None — straightforward decomposition and defensive parsing

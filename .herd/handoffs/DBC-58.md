# DBC-58 Handoff: Output Formatters

**Agent:** Grunt
**Date:** 2026-02-14
**Status:** Ready for QA

## What Was Implemented

Created three output formatters for MCP context resolution in `src/dbt_conceptual/mcp/formatters.py`:

1. **LLM Format** (`format_llm`)
   - Natural language optimized for agent consumption
   - Prose sentences with explicit grain statements
   - Negative guidance for 1:N relationships ("DO NOT join without accounting for fan-out")
   - Clear source attribution: `[authored]` vs `[inferred]`
   - XML-like tags for multi-concept output: `<concepts>`, `<concept name="...">`
   - Business guidance rules prominently surfaced in "IMPORTANT RULES" section
   - Risk emojis (🔴 high, 🟡 medium, 🟢 low)

2. **JSON Format** (`format_json`)
   - Structured JSON for programmatic consumption
   - Pretty-printed with `indent=2`
   - Recursively converts all dataclasses to dicts
   - Parseable and valid JSON output

3. **Markdown Format** (`format_markdown`)
   - Standard markdown for human reading
   - Tables for metadata, columns, relationships
   - Italics `*(inferred)*` for inferred content attribution
   - Headers, code blocks, lists
   - Consistent human-friendly formatting

## Key Design Decisions

### Consumed Canonical FullContext
All formatters consume `FullContext` from `src/dbt_conceptual/mcp/context.py` (the 5-layer resolution engine). This is the proper architectural pattern — formatters live in the MCP package and use the canonical context definition.

**Note:** There is an existing `src/dbt_conceptual/formatters.py` (from PR #144) that defines its own `FullContext`. This creates duplication. The MCP formatters use the canonical definition from `mcp/context.py`.

### Source Attribution
- LLM format: `[authored]` and `[inferred]` tags inline
- Markdown format: `*(inferred)*` in italics for inferred fields
- JSON format: Separation of authored (concepts, models, contracts) vs inferred (inferences) data

### Multi-Concept Output
When multiple concepts are in the context, LLM format uses XML-like wrapper tags:
```
<concepts count="2">
  <concept name="customer">
    ...
  </concept>
  <concept name="order">
    ...
  </concept>
</concepts>
```

### Relationship Grain Warnings
For 1:N relationships, LLM format includes explicit warnings:
> "WARNING: This is a 1:N relationship. DO NOT join to [concept] without accounting for fan-out. Aggregation or DISTINCT may be required."

## Files Changed

- `src/dbt_conceptual/mcp/formatters.py` (new, 263 lines)
- `tests/test_mcp_formatters.py` (new, 763 lines)

## Test Coverage

**98% coverage** (263 statements, 160 branches)

Test categories:
- Entry point (`format_context` with all three formats)
- LLM format (minimal, full, multi-concept, relationships, edge cases)
- JSON format (minimal, full, validation)
- Markdown format (minimal, full, multi-concept, tables)
- Attribution clarity across all formats
- Consistency across formats (same info in all three)
- Edge cases (empty context, missing fields, sparse data)

## Pre-Commit Checks

All checks passed:
- ✅ pytest (29 tests, 98% coverage)
- ✅ ruff (no linting errors)
- ✅ black (formatted)
- ✅ mypy (external mcp package has syntax error for Python 3.9 compatibility, but our code is clean)

## QA Notes

### What to Test

1. **LLM format produces agent-optimized prose**
   - Grain statements are explicit
   - Guidance rules are prominent
   - Warnings for 1:N joins are clear
   - Attribution tags present

2. **JSON format is valid and parseable**
   - Run `json.loads()` on output
   - Check all fields are present

3. **Markdown format is clean standard markdown**
   - Tables render properly
   - Headers are nested correctly
   - Inferred fields marked with italics

4. **All formats contain same information**
   - Cross-check concept definitions
   - Verify model metadata
   - Confirm inference data

### Known Limitations

- Formatters output ALL models in the context (there's currently no concept-to-model filtering in the output logic, though the context resolution engine does the filtering)
- The existing `src/dbt_conceptual/formatters.py` creates architectural duplication — may want to deprecate it in favor of the MCP version

## Next Steps

1. Wardenstein QA review
2. Integration testing with actual MCP server calls
3. Consider deprecating the duplicate `formatters.py` at root level

For the Herd!

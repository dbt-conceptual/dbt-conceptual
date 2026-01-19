# Collaboration Guidelines

## Communication Protocol

### When to Pause and Consult

**CRITICAL**: When encountering technical issues, architectural decisions, or design patterns, PAUSE and communicate with the user BEFORE implementing solutions.

The user is an architect with 30+ years of experience and may have:
- Established patterns to follow
- Architectural preferences
- Better solutions based on deep system knowledge
- Context that isn't visible in the code

### Examples of When to Pause:
1. **Mysterious/unexpected errors** - Like the duplicate key error we encountered
2. **Multiple solution approaches** - Present options rather than choosing
3. **Architectural decisions** - Database patterns, code organization, etc.
4. **Performance issues** - May have existing patterns or constraints
5. **Refactoring** - Discuss scope and approach first
6. **Breaking changes** - Get approval before proceeding

### Pattern: Pause → Discuss → Implement
1. Identify the problem clearly
2. Present 2-3 potential approaches (if obvious)
3. Ask for guidance/preferences
4. Implement the chosen solution

## Lessons Learned

### Orchestrator Pattern (Issue #40)
**Problem**: Multiple INSERT statements in one `run_query()` caused DuckDB parser confusion
**Solution**: User suggested orchestrator pattern - split into table-by-table sequential execution
**Takeaway**: User's architectural experience immediately identified the right pattern. Should have consulted earlier rather than debugging alone.

---
Last Updated: 2026-01-17

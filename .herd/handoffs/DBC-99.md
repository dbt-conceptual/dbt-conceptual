# DBC-99 Handoff: Remaining 8 Evidence Dashboards

**From**: Pikasso
**To**: Wardenstein
**Date**: 2026-02-10

## What Was Done

Created 8 Evidence.dev dashboard pages for the Herd MCP project:

1. **agents.md** — Agent performance tracking
   - Agent work summary with sessions, tokens, costs
   - QA pass rates by agent
   - Cost efficiency metrics (cost per line)
   - Model comparison by agent
   - Agent skillsets display
   - Work distribution analysis

2. **qa.md** — QA effectiveness metrics
   - Overall QA overview with first-pass rates
   - First-pass rate trend (30 days)
   - Findings by category (blocking/advisory/clean)
   - Findings by agent
   - Review rounds distribution
   - Rework cost analysis
   - Review duration distribution

3. **costs.md** — Token economics dashboard
   - Cost summary (total, per ticket, per session)
   - Daily cost trend (60 days)
   - Cost by model breakdown
   - Cache efficiency tracking
   - Cost per line of code trend
   - 30-day cost projections
   - Most expensive tickets

4. **pipeline.md** — Pipeline efficiency metrics
   - Pipeline status summary
   - Time in status analysis
   - Handoff latency tracking
   - Blocked tickets monitoring
   - Ticket flow visualization (created/started/completed)
   - Cycle time by ticket size
   - Longest in-progress tickets

5. **ticket/[ticket_code].md** — Parametric ticket deep dive
   - Ticket details and summary
   - Full ticket lifecycle
   - Agent sessions detail
   - Review history
   - Cost breakdown by agent
   - Pull requests
   - Time distribution by status

6. **architect.md** — Architect efficiency tracking
   - Architect overview (sessions, tickets, costs)
   - Intervention trend (30 days)
   - Autonomy ratio calculation
   - Tickets requiring intervention
   - Coordination cost by ticket size
   - Session duration distribution
   - Recent coordination activity
   - Intervention types breakdown

7. **prompts.md** — Prompt effectiveness analysis
   - Prompt overview with success rates
   - First-pass success by ticket size
   - Success rate by agent role
   - Clean vs churn (session outcomes)
   - Craft impact on success
   - Success trend (30 days)
   - QA/prompt quality correlation
   - Model performance by outcome

8. **efficiency.md** — Operational efficiency metrics
   - Efficiency overview
   - Session productivity by agent
   - Context utilization (token usage vs window)
   - Cache hit rate by agent
   - Session duration distribution
   - Token efficiency (cost per activity)
   - Compaction opportunities
   - Activity type distribution
   - Efficiency trend (activities per hour)

## Key Implementation Details

- **Schema**: All queries use `herd_dm.` prefix (NOT `mart.`)
- **Type 2 SCD Joins**: Used `valid_from`/`valid_to` for dim_agent and dim_ticket
- **Type 1 Joins**: Used direct TK=SK for dim_model, dim_craft, dim_personality
- **Column Names**: Verified against actual dbt model SQL files
- **Evidence Components**: BigValue, LineChart, BarChart, DataTable, ScatterPlot, Histogram, Dropdown
- **Color Language**:
  - Blue (#3B82F6) for primary series
  - Green (#10B981) for success/secondary
  - Amber (#F59E0B) for transitions/flow
  - Red (#EF4444) for costs/alerts
  - Purple (#8B5CF6) for composition/skillsets

## Files Changed

```
.herd/evidence/pages/agents.md (new)
.herd/evidence/pages/qa.md (new)
.herd/evidence/pages/costs.md (new)
.herd/evidence/pages/pipeline.md (new)
.herd/evidence/pages/ticket/[ticket_code].md (new)
.herd/evidence/pages/architect.md (new)
.herd/evidence/pages/prompts.md (new)
.herd/evidence/pages/efficiency.md (new)
```

## What to Test

1. **SQL Syntax**: Verify all queries run without errors in DuckDB
2. **Schema References**: Confirm `herd_dm.` schema prefix is correct
3. **Column Names**: Check all column names match actual mart models
4. **Type 2 SCD Joins**: Verify joins to dim_agent and dim_ticket use valid_from/valid_to correctly
5. **Aggregations**: Test NULL handling in COALESCEs and NULLIFs
6. **Date Functions**: Verify `strftime` and `INTERVAL` syntax works in DuckDB
7. **Components**: Check Evidence.dev component syntax (fmt, series, colors)
8. **Parametric Page**: Test ticket/[ticket_code].md with actual ticket code parameter
9. **Visual Consistency**: Verify color scheme matches spec across all dashboards
10. **Data Completeness**: Check for empty results and NULL handling

## Known Issues / Notes

- dim_craft uses `craft_description` (not `craft_name`) — corrected in prompts.md
- Parametric ticket page uses Evidence.dev `${inputs.ticket_code}` syntax
- Some queries use `MEDIAN()` function — verify DuckDB support
- Cache efficiency calculations assume cache tokens are present
- Autonomy ratio in architect.md uses subquery pattern

## Next Steps

1. Wardenstein reviews SQL and Evidence.dev syntax
2. Test dashboards against actual DuckDB data
3. Verify parametric ticket page works with actual ticket codes
4. Fix any SQL errors or component syntax issues
5. Approve for merge

---

**Branch**: herd/pikasso/dbc-99-remaining-dashboards
**Ticket**: DBC-99

"Every pixel tells a story."

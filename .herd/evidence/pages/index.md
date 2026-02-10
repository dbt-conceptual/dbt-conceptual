# Executive Overview

> "Every pixel tells a story." — The Herd dashboards bring clarity to the chaos.

## System Health

**Question**: What is the current state of the system and recent activity?

```sql active_agents
SELECT
    COUNT(DISTINCT agent_code) as total_agents,
    SUM(CASE WHEN agent_status = 'Active' THEN 1 ELSE 0 END) as active_agents,
    SUM(CASE WHEN agent_status = 'Idle' THEN 1 ELSE 0 END) as idle_agents,
    SUM(CASE WHEN agent_status = 'Blocked' THEN 1 ELSE 0 END) as blocked_agents
FROM herd_dm.dim_agent
WHERE is_current = true AND NOT is_deleted
```

```sql open_tickets
SELECT COUNT(*) as count
FROM herd_dm.dim_ticket
WHERE is_current = true
  AND NOT is_deleted
  AND ticket_current_status NOT IN ('Done', 'Canceled', 'Cancelled', 'Archived')
```

```sql prs_this_week
SELECT COUNT(*) as count
FROM herd_dm.fact_pr_delivery fpd
JOIN herd_dm.dim_date dd ON CAST(strftime(fpd.pr_merged_at, '%Y%m%d') AS INTEGER) = dd.date_sk
WHERE dd.date_actual >= DATE_TRUNC('week', CURRENT_DATE)
  AND fpd.pr_merged_at IS NOT NULL
```

```sql cost_this_week
SELECT COALESCE(SUM(total_token_cost_usd), 0) as total_cost
FROM herd_dm.fact_agent_instance_cost
```

```sql cost_per_line
SELECT
    CASE
        WHEN SUM(fpd.pr_lines_added + fpd.pr_lines_deleted) > 0
        THEN SUM(faic.total_token_cost_usd) / SUM(fpd.pr_lines_added + fpd.pr_lines_deleted)
        ELSE 0
    END as cost_per_line
FROM herd_dm.fact_pr_delivery fpd
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON fpd.agent_sk = faic.agent_sk
WHERE fpd.pr_merged_at >= CURRENT_DATE - INTERVAL '7 days'
```

<div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
  <BigValue
    data={active_agents}
    value="active_agents"
    title="Active Agents"
    comparison="total_agents"
    comparisonTitle="Total"
  />

  <BigValue
    data={open_tickets}
    value="count"
    title="Open Tickets"
  />

  <BigValue
    data={prs_this_week}
    value="count"
    title="PRs This Week"
  />

  <BigValue
    data={cost_this_week}
    value="total_cost"
    title="Total Cost"
    fmt="usd"
  />

  <BigValue
    data={cost_per_line}
    value="cost_per_line"
    title="Cost/Line"
    fmt="usd2"
  />
</div>

---

## Agent Utilization

**Question**: Which agents are working and what are they costing?

```sql agent_work_summary
SELECT
    da.agent_code,
    da.agent_role,
    da.agent_status,
    SUM(faic.total_token_input_count + faic.total_token_output_count) as tokens_used,
    SUM(faic.total_token_cost_usd) as cost_usd,
    COUNT(DISTINCT faic.agent_instance_tk) as instances
FROM herd_dm.dim_agent da
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON da.agent_sk = faic.agent_sk
WHERE da.is_current = true AND NOT da.is_deleted
GROUP BY
    da.agent_code,
    da.agent_role,
    da.agent_status
ORDER BY cost_usd DESC NULLS LAST, da.agent_code
```

<DataTable data={agent_work_summary}>
  <Column id="agent_code" title="Agent" />
  <Column id="agent_role" title="Role" />
  <Column id="agent_status" title="Status" />
  <Column id="instances" title="Instances" fmt="num0" />
  <Column id="tokens_used" title="Tokens" fmt="num0" />
  <Column id="cost_usd" title="Cost" fmt="usd2" />
</DataTable>

---

## Cost Trends (Last 30 Days)

**Question**: How are costs trending recently?

```sql cost_trends
SELECT
    dd.date_actual as date,
    COALESCE(SUM(faic.total_token_cost_usd), 0) as daily_cost,
    SUM(COALESCE(SUM(faic.total_token_cost_usd), 0)) OVER (
        ORDER BY dd.date_actual
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cumulative_cost
FROM herd_dm.dim_date dd
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faic.agent_sk IN (
        SELECT agent_sk FROM herd_dm.dim_agent
        WHERE valid_from::DATE = dd.date_actual
    )
WHERE dd.date_actual >= CURRENT_DATE - INTERVAL '30 days'
  AND dd.date_actual <= CURRENT_DATE
GROUP BY dd.date_actual
ORDER BY dd.date_actual
```

<LineChart
  data={cost_trends}
  x="date"
  y="daily_cost"
  y2="cumulative_cost"
  yAxisTitle="Daily Cost (USD)"
  y2AxisTitle="Cumulative Cost (USD)"
  title="Daily & Cumulative Costs"
  series={[
    { name: 'Daily Cost', color: '#3B82F6' },
    { name: 'Cumulative Cost', color: '#10B981' }
  ]}
/>

---

## Recent Pull Requests

**Question**: What work has been delivered recently?

```sql recent_prs
SELECT
    dpr.pr_code,
    dpr.pr_title,
    dpr.ticket_code,
    da.agent_code,
    fpd.pr_merged_at as merged_date,
    fpd.pr_lines_added as lines_added,
    fpd.pr_lines_deleted as lines_deleted,
    fpd.pr_files_changed as files_changed
FROM herd_dm.fact_pr_delivery fpd
JOIN herd_dm.dim_pull_request dpr
    ON fpd.pull_request_sk = dpr.pull_request_sk
LEFT JOIN herd_dm.dim_agent da
    ON fpd.agent_sk = da.agent_sk
WHERE fpd.pr_merged_at >= CURRENT_DATE - INTERVAL '7 days'
  AND fpd.pr_merged_at IS NOT NULL
ORDER BY fpd.pr_merged_at DESC
LIMIT 10
```

<DataTable data={recent_prs}>
  <Column id="pr_code" title="PR" />
  <Column id="pr_title" title="Title" />
  <Column id="ticket_code" title="Ticket" />
  <Column id="agent_code" title="Agent" />
  <Column id="merged_date" title="Merged" fmt="date" />
  <Column id="files_changed" title="Files" fmt="num0" />
  <Column id="lines_added" title="Added" fmt="num0" />
  <Column id="lines_deleted" title="Deleted" fmt="num0" />
</DataTable>

---

## Agent Status

**Question**: How are agents distributed across status categories?

```sql agent_status_summary
SELECT
    agent_status,
    COUNT(*) as agent_count
FROM herd_dm.dim_agent
WHERE is_current = true AND NOT is_deleted
GROUP BY agent_status
ORDER BY agent_count DESC
```

<BarChart
  data={agent_status_summary}
  x="agent_status"
  y="agent_count"
  title="Agents by Status"
  xAxisTitle="Status"
  yAxisTitle="Count"
  series={[
    { name: 'Agent Count', color: '#8B5CF6' }
  ]}
/>

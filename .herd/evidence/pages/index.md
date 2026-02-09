# Executive Overview

> "Every pixel tells a story." — The Herd dashboards bring clarity to the chaos.

## System Health

```sql active_agents
SELECT
    COUNT(DISTINCT agent_name) as total_agents,
    SUM(CASE WHEN current_status = 'Active' THEN 1 ELSE 0 END) as active_agents,
    SUM(CASE WHEN current_status = 'Idle' THEN 1 ELSE 0 END) as idle_agents,
    SUM(CASE WHEN current_status = 'Blocked' THEN 1 ELSE 0 END) as blocked_agents
FROM dim_agent
WHERE is_active = true
```

```sql open_tickets
SELECT COUNT(*) as count
FROM dim_ticket
WHERE current_state NOT IN ('Done', 'Canceled', 'Archived')
```

```sql prs_this_week
SELECT COUNT(*) as count
FROM fact_pr_delivery fpd
JOIN dim_date dd ON fpd.merged_date_key = dd.date_key
WHERE dd.week_start_date = DATE_TRUNC('week', CURRENT_DATE)
```

```sql cost_this_week
SELECT COALESCE(SUM(total_cost_usd), 0) as total_cost
FROM fact_agent_instance_cost faic
JOIN dim_date dd ON faic.date_key = dd.date_key
WHERE dd.week_start_date = DATE_TRUNC('week', CURRENT_DATE)
```

<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
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
    title="Cost This Week"
    fmt="usd"
  />
</div>

---

## Agent Utilization

```sql agent_work_summary
SELECT
    da.agent_name,
    da.current_status,
    da.current_ticket,
    dt.title as ticket_title,
    dt.priority,
    SUM(faiw.total_tokens) as tokens_used,
    SUM(faic.total_cost_usd) as cost_usd,
    MAX(dd.full_date) as last_active
FROM dim_agent da
LEFT JOIN dim_ticket dt ON da.current_ticket = dt.ticket_id
LEFT JOIN fact_agent_instance_work faiw ON da.agent_key = faiw.agent_key
LEFT JOIN fact_agent_instance_cost faic ON faiw.agent_instance_key = faic.agent_instance_key
LEFT JOIN dim_date dd ON faic.date_key = dd.date_key
WHERE da.is_active = true
GROUP BY
    da.agent_name,
    da.current_status,
    da.current_ticket,
    dt.title,
    dt.priority
ORDER BY da.agent_name
```

<DataTable data={agent_work_summary}>
  <Column id="agent_name" title="Agent" />
  <Column id="current_status" title="Status" />
  <Column id="current_ticket" title="Ticket" />
  <Column id="ticket_title" title="Description" />
  <Column id="priority" title="Priority" />
  <Column id="tokens_used" title="Tokens" fmt="num0" />
  <Column id="cost_usd" title="Cost" fmt="usd2" />
  <Column id="last_active" title="Last Active" fmt="date" />
</DataTable>

---

## Cost Trends (Last 30 Days)

```sql cost_trends
SELECT
    dd.full_date as date,
    SUM(faic.total_cost_usd) as daily_cost,
    SUM(SUM(faic.total_cost_usd)) OVER (
        ORDER BY dd.full_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cumulative_cost
FROM fact_agent_instance_cost faic
JOIN dim_date dd ON faic.date_key = dd.date_key
WHERE dd.full_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY dd.full_date
ORDER BY dd.full_date
```

<LineChart
  data={cost_trends}
  x="date"
  y="daily_cost"
  y2="cumulative_cost"
  yAxisTitle="Daily Cost (USD)"
  y2AxisTitle="Cumulative Cost (USD)"
  title="Daily & Cumulative Costs"
/>

---

## Recent Pull Requests

```sql recent_prs
SELECT
    dpr.pr_number,
    dpr.title,
    dpr.author,
    da.agent_name,
    dd.full_date as merged_date,
    fpd.lines_added,
    fpd.lines_deleted,
    fpd.files_changed,
    frq.review_depth_score
FROM fact_pr_delivery fpd
JOIN dim_pull_request dpr ON fpd.pr_key = dpr.pr_key
JOIN dim_agent da ON fpd.agent_key = da.agent_key
JOIN dim_date dd ON fpd.merged_date_key = dd.date_key
LEFT JOIN fact_review_quality frq ON fpd.pr_key = frq.pr_key
WHERE dd.full_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY dd.full_date DESC
LIMIT 10
```

<DataTable data={recent_prs}>
  <Column id="pr_number" title="PR#" />
  <Column id="title" title="Title" />
  <Column id="agent_name" title="Agent" />
  <Column id="merged_date" title="Merged" fmt="date" />
  <Column id="files_changed" title="Files" />
  <Column id="lines_added" title="Added" fmt="num0" />
  <Column id="lines_deleted" title="Deleted" fmt="num0" />
  <Column id="review_depth_score" title="Quality" fmt="pct1" />
</DataTable>

---

## Blocked Agents

```sql blocked_agents
SELECT
    da.agent_name,
    da.current_ticket,
    dt.title as ticket_title,
    dt.blocked_reason,
    dd.full_date as blocked_since
FROM dim_agent da
JOIN dim_ticket dt ON da.current_ticket = dt.ticket_id
LEFT JOIN dim_date dd ON dt.blocked_date_key = dd.date_key
WHERE da.current_status = 'Blocked'
ORDER BY dd.full_date
```

{#if blocked_agents.length > 0}
<Alert status="warning">
  <strong>{blocked_agents.length} agent(s) currently blocked</strong>
</Alert>

<DataTable data={blocked_agents}>
  <Column id="agent_name" title="Agent" />
  <Column id="current_ticket" title="Ticket" />
  <Column id="ticket_title" title="Title" />
  <Column id="blocked_reason" title="Reason" />
  <Column id="blocked_since" title="Since" fmt="date" />
</DataTable>
{:else}
<Alert status="success">
  No agents currently blocked. All systems operational.
</Alert>
{/if}

# Sprint Metrics

> "Art is never finished, only abandoned." — Track sprint progress and velocity.

## Sprint Selection

**Select a sprint to analyze its metrics and burndown.**

```sql sprints
SELECT
    sprint_code,
    sprint_title,
    sprint_started_at,
    sprint_planned_end_at,
    sprint_actual_end_at,
    CASE WHEN sprint_actual_end_at IS NULL THEN true ELSE false END as is_active
FROM herd_dm.dim_sprint
WHERE is_current = true
  AND NOT is_deleted
  AND (sprint_planned_end_at >= CURRENT_DATE - INTERVAL '90 days'
       OR sprint_actual_end_at >= CURRENT_DATE - INTERVAL '90 days'
       OR sprint_actual_end_at IS NULL)
ORDER BY sprint_started_at DESC
```

<Dropdown
  data={sprints}
  name="selected_sprint"
  value="sprint_code"
  label="sprint_title"
  defaultValue={sprints[0].sprint_code}
  title="Select Sprint"
/>

---

## Sprint Overview

**Question**: What is the status of work in this sprint?

```sql sprint_summary
SELECT
    ds.sprint_title,
    ds.sprint_code,
    ds.sprint_started_at as start_date,
    ds.sprint_planned_end_at as end_date,
    CASE WHEN ds.sprint_actual_end_at IS NULL THEN true ELSE false END as is_active,
    COUNT(DISTINCT dt.ticket_code) as total_tickets,
    SUM(CASE WHEN dt.ticket_current_status = 'Done' THEN 1 ELSE 0 END) as completed_tickets,
    SUM(CASE WHEN dt.ticket_current_status IN ('In Progress', 'In Review', 'PR Submitted', 'QA Review') THEN 1 ELSE 0 END) as in_progress_tickets,
    SUM(CASE WHEN dt.ticket_current_status IN ('Backlog', 'Todo', 'Assigned') THEN 1 ELSE 0 END) as todo_tickets
FROM herd_dm.dim_sprint ds
LEFT JOIN herd_dm.dim_ticket dt
    ON ds.sprint_code = dt.current_sprint_code
    AND dt.is_current = true
    AND NOT dt.is_deleted
WHERE ds.sprint_code = '${inputs.selected_sprint}'
  AND ds.is_current = true
GROUP BY ds.sprint_title, ds.sprint_code, ds.sprint_started_at, ds.sprint_planned_end_at, ds.sprint_actual_end_at
```

<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
  <BigValue
    data={sprint_summary}
    value="completed_tickets"
    comparison="total_tickets"
    comparisonTitle="Total"
    title="Completed Tickets"
  />

  <BigValue
    data={sprint_summary}
    value="in_progress_tickets"
    title="In Progress"
  />

  <BigValue
    data={sprint_summary}
    value="todo_tickets"
    title="To Do"
  />

  <BigValue
    data={sprint_summary}
    value="is_active"
    title="Active Sprint"
    fmt="bool"
  />
</div>

---

## Burndown Chart

**Question**: Are we completing work at the expected pace?

```sql burndown
SELECT
    dd.date_actual as date,
    COUNT(DISTINCT CASE WHEN fsb.ticket_status NOT IN ('Done', 'Completed', 'Closed') THEN fsb.ticket_tk END) as remaining_tickets,
    COUNT(DISTINCT CASE WHEN fsb.ticket_status IN ('Done', 'Completed', 'Closed') THEN fsb.ticket_tk END) as completed_tickets
FROM herd_dm.fact_sprint_burndown fsb
JOIN herd_dm.dim_date dd
    ON CAST(strftime(fsb.event_ts, '%Y%m%d') AS INTEGER) = dd.date_sk
WHERE fsb.sprint_code = '${inputs.selected_sprint}'
GROUP BY dd.date_actual
ORDER BY dd.date_actual
```

<LineChart
  data={burndown}
  x="date"
  y="remaining_tickets"
  y2="completed_tickets"
  yAxisTitle="Ticket Count"
  title="Sprint Burndown (Tickets)"
  legend=true
  series={[
    { name: 'Remaining', color: '#F59E0B' },
    { name: 'Completed', color: '#10B981' }
  ]}
/>

---

## Agent Contributions

**Question**: Which agents contributed the most to this sprint?

```sql agent_contributions
WITH sprint_window AS (
    SELECT
        sprint_started_at,
        COALESCE(sprint_actual_end_at, sprint_planned_end_at) as sprint_end_at
    FROM herd_dm.dim_sprint
    WHERE sprint_code = '${inputs.selected_sprint}'
      AND is_current = true
),
pr_metrics AS (
    SELECT
        fpd.agent_sk,
        COUNT(DISTINCT fpd.pull_request_sk) as prs_merged,
        SUM(fpd.pr_lines_added + fpd.pr_lines_deleted) as total_lines_changed
    FROM herd_dm.fact_pr_delivery fpd
    CROSS JOIN sprint_window sw
    WHERE fpd.pr_merged_at IS NOT NULL
      AND fpd.pr_merged_at BETWEEN sw.sprint_started_at AND sw.sprint_end_at
    GROUP BY fpd.agent_sk
),
cost_metrics AS (
    SELECT
        faic.agent_sk,
        SUM(faic.total_token_cost_usd) as cost_usd
    FROM herd_dm.fact_agent_instance_cost faic
    JOIN herd_dm.dim_ticket dt
        ON faic.ticket_sk = dt.ticket_sk
    CROSS JOIN sprint_window sw
    WHERE dt.is_current = true
    GROUP BY faic.agent_sk
)
SELECT
    da.agent_code,
    da.agent_role,
    COALESCE(pm.prs_merged, 0) as prs_merged,
    COALESCE(pm.total_lines_changed, 0) as total_lines_changed,
    COALESCE(cm.cost_usd, 0) as cost_usd
FROM herd_dm.dim_agent da
LEFT JOIN pr_metrics pm
    ON da.agent_sk = pm.agent_sk
LEFT JOIN cost_metrics cm
    ON da.agent_sk = cm.agent_sk
WHERE da.is_current = true
  AND NOT da.is_deleted
  AND (pm.prs_merged > 0 OR cm.cost_usd > 0)
ORDER BY cost_usd DESC NULLS LAST
```

<BarChart
  data={agent_contributions}
  x="agent_code"
  y="prs_merged"
  title="PRs Merged by Agent"
  xAxisTitle="Agent"
  yAxisTitle="PR Count"
  series={[
    { name: 'PRs Merged', color: '#3B82F6' }
  ]}
/>

<DataTable data={agent_contributions}>
  <Column id="agent_code" title="Agent" />
  <Column id="agent_role" title="Role" />
  <Column id="prs_merged" title="PRs" fmt="num0" />
  <Column id="total_lines_changed" title="Lines Changed" fmt="num0" />
  <Column id="cost_usd" title="Cost" fmt="usd2" />
</DataTable>

---

## Velocity Trends (Last 6 Sprints)

**Question**: How does this sprint's velocity compare to historical performance?

```sql velocity_history
SELECT
    ds.sprint_title,
    ds.sprint_code,
    ds.sprint_started_at as start_date,
    COUNT(DISTINCT dt.ticket_code) as tickets_completed,
    COUNT(DISTINCT fpd.pull_request_sk) as prs_merged
FROM herd_dm.dim_sprint ds
LEFT JOIN herd_dm.dim_ticket dt
    ON ds.sprint_code = dt.current_sprint_code
    AND dt.is_current = true
    AND NOT dt.is_deleted
    AND dt.ticket_current_status = 'Done'
LEFT JOIN herd_dm.fact_pr_delivery fpd
    ON fpd.pr_merged_at BETWEEN ds.sprint_started_at AND COALESCE(ds.sprint_actual_end_at, ds.sprint_planned_end_at)
WHERE ds.is_current = true
  AND NOT ds.is_deleted
  AND COALESCE(ds.sprint_actual_end_at, ds.sprint_planned_end_at) >= CURRENT_DATE - INTERVAL '180 days'
  AND COALESCE(ds.sprint_actual_end_at, ds.sprint_planned_end_at) <= CURRENT_DATE
GROUP BY ds.sprint_title, ds.sprint_code, ds.sprint_started_at
ORDER BY ds.sprint_started_at DESC
LIMIT 6
```

<BarChart
  data={velocity_history}
  x="sprint_title"
  y="tickets_completed"
  title="Sprint Velocity (Tickets Completed)"
  xAxisTitle="Sprint"
  yAxisTitle="Tickets Completed"
  series={[
    { name: 'Tickets', color: '#10B981' }
  ]}
/>

---

## Sprint Tickets Detail

**Question**: What is the detailed status of each ticket in this sprint?

```sql sprint_tickets
WITH ticket_assignees AS (
    SELECT
        faic.ticket_sk,
        faic.agent_sk,
        ROW_NUMBER() OVER (PARTITION BY faic.ticket_sk ORDER BY faic.agent_instance_tk DESC) as rn
    FROM herd_dm.fact_agent_instance_cost faic
)
SELECT
    dt.ticket_code,
    dt.ticket_title,
    dt.ticket_current_status,
    dt.ticket_tshirt_size,
    da.agent_code as assignee
FROM herd_dm.dim_ticket dt
LEFT JOIN ticket_assignees ta
    ON dt.ticket_sk = ta.ticket_sk
    AND ta.rn = 1
LEFT JOIN herd_dm.dim_agent da
    ON ta.agent_sk = da.agent_sk
WHERE dt.current_sprint_code = '${inputs.selected_sprint}'
  AND dt.is_current = true
  AND NOT dt.is_deleted
ORDER BY
    CASE dt.ticket_current_status
        WHEN 'Done' THEN 3
        WHEN 'In Review' THEN 1
        WHEN 'In Progress' THEN 2
        ELSE 4
    END,
    dt.ticket_code
```

<DataTable data={sprint_tickets}>
  <Column id="ticket_code" title="Ticket" />
  <Column id="ticket_title" title="Title" />
  <Column id="ticket_current_status" title="Status" />
  <Column id="ticket_tshirt_size" title="Size" />
  <Column id="assignee" title="Assignee" />
</DataTable>

---

## Recent Activity

**Question**: What recent events have occurred in this sprint?

```sql recent_activity
SELECT
    fsb.event_ts,
    dt.ticket_code,
    dt.ticket_title,
    fsb.ticket_status,
    fsb.ticket_event_type
FROM herd_dm.fact_sprint_burndown fsb
JOIN herd_dm.dim_ticket dt
    ON fsb.ticket_sk = dt.ticket_sk
WHERE fsb.sprint_code = '${inputs.selected_sprint}'
ORDER BY fsb.event_ts DESC
LIMIT 20
```

<DataTable data={recent_activity}>
  <Column id="event_ts" title="Time" fmt="datetime" />
  <Column id="ticket_code" title="Ticket" />
  <Column id="ticket_title" title="Title" />
  <Column id="ticket_status" title="Status" />
  <Column id="ticket_event_type" title="Event" />
</DataTable>

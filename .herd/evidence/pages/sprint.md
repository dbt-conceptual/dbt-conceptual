# Sprint Metrics

> "Art is never finished, only abandoned." — Track sprint progress and velocity.

## Sprint Selection

```sql sprints
SELECT
    sprint_id,
    sprint_name,
    start_date,
    end_date,
    is_active
FROM dim_sprint
WHERE end_date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY start_date DESC
```

<Dropdown
  data={sprints}
  name="selected_sprint"
  value="sprint_id"
  label="sprint_name"
  defaultValue={sprints[0].sprint_id}
  title="Select Sprint"
/>

---

## Sprint Overview

```sql sprint_summary
SELECT
    ds.sprint_name,
    ds.start_date,
    ds.end_date,
    ds.is_active,
    COUNT(DISTINCT dt.ticket_id) as total_tickets,
    SUM(CASE WHEN dt.current_state = 'Done' THEN 1 ELSE 0 END) as completed_tickets,
    SUM(CASE WHEN dt.current_state IN ('In Progress', 'In Review') THEN 1 ELSE 0 END) as in_progress_tickets,
    SUM(CASE WHEN dt.current_state = 'Todo' THEN 1 ELSE 0 END) as todo_tickets,
    SUM(dt.story_points) as total_points,
    SUM(CASE WHEN dt.current_state = 'Done' THEN dt.story_points ELSE 0 END) as completed_points
FROM dim_sprint ds
LEFT JOIN dim_ticket dt ON ds.sprint_id = dt.sprint_id
WHERE ds.sprint_id = '${inputs.selected_sprint}'
GROUP BY ds.sprint_name, ds.start_date, ds.end_date, ds.is_active
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
    value="completed_points"
    comparison="total_points"
    comparisonTitle="Total"
    title="Story Points"
  />

  <BigValue
    data={sprint_summary}
    value="is_active"
    title="Status"
    fmt="bool"
  />
</div>

---

## Burndown Chart

```sql burndown
SELECT
    dd.full_date as date,
    fsb.remaining_points,
    fsb.ideal_remaining_points,
    fsb.completed_points_cumulative
FROM fact_sprint_burndown fsb
JOIN dim_date dd ON fsb.date_key = dd.date_key
JOIN dim_sprint ds ON fsb.sprint_key = ds.sprint_key
WHERE ds.sprint_id = '${inputs.selected_sprint}'
ORDER BY dd.full_date
```

<LineChart
  data={burndown}
  x="date"
  y="remaining_points"
  y2="ideal_remaining_points"
  yAxisTitle="Remaining Story Points"
  title="Sprint Burndown"
  legend=true
  series={[
    { name: 'Actual Remaining', color: '#4A90D9' },
    { name: 'Ideal Remaining', color: '#7AB648', lineStyle: 'dashed' }
  ]}
/>

---

## Agent Contributions

```sql agent_contributions
SELECT
    da.agent_name,
    COUNT(DISTINCT dt.ticket_id) as tickets_completed,
    SUM(dt.story_points) as points_delivered,
    COUNT(DISTINCT fpd.pr_key) as prs_merged,
    SUM(faic.total_cost_usd) as cost_usd,
    AVG(frq.review_depth_score) as avg_review_quality
FROM dim_agent da
JOIN dim_ticket dt ON da.agent_key = dt.assignee_agent_key
JOIN dim_sprint ds ON dt.sprint_id = ds.sprint_id
LEFT JOIN fact_pr_delivery fpd ON da.agent_key = fpd.agent_key
    AND fpd.merged_date_key IN (
        SELECT date_key FROM dim_date
        WHERE full_date BETWEEN ds.start_date AND ds.end_date
    )
LEFT JOIN fact_agent_instance_cost faic ON da.agent_key = faic.agent_key
    AND faic.date_key IN (
        SELECT date_key FROM dim_date
        WHERE full_date BETWEEN ds.start_date AND ds.end_date
    )
LEFT JOIN fact_review_quality frq ON fpd.pr_key = frq.pr_key
WHERE ds.sprint_id = '${inputs.selected_sprint}'
    AND dt.current_state = 'Done'
GROUP BY da.agent_name
ORDER BY points_delivered DESC
```

<BarChart
  data={agent_contributions}
  x="agent_name"
  y="points_delivered"
  title="Story Points Delivered by Agent"
  xAxisTitle="Agent"
  yAxisTitle="Story Points"
/>

<DataTable data={agent_contributions}>
  <Column id="agent_name" title="Agent" />
  <Column id="tickets_completed" title="Tickets" />
  <Column id="points_delivered" title="Points" />
  <Column id="prs_merged" title="PRs" />
  <Column id="cost_usd" title="Cost" fmt="usd2" />
  <Column id="avg_review_quality" title="Avg Quality" fmt="pct1" />
</DataTable>

---

## Velocity Trends (Last 6 Sprints)

```sql velocity_history
SELECT
    ds.sprint_name,
    ds.start_date,
    COUNT(DISTINCT dt.ticket_id) as tickets_completed,
    SUM(dt.story_points) as points_completed,
    COUNT(DISTINCT fpd.pr_key) as prs_merged
FROM dim_sprint ds
LEFT JOIN dim_ticket dt ON ds.sprint_id = dt.sprint_id
    AND dt.current_state = 'Done'
LEFT JOIN fact_pr_delivery fpd ON fpd.merged_date_key IN (
    SELECT date_key FROM dim_date
    WHERE full_date BETWEEN ds.start_date AND ds.end_date
)
WHERE ds.end_date >= CURRENT_DATE - INTERVAL '180 days'
    AND ds.end_date <= CURRENT_DATE
GROUP BY ds.sprint_name, ds.start_date
ORDER BY ds.start_date DESC
LIMIT 6
```

<BarChart
  data={velocity_history}
  x="sprint_name"
  y="points_completed"
  title="Sprint Velocity (Story Points)"
  xAxisTitle="Sprint"
  yAxisTitle="Story Points Completed"
/>

---

## Completion Rates by Priority

```sql completion_by_priority
SELECT
    dt.priority,
    COUNT(*) as total_tickets,
    SUM(CASE WHEN dt.current_state = 'Done' THEN 1 ELSE 0 END) as completed,
    ROUND(100.0 * SUM(CASE WHEN dt.current_state = 'Done' THEN 1 ELSE 0 END) / COUNT(*), 1) as completion_rate
FROM dim_ticket dt
JOIN dim_sprint ds ON dt.sprint_id = ds.sprint_id
WHERE ds.sprint_id = '${inputs.selected_sprint}'
GROUP BY dt.priority
ORDER BY
    CASE dt.priority
        WHEN 'Urgent' THEN 1
        WHEN 'High' THEN 2
        WHEN 'Medium' THEN 3
        WHEN 'Low' THEN 4
        ELSE 5
    END
```

<BarChart
  data={completion_by_priority}
  x="priority"
  y="completion_rate"
  title="Completion Rate by Priority"
  xAxisTitle="Priority"
  yAxisTitle="Completion Rate (%)"
  swapXY=true
/>

---

## Sprint Tickets Detail

```sql sprint_tickets
SELECT
    dt.ticket_id,
    dt.title,
    dt.priority,
    dt.current_state,
    dt.story_points,
    da.agent_name as assignee,
    dd_created.full_date as created_date,
    dd_completed.full_date as completed_date,
    CASE
        WHEN dt.current_state = 'Done' AND dd_completed.full_date IS NOT NULL
        THEN dd_completed.full_date - dd_created.full_date
        ELSE NULL
    END as days_to_complete
FROM dim_ticket dt
JOIN dim_sprint ds ON dt.sprint_id = ds.sprint_id
LEFT JOIN dim_agent da ON dt.assignee_agent_key = da.agent_key
LEFT JOIN dim_date dd_created ON dt.created_date_key = dd_created.date_key
LEFT JOIN dim_date dd_completed ON dt.completed_date_key = dd_completed.date_key
WHERE ds.sprint_id = '${inputs.selected_sprint}'
ORDER BY
    CASE dt.current_state
        WHEN 'Done' THEN 3
        WHEN 'In Review' THEN 1
        WHEN 'In Progress' THEN 2
        ELSE 4
    END,
    dt.priority
```

<DataTable data={sprint_tickets}>
  <Column id="ticket_id" title="Ticket" />
  <Column id="title" title="Title" />
  <Column id="priority" title="Priority" />
  <Column id="current_state" title="State" />
  <Column id="story_points" title="Points" />
  <Column id="assignee" title="Assignee" />
  <Column id="created_date" title="Created" fmt="date" />
  <Column id="completed_date" title="Completed" fmt="date" />
  <Column id="days_to_complete" title="Days" />
</DataTable>

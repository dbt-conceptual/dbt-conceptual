# Pipeline Efficiency

> "The canvas flows from idea to masterpiece." — Track ticket flow, bottlenecks, and cycle time.

## Pipeline Summary

**Question**: What is the current state of work in progress?

```sql pipeline_summary
SELECT
    COUNT(DISTINCT dt.ticket_tk) as active_tickets,
    COUNT(DISTINCT CASE WHEN dt.ticket_current_status = 'Backlog' THEN dt.ticket_tk END) as backlog_tickets,
    COUNT(DISTINCT CASE WHEN dt.ticket_current_status = 'In Progress' THEN dt.ticket_tk END) as in_progress_tickets,
    COUNT(DISTINCT CASE WHEN dt.ticket_current_status IN ('PR Submitted', 'QA Review') THEN dt.ticket_tk END) as review_tickets,
    COUNT(DISTINCT CASE WHEN ftl.blocker_ticket_code IS NOT NULL THEN dt.ticket_tk END) as blocked_tickets
FROM herd_dm.dim_ticket dt
LEFT JOIN herd_dm.fact_ticket_lifecycle ftl
    ON dt.ticket_sk = ftl.ticket_sk
WHERE dt.is_current = true
  AND NOT dt.is_deleted
  AND dt.ticket_current_status NOT IN ('Done', 'Canceled', 'Cancelled', 'Archived')
```

<div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
  <BigValue
    data={pipeline_summary}
    value="active_tickets"
    title="Active Tickets"
  />

  <BigValue
    data={pipeline_summary}
    value="backlog_tickets"
    title="Backlog"
  />

  <BigValue
    data={pipeline_summary}
    value="in_progress_tickets"
    title="In Progress"
  />

  <BigValue
    data={pipeline_summary}
    value="review_tickets"
    title="In Review"
  />

  <BigValue
    data={pipeline_summary}
    value="blocked_tickets"
    title="Blocked"
  />
</div>

---

## Time in Status (Average Minutes)

**Question**: Which statuses are bottlenecks in our workflow?

```sql time_in_status
SELECT
    ftl.previous_status,
    COUNT(*) as transition_count,
    ROUND(AVG(ftl.time_in_previous_status_minutes), 1) as avg_minutes,
    ROUND(MIN(ftl.time_in_previous_status_minutes), 1) as min_minutes,
    ROUND(MAX(ftl.time_in_previous_status_minutes), 1) as max_minutes,
    ROUND(MEDIAN(ftl.time_in_previous_status_minutes), 1) as median_minutes
FROM herd_dm.fact_ticket_lifecycle ftl
WHERE ftl.time_in_previous_status_minutes IS NOT NULL
  AND ftl.previous_status IS NOT NULL
GROUP BY ftl.previous_status
ORDER BY avg_minutes DESC
```

<BarChart
  data={time_in_status}
  x="previous_status"
  y="avg_minutes"
  title="Average Time in Status (Minutes)"
  xAxisTitle="Status"
  yAxisTitle="Minutes"
  series={[
    { name: 'Avg Time', color: '#F59E0B' }
  ]}
/>

<DataTable data={time_in_status}>
  <Column id="previous_status" title="Status" />
  <Column id="transition_count" title="Transitions" fmt="num0" />
  <Column id="avg_minutes" title="Avg" fmt="num1" />
  <Column id="median_minutes" title="Median" fmt="num1" />
  <Column id="min_minutes" title="Min" fmt="num1" />
  <Column id="max_minutes" title="Max" fmt="num1" />
</DataTable>

---

## Handoff Latency

**Question**: Where do handoffs between states cause the most delay?

```sql handoff_latency
SELECT
    CONCAT(ftl.previous_status, ' → ', ftl.ticket_status) as transition,
    COUNT(*) as count,
    ROUND(AVG(ftl.time_in_previous_status_minutes / 60.0), 1) as avg_hours,
    ROUND(MEDIAN(ftl.time_in_previous_status_minutes / 60.0), 1) as median_hours
FROM herd_dm.fact_ticket_lifecycle ftl
WHERE ftl.time_in_previous_status_minutes IS NOT NULL
  AND ftl.previous_status IS NOT NULL
  AND ftl.ticket_status != ftl.previous_status
GROUP BY transition
ORDER BY avg_hours DESC
LIMIT 20
```

<DataTable data={handoff_latency} search=true>
  <Column id="transition" title="Transition" />
  <Column id="count" title="Count" fmt="num0" />
  <Column id="avg_hours" title="Avg Hours" fmt="num1" />
  <Column id="median_hours" title="Median Hours" fmt="num1" />
</DataTable>

---

## Blocked Tickets

**Question**: What tickets are currently blocked and by what?

```sql blocked_tickets
SELECT
    dt.ticket_code,
    dt.ticket_title,
    dt.ticket_current_status,
    ftl.blocker_ticket_code,
    da.agent_code as assigned_agent,
    ftl.event_ts as blocked_since
FROM herd_dm.fact_ticket_lifecycle ftl
JOIN herd_dm.dim_ticket dt
    ON ftl.ticket_sk = dt.ticket_sk
LEFT JOIN herd_dm.dim_agent da
    ON ftl.agent_sk = da.agent_sk
WHERE ftl.blocker_ticket_code IS NOT NULL
  AND dt.is_current = true
  AND NOT dt.is_deleted
ORDER BY ftl.event_ts DESC
```

<DataTable data={blocked_tickets} search=true>
  <Column id="ticket_code" title="Ticket" />
  <Column id="ticket_title" title="Title" />
  <Column id="ticket_current_status" title="Status" />
  <Column id="blocker_ticket_code" title="Blocked By" />
  <Column id="assigned_agent" title="Agent" />
  <Column id="blocked_since" title="Since" fmt="datetime" />
</DataTable>

---

## Ticket Flow (Last 30 Days)

**Question**: How many tickets are created, started, and completed each day?

```sql ticket_flow
SELECT
    dd.date_actual as date,
    COUNT(DISTINCT CASE WHEN ftl.ticket_event_type = 'created' THEN ftl.ticket_code END) as created,
    COUNT(DISTINCT CASE WHEN ftl.ticket_event_type = 'started' THEN ftl.ticket_code END) as started,
    COUNT(DISTINCT CASE WHEN ftl.ticket_event_type = 'completed' THEN ftl.ticket_code END) as completed
FROM herd_dm.dim_date dd
LEFT JOIN herd_dm.fact_ticket_lifecycle ftl
    ON CAST(strftime(ftl.event_ts, '%Y%m%d') AS INTEGER) = dd.date_sk
WHERE dd.date_actual >= CURRENT_DATE - INTERVAL '30 days'
  AND dd.date_actual <= CURRENT_DATE
GROUP BY dd.date_actual
ORDER BY dd.date_actual
```

<LineChart
  data={ticket_flow}
  x="date"
  y={['created', 'started', 'completed']}
  yAxisTitle="Ticket Count"
  title="Ticket Flow (Created, Started, Completed)"
  series={[
    { name: 'Created', color: '#3B82F6' },
    { name: 'Started', color: '#F59E0B' },
    { name: 'Completed', color: '#10B981' }
  ]}
/>

---

## Cycle Time by Ticket Size

**Question**: Does ticket size correlate with cycle time as expected?

```sql cycle_time_by_size
WITH ticket_cycle_time AS (
    SELECT
        dt.ticket_tk,
        dt.ticket_code,
        dt.ticket_tshirt_size,
        MIN(CASE WHEN ftl.ticket_event_type = 'started' THEN ftl.event_ts END) as started_at,
        MAX(CASE WHEN ftl.ticket_event_type = 'completed' THEN ftl.event_ts END) as completed_at
    FROM herd_dm.dim_ticket dt
    JOIN herd_dm.fact_ticket_lifecycle ftl
        ON dt.ticket_sk = ftl.ticket_sk
    WHERE dt.is_current = true
      AND NOT dt.is_deleted
    GROUP BY dt.ticket_tk, dt.ticket_code, dt.ticket_tshirt_size
    HAVING started_at IS NOT NULL AND completed_at IS NOT NULL
)
SELECT
    ticket_tshirt_size,
    COUNT(*) as ticket_count,
    ROUND(AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) / 3600.0), 1) as avg_cycle_hours,
    ROUND(MEDIAN(EXTRACT(EPOCH FROM (completed_at - started_at)) / 3600.0), 1) as median_cycle_hours
FROM ticket_cycle_time
WHERE ticket_tshirt_size IS NOT NULL
GROUP BY ticket_tshirt_size
ORDER BY
    CASE ticket_tshirt_size
        WHEN 'XS' THEN 1
        WHEN 'S' THEN 2
        WHEN 'M' THEN 3
        WHEN 'L' THEN 4
        WHEN 'XL' THEN 5
        ELSE 6
    END
```

<BarChart
  data={cycle_time_by_size}
  x="ticket_tshirt_size"
  y="avg_cycle_hours"
  title="Avg Cycle Time by Ticket Size"
  xAxisTitle="Size"
  yAxisTitle="Hours"
  series={[
    { name: 'Avg Hours', color: '#8B5CF6' }
  ]}
/>

<DataTable data={cycle_time_by_size}>
  <Column id="ticket_tshirt_size" title="Size" />
  <Column id="ticket_count" title="Tickets" fmt="num0" />
  <Column id="avg_cycle_hours" title="Avg Hours" fmt="num1" />
  <Column id="median_cycle_hours" title="Median Hours" fmt="num1" />
</DataTable>

---

## Longest In-Progress Tickets

**Question**: Which in-progress tickets have been active the longest?

```sql longest_in_progress
WITH ticket_start_times AS (
    SELECT
        dt.ticket_code,
        dt.ticket_title,
        dt.ticket_current_status,
        dt.ticket_tshirt_size,
        da.agent_code as assigned_agent,
        MIN(ftl.event_ts) as started_at
    FROM herd_dm.dim_ticket dt
    JOIN herd_dm.fact_ticket_lifecycle ftl
        ON dt.ticket_sk = ftl.ticket_sk
    LEFT JOIN herd_dm.dim_agent da
        ON ftl.agent_sk = da.agent_sk
    WHERE dt.is_current = true
      AND NOT dt.is_deleted
      AND dt.ticket_current_status IN ('In Progress', 'PR Submitted', 'QA Review', 'Assigned')
      AND ftl.ticket_status IN ('In Progress', 'PR Submitted', 'QA Review', 'Assigned')
    GROUP BY dt.ticket_code, dt.ticket_title, dt.ticket_current_status, dt.ticket_tshirt_size, da.agent_code
)
SELECT
    ticket_code,
    ticket_title,
    ticket_current_status,
    ticket_tshirt_size,
    assigned_agent,
    started_at,
    ROUND(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at)) / 3600.0, 1) as hours_in_progress
FROM ticket_start_times
ORDER BY hours_in_progress DESC
LIMIT 20
```

<DataTable data={longest_in_progress} search=true>
  <Column id="ticket_code" title="Ticket" />
  <Column id="ticket_title" title="Title" />
  <Column id="ticket_current_status" title="Status" />
  <Column id="ticket_tshirt_size" title="Size" />
  <Column id="assigned_agent" title="Agent" />
  <Column id="started_at" title="Started" fmt="datetime" />
  <Column id="hours_in_progress" title="Hours" fmt="num1" />
</DataTable>

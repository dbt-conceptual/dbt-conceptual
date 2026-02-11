# Architect Efficiency

> "The master's touch guides the hand." — Track architect interventions, coordination overhead, and autonomy.

## Architect Overview

**Question**: How much coordination overhead does the architect require?

```sql architect_overview
SELECT
    COUNT(DISTINCT faiw.agent_instance_tk) as total_sessions,
    COUNT(DISTINCT dt.ticket_tk) as tickets_coordinated,
    SUM(faiw.lifecycle_event_count) as lifecycle_events,
    SUM(faiw.ticket_activity_count) as ticket_activities,
    SUM(faic.total_token_cost_usd) as total_cost,
    ROUND(AVG(faiw.instance_duration_minutes), 1) as avg_session_minutes
FROM herd_dm.dim_agent da
LEFT JOIN herd_dm.fact_agent_instance_work faiw
    ON da.agent_sk = faiw.agent_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
LEFT JOIN herd_dm.dim_ticket dt
    ON faiw.ticket_sk = dt.ticket_sk
WHERE da.agent_code = 'mini-mao'
  AND da.is_current = true
```

<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
  <BigValue
    data={architect_overview}
    value="total_sessions"
    title="Total Sessions"
  />

  <BigValue
    data={architect_overview}
    value="tickets_coordinated"
    title="Tickets Coordinated"
  />

  <BigValue
    data={architect_overview}
    value="lifecycle_events"
    title="Lifecycle Events"
  />

  <BigValue
    data={architect_overview}
    value="total_cost"
    title="Total Cost"
    fmt="usd2"
  />
</div>

---

## Intervention Trend (Last 30 Days)

**Question**: Is architect intervention increasing or decreasing over time?

```sql intervention_trend
SELECT
    dd.date_actual as date,
    COUNT(DISTINCT faiw.agent_instance_tk) as sessions,
    SUM(faiw.lifecycle_event_count) as events,
    SUM(faic.total_token_cost_usd) as cost
FROM herd_dm.dim_date dd
LEFT JOIN herd_dm.fact_agent_instance_work faiw
    ON CAST(strftime(faiw.agent_instance_started_at, '%Y%m%d') AS INTEGER) = dd.date_sk
LEFT JOIN herd_dm.dim_agent da
    ON faiw.agent_sk = da.agent_sk
    AND da.agent_code = 'mini-mao'
    AND da.is_current = true
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
WHERE dd.date_actual >= CURRENT_DATE - INTERVAL '30 days'
  AND dd.date_actual <= CURRENT_DATE
GROUP BY dd.date_actual
ORDER BY dd.date_actual
```

<LineChart
  data={intervention_trend}
  x="date"
  y="sessions"
  y2="events"
  yAxisTitle="Session Count"
  y2AxisTitle="Event Count"
  title="Architect Activity Trend"
  series={[
    { name: 'Sessions', color: '#8B5CF6' },
    { name: 'Events', color: '#F59E0B' }
  ]}
/>

---

## Autonomy Ratio

**Question**: What percentage of work happens without architect involvement?

```sql autonomy_ratio
WITH all_work AS (
    SELECT
        COUNT(DISTINCT faiw.agent_instance_tk) as total_sessions
    FROM herd_dm.fact_agent_instance_work faiw
),
architect_work AS (
    SELECT
        COUNT(DISTINCT faiw.agent_instance_tk) as architect_sessions
    FROM herd_dm.fact_agent_instance_work faiw
    JOIN herd_dm.dim_agent da
        ON faiw.agent_sk = da.agent_sk
    WHERE da.agent_code = 'mini-mao'
      AND da.is_current = true
)
SELECT
    all_work.total_sessions,
    architect_work.architect_sessions,
    ROUND(100.0 * (all_work.total_sessions - architect_work.architect_sessions) / NULLIF(all_work.total_sessions, 0), 1) as autonomy_ratio
FROM all_work, architect_work
```

<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
  <BigValue
    data={autonomy_ratio}
    value="total_sessions"
    title="Total Sessions"
  />

  <BigValue
    data={autonomy_ratio}
    value="architect_sessions"
    title="Architect Sessions"
  />

  <BigValue
    data={autonomy_ratio}
    value="autonomy_ratio"
    title="Agent Autonomy"
    fmt="pct1"
  />
</div>

---

## Tickets Requiring Intervention

**Question**: Which tickets required the most architect coordination?

```sql tickets_needing_intervention
SELECT
    dt.ticket_code,
    dt.ticket_title,
    dt.ticket_current_status,
    dt.ticket_tshirt_size,
    COUNT(DISTINCT faiw.agent_instance_tk) as architect_sessions,
    SUM(faic.total_token_cost_usd) as intervention_cost,
    ROUND(SUM(faiw.instance_duration_minutes), 1) as total_minutes
FROM herd_dm.dim_ticket dt
JOIN herd_dm.fact_agent_instance_work faiw
    ON dt.ticket_sk = faiw.ticket_sk
JOIN herd_dm.dim_agent da
    ON faiw.agent_sk = da.agent_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
WHERE da.agent_code = 'mini-mao'
  AND da.is_current = true
  AND dt.is_current = true
  AND NOT dt.is_deleted
GROUP BY dt.ticket_code, dt.ticket_title, dt.ticket_current_status, dt.ticket_tshirt_size
ORDER BY architect_sessions DESC, intervention_cost DESC
LIMIT 20
```

<DataTable data={tickets_needing_intervention} search=true>
  <Column id="ticket_code" title="Ticket" />
  <Column id="ticket_title" title="Title" />
  <Column id="ticket_current_status" title="Status" />
  <Column id="ticket_tshirt_size" title="Size" />
  <Column id="architect_sessions" title="Sessions" fmt="num0" />
  <Column id="intervention_cost" title="Cost" fmt="usd2" />
  <Column id="total_minutes" title="Minutes" fmt="num1" />
</DataTable>

---

## Coordination Cost by Ticket Size

**Question**: Do larger tickets require more coordination effort?

```sql cost_by_ticket_size
SELECT
    dt.ticket_tshirt_size,
    COUNT(DISTINCT dt.ticket_tk) as ticket_count,
    COUNT(DISTINCT faiw.agent_instance_tk) as sessions,
    SUM(faic.total_token_cost_usd) as total_cost,
    ROUND(AVG(faic.total_token_cost_usd), 4) as avg_cost_per_session
FROM herd_dm.dim_ticket dt
JOIN herd_dm.fact_agent_instance_work faiw
    ON dt.ticket_sk = faiw.ticket_sk
JOIN herd_dm.dim_agent da
    ON faiw.agent_sk = da.agent_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
WHERE da.agent_code = 'mini-mao'
  AND da.is_current = true
  AND dt.is_current = true
  AND NOT dt.is_deleted
  AND dt.ticket_tshirt_size IS NOT NULL
GROUP BY dt.ticket_tshirt_size
ORDER BY
    CASE dt.ticket_tshirt_size
        WHEN 'XS' THEN 1
        WHEN 'S' THEN 2
        WHEN 'M' THEN 3
        WHEN 'L' THEN 4
        WHEN 'XL' THEN 5
        ELSE 6
    END
```

<BarChart
  data={cost_by_ticket_size}
  x="ticket_tshirt_size"
  y="total_cost"
  title="Coordination Cost by Ticket Size"
  xAxisTitle="Size"
  yAxisTitle="Cost (USD)"
  series={[
    { name: 'Cost', color: '#8B5CF6' }
  ]}
/>

<DataTable data={cost_by_ticket_size}>
  <Column id="ticket_tshirt_size" title="Size" />
  <Column id="ticket_count" title="Tickets" fmt="num0" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="total_cost" title="Cost" fmt="usd2" />
  <Column id="avg_cost_per_session" title="Avg/Session" fmt="usd4" />
</DataTable>

---

## Session Duration Distribution

**Question**: How long are typical coordination sessions?

```sql session_duration
SELECT
    faiw.instance_duration_minutes as duration,
    COUNT(*) as count
FROM herd_dm.fact_agent_instance_work faiw
JOIN herd_dm.dim_agent da
    ON faiw.agent_sk = da.agent_sk
WHERE da.agent_code = 'mini-mao'
  AND da.is_current = true
  AND faiw.instance_duration_minutes IS NOT NULL
```

<Histogram
  data={session_duration}
  x="duration"
  y="count"
  title="Session Duration Distribution"
  xAxisTitle="Duration (minutes)"
  yAxisTitle="Count"
/>

---

## Recent Coordination Activity

**Question**: What has the architect been working on recently?

```sql recent_activity
SELECT
    faiw.agent_instance_started_at,
    dt.ticket_code,
    dt.ticket_title,
    faiw.agent_instance_outcome,
    faiw.instance_duration_minutes,
    faic.total_token_cost_usd as cost
FROM herd_dm.fact_agent_instance_work faiw
JOIN herd_dm.dim_agent da
    ON faiw.agent_sk = da.agent_sk
LEFT JOIN herd_dm.dim_ticket dt
    ON faiw.ticket_sk = dt.ticket_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
WHERE da.agent_code = 'mini-mao'
  AND da.is_current = true
ORDER BY faiw.agent_instance_started_at DESC
LIMIT 50
```

<DataTable data={recent_activity}>
  <Column id="agent_instance_started_at" title="Started" fmt="datetime" />
  <Column id="ticket_code" title="Ticket" />
  <Column id="ticket_title" title="Title" />
  <Column id="agent_instance_outcome" title="Outcome" />
  <Column id="instance_duration_minutes" title="Duration" fmt="num1" />
  <Column id="cost" title="Cost" fmt="usd4" />
</DataTable>

---

## Intervention Types

**Question**: What types of work require architect involvement?

```sql intervention_types
SELECT
    CASE
        WHEN faiw.lifecycle_event_count > 0 THEN 'Lifecycle Management'
        WHEN faiw.ticket_activity_count > 0 THEN 'Ticket Coordination'
        WHEN faiw.pr_activity_count > 0 THEN 'PR Management'
        ELSE 'Other'
    END as intervention_type,
    COUNT(DISTINCT faiw.agent_instance_tk) as session_count,
    SUM(faic.total_token_cost_usd) as total_cost
FROM herd_dm.fact_agent_instance_work faiw
JOIN herd_dm.dim_agent da
    ON faiw.agent_sk = da.agent_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
WHERE da.agent_code = 'mini-mao'
  AND da.is_current = true
GROUP BY intervention_type
ORDER BY session_count DESC
```

<BarChart
  data={intervention_types}
  x="intervention_type"
  y="session_count"
  title="Sessions by Intervention Type"
  xAxisTitle="Type"
  yAxisTitle="Count"
  series={[
    { name: 'Sessions', color: '#F59E0B' }
  ]}
/>

<DataTable data={intervention_types}>
  <Column id="intervention_type" title="Type" />
  <Column id="session_count" title="Sessions" fmt="num0" />
  <Column id="total_cost" title="Cost" fmt="usd2" />
</DataTable>

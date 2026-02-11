# Agent Operational Efficiency

> "The practiced hand wastes no motion." — Track session productivity, context usage, and operational patterns.

## Efficiency Overview

**Question**: How productive are agent sessions on average?

```sql efficiency_overview
SELECT
    COUNT(DISTINCT faiw.agent_instance_tk) as total_sessions,
    ROUND(AVG(faiw.instance_duration_minutes), 1) as avg_session_minutes,
    SUM(faiw.lifecycle_event_count) as total_lifecycle_events,
    SUM(faiw.ticket_activity_count) as total_ticket_activities,
    SUM(faiw.pr_activity_count) as total_pr_activities,
    ROUND(AVG(faiw.lifecycle_event_count), 1) as avg_lifecycle_per_session,
    ROUND(AVG(faiw.ticket_activity_count), 1) as avg_ticket_activity_per_session
FROM herd_dm.fact_agent_instance_work faiw
```

<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
  <BigValue
    data={efficiency_overview}
    value="total_sessions"
    title="Total Sessions"
  />

  <BigValue
    data={efficiency_overview}
    value="avg_session_minutes"
    title="Avg Session"
    fmt="num1"
  />

  <BigValue
    data={efficiency_overview}
    value="avg_lifecycle_per_session"
    title="Events/Session"
    fmt="num1"
  />

  <BigValue
    data={efficiency_overview}
    value="avg_ticket_activity_per_session"
    title="Activities/Session"
    fmt="num1"
  />
</div>

---

## Session Productivity by Agent

**Question**: Which agents accomplish the most work per session?

```sql session_productivity
SELECT
    da.agent_code,
    da.agent_role,
    COUNT(DISTINCT faiw.agent_instance_tk) as sessions,
    ROUND(AVG(faiw.instance_duration_minutes), 1) as avg_duration,
    ROUND(AVG(faiw.lifecycle_event_count), 1) as avg_lifecycle_events,
    ROUND(AVG(faiw.ticket_activity_count), 1) as avg_ticket_activities,
    ROUND(AVG(faiw.pr_activity_count), 1) as avg_pr_activities,
    ROUND(AVG(faiw.lifecycle_event_count + faiw.ticket_activity_count + faiw.pr_activity_count), 1) as avg_total_activity
FROM herd_dm.fact_agent_instance_work faiw
JOIN herd_dm.dim_agent da
    ON faiw.agent_sk = da.agent_sk
WHERE da.is_current = true
  AND NOT da.is_deleted
GROUP BY da.agent_code, da.agent_role
ORDER BY avg_total_activity DESC
```

<BarChart
  data={session_productivity}
  x="agent_code"
  y="avg_total_activity"
  title="Average Activity per Session by Agent"
  xAxisTitle="Agent"
  yAxisTitle="Activities"
  series={[
    { name: 'Activity', color: '#3B82F6' }
  ]}
/>

<DataTable data={session_productivity} search=true>
  <Column id="agent_code" title="Agent" />
  <Column id="agent_role" title="Role" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="avg_duration" title="Avg Duration" fmt="num1" />
  <Column id="avg_lifecycle_events" title="Lifecycle" fmt="num1" />
  <Column id="avg_ticket_activities" title="Ticket" fmt="num1" />
  <Column id="avg_pr_activities" title="PR" fmt="num1" />
  <Column id="avg_total_activity" title="Total" fmt="num1" />
</DataTable>

---

## Context Utilization (Token Usage)

**Question**: How much of the available context window is each agent using?

```sql context_utilization
SELECT
    da.agent_code,
    dm.model_code,
    dm.model_context_window,
    COUNT(DISTINCT faic.agent_instance_tk) as sessions,
    ROUND(AVG(faic.total_token_input_count + faic.total_token_output_count), 0) as avg_tokens_per_session,
    ROUND(100.0 * AVG(faic.total_token_input_count + faic.total_token_output_count) / dm.model_context_window, 1) as context_utilization_pct
FROM herd_dm.fact_agent_instance_cost faic
JOIN herd_dm.dim_agent da
    ON faic.agent_sk = da.agent_sk
JOIN herd_dm.dim_model dm
    ON faic.model_sk = dm.model_sk
WHERE da.is_current = true
  AND NOT da.is_deleted
GROUP BY da.agent_code, dm.model_code, dm.model_context_window
ORDER BY context_utilization_pct DESC
```

<BarChart
  data={context_utilization}
  x="agent_code"
  y="context_utilization_pct"
  title="Context Window Utilization by Agent (%)"
  xAxisTitle="Agent"
  yAxisTitle="Utilization (%)"
  series={[
    { name: 'Utilization', color: '#8B5CF6' }
  ]}
/>

<DataTable data={context_utilization}>
  <Column id="agent_code" title="Agent" />
  <Column id="model_code" title="Model" />
  <Column id="model_context_window" title="Window" fmt="num0" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="avg_tokens_per_session" title="Avg Tokens" fmt="num0" />
  <Column id="context_utilization_pct" title="Utilization %" fmt="num1" />
</DataTable>

---

## Cache Hit Rate by Agent

**Question**: Which agents are most effectively using prompt caching?

```sql cache_hit_rate
SELECT
    da.agent_code,
    COUNT(DISTINCT faic.agent_instance_tk) as sessions,
    SUM(faic.total_token_input_count + faic.total_token_output_count) as direct_tokens,
    SUM(faic.total_token_cache_read_count) as cache_read_tokens,
    SUM(faic.total_token_cache_create_count) as cache_create_tokens,
    ROUND(100.0 * SUM(faic.total_token_cache_read_count) /
        NULLIF(SUM(faic.total_token_input_count + faic.total_token_output_count + faic.total_token_cache_read_count), 0), 1) as cache_hit_rate
FROM herd_dm.fact_agent_instance_cost faic
JOIN herd_dm.dim_agent da
    ON faic.agent_sk = da.agent_sk
WHERE da.is_current = true
  AND NOT da.is_deleted
GROUP BY da.agent_code
ORDER BY cache_hit_rate DESC NULLS LAST
```

<BarChart
  data={cache_hit_rate}
  x="agent_code"
  y="cache_hit_rate"
  title="Cache Hit Rate by Agent (%)"
  xAxisTitle="Agent"
  yAxisTitle="Hit Rate (%)"
  series={[
    { name: 'Cache Hit', color: '#10B981' }
  ]}
/>

<DataTable data={cache_hit_rate}>
  <Column id="agent_code" title="Agent" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="direct_tokens" title="Direct" fmt="num0" />
  <Column id="cache_read_tokens" title="Cache Read" fmt="num0" />
  <Column id="cache_create_tokens" title="Cache Create" fmt="num0" />
  <Column id="cache_hit_rate" title="Hit Rate %" fmt="num1" />
</DataTable>

---

## Session Duration Distribution

**Question**: How long do most sessions last?

```sql duration_distribution
SELECT
    CASE
        WHEN faiw.instance_duration_minutes < 5 THEN '< 5 min'
        WHEN faiw.instance_duration_minutes < 15 THEN '5-15 min'
        WHEN faiw.instance_duration_minutes < 30 THEN '15-30 min'
        WHEN faiw.instance_duration_minutes < 60 THEN '30-60 min'
        ELSE '60+ min'
    END as duration_bucket,
    COUNT(*) as session_count,
    ROUND(AVG(faiw.lifecycle_event_count + faiw.ticket_activity_count + faiw.pr_activity_count), 1) as avg_activity
FROM herd_dm.fact_agent_instance_work faiw
WHERE faiw.instance_duration_minutes IS NOT NULL
GROUP BY duration_bucket
ORDER BY
    CASE duration_bucket
        WHEN '< 5 min' THEN 1
        WHEN '5-15 min' THEN 2
        WHEN '15-30 min' THEN 3
        WHEN '30-60 min' THEN 4
        ELSE 5
    END
```

<BarChart
  data={duration_distribution}
  x="duration_bucket"
  y="session_count"
  title="Session Duration Distribution"
  xAxisTitle="Duration"
  yAxisTitle="Count"
  series={[
    { name: 'Sessions', color: '#F59E0B' }
  ]}
/>

<DataTable data={duration_distribution}>
  <Column id="duration_bucket" title="Duration" />
  <Column id="session_count" title="Sessions" fmt="num0" />
  <Column id="avg_activity" title="Avg Activity" fmt="num1" />
</DataTable>

---

## Token Efficiency (Cost per Activity)

**Question**: What is the cost per unit of work accomplished?

```sql token_efficiency
SELECT
    da.agent_code,
    COUNT(DISTINCT faiw.agent_instance_tk) as sessions,
    SUM(faiw.lifecycle_event_count + faiw.ticket_activity_count + faiw.pr_activity_count) as total_activities,
    SUM(faic.total_token_cost_usd) as total_cost,
    CASE
        WHEN SUM(faiw.lifecycle_event_count + faiw.ticket_activity_count + faiw.pr_activity_count) > 0
        THEN SUM(faic.total_token_cost_usd) / SUM(faiw.lifecycle_event_count + faiw.ticket_activity_count + faiw.pr_activity_count)
        ELSE 0
    END as cost_per_activity
FROM herd_dm.fact_agent_instance_work faiw
JOIN herd_dm.dim_agent da
    ON faiw.agent_sk = da.agent_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
WHERE da.is_current = true
  AND NOT da.is_deleted
GROUP BY da.agent_code
HAVING SUM(faiw.lifecycle_event_count + faiw.ticket_activity_count + faiw.pr_activity_count) > 0
ORDER BY cost_per_activity ASC
```

<ScatterPlot
  data={token_efficiency}
  x="total_activities"
  y="cost_per_activity"
  series="agent_code"
  title="Cost per Activity vs Total Activities"
  xAxisTitle="Total Activities"
  yAxisTitle="Cost per Activity (USD)"
/>

<DataTable data={token_efficiency}>
  <Column id="agent_code" title="Agent" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="total_activities" title="Activities" fmt="num0" />
  <Column id="total_cost" title="Cost" fmt="usd2" />
  <Column id="cost_per_activity" title="Cost/Activity" fmt="usd4" />
</DataTable>

---

## Compaction Opportunities

**Question**: Which agents have long sessions with low activity (potential inefficiency)?

```sql compaction_opportunities
WITH session_stats AS (
    SELECT
        faiw.agent_instance_tk,
        da.agent_code,
        faiw.instance_duration_minutes,
        faiw.lifecycle_event_count + faiw.ticket_activity_count + faiw.pr_activity_count as total_activity,
        faic.total_token_input_count + faic.total_token_output_count as total_tokens
    FROM herd_dm.fact_agent_instance_work faiw
    JOIN herd_dm.dim_agent da
        ON faiw.agent_sk = da.agent_sk
    LEFT JOIN herd_dm.fact_agent_instance_cost faic
        ON faiw.agent_instance_tk = faic.agent_instance_tk
    WHERE da.is_current = true
      AND NOT da.is_deleted
      AND faiw.instance_duration_minutes IS NOT NULL
)
SELECT
    agent_code,
    COUNT(*) as low_efficiency_sessions,
    ROUND(AVG(instance_duration_minutes), 1) as avg_duration,
    ROUND(AVG(total_activity), 1) as avg_activity,
    ROUND(AVG(total_tokens), 0) as avg_tokens
FROM session_stats
WHERE instance_duration_minutes > 30
  AND total_activity < 5
GROUP BY agent_code
ORDER BY low_efficiency_sessions DESC
```

<DataTable data={compaction_opportunities}>
  <Column id="agent_code" title="Agent" />
  <Column id="low_efficiency_sessions" title="Long/Low Activity" fmt="num0" />
  <Column id="avg_duration" title="Avg Duration" fmt="num1" />
  <Column id="avg_activity" title="Avg Activity" fmt="num1" />
  <Column id="avg_tokens" title="Avg Tokens" fmt="num0" />
</DataTable>

---

## Activity Type Distribution

**Question**: What types of activities consume the most time?

```sql activity_type_distribution
SELECT
    'Lifecycle Events' as activity_type,
    SUM(faiw.lifecycle_event_count) as total_count,
    ROUND(AVG(faiw.lifecycle_event_count), 1) as avg_per_session
FROM herd_dm.fact_agent_instance_work faiw
UNION ALL
SELECT
    'Ticket Activities' as activity_type,
    SUM(faiw.ticket_activity_count) as total_count,
    ROUND(AVG(faiw.ticket_activity_count), 1) as avg_per_session
FROM herd_dm.fact_agent_instance_work faiw
UNION ALL
SELECT
    'PR Activities' as activity_type,
    SUM(faiw.pr_activity_count) as total_count,
    ROUND(AVG(faiw.pr_activity_count), 1) as avg_per_session
FROM herd_dm.fact_agent_instance_work faiw
ORDER BY total_count DESC
```

<BarChart
  data={activity_type_distribution}
  x="activity_type"
  y="total_count"
  title="Activity Type Distribution"
  xAxisTitle="Type"
  yAxisTitle="Count"
  series={[
    { name: 'Total', color: '#3B82F6' }
  ]}
/>

<DataTable data={activity_type_distribution}>
  <Column id="activity_type" title="Activity Type" />
  <Column id="total_count" title="Total" fmt="num0" />
  <Column id="avg_per_session" title="Avg/Session" fmt="num1" />
</DataTable>

---

## Efficiency Trend (Last 30 Days)

**Question**: Is operational efficiency improving over time?

```sql efficiency_trend
SELECT
    dd.date_actual as date,
    COUNT(DISTINCT faiw.agent_instance_tk) as sessions,
    ROUND(AVG(faiw.lifecycle_event_count + faiw.ticket_activity_count + faiw.pr_activity_count), 1) as avg_activity,
    ROUND(AVG(faiw.instance_duration_minutes), 1) as avg_duration,
    ROUND(AVG(faiw.lifecycle_event_count + faiw.ticket_activity_count + faiw.pr_activity_count) /
        NULLIF(AVG(faiw.instance_duration_minutes), 0) * 60, 2) as activities_per_hour
FROM herd_dm.dim_date dd
LEFT JOIN herd_dm.fact_agent_instance_work faiw
    ON CAST(strftime(faiw.agent_instance_started_at, '%Y%m%d') AS INTEGER) = dd.date_sk
WHERE dd.date_actual >= CURRENT_DATE - INTERVAL '30 days'
  AND dd.date_actual <= CURRENT_DATE
GROUP BY dd.date_actual
ORDER BY dd.date_actual
```

<LineChart
  data={efficiency_trend}
  x="date"
  y="activities_per_hour"
  yAxisTitle="Activities per Hour"
  title="Efficiency Trend (Activities/Hour)"
  series={[
    { name: 'Efficiency', color: '#10B981' }
  ]}
/>

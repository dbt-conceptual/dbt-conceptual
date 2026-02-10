# Prompt Effectiveness

> "The question shapes the answer." — Track prompt patterns, first-pass success, and craft correlation.

## Prompt Overview

**Question**: How successful are agent sessions at achieving their goals?

```sql prompt_overview
SELECT
    COUNT(DISTINCT faiw.agent_instance_tk) as total_sessions,
    SUM(CASE WHEN faiw.agent_instance_outcome = 'success' THEN 1 ELSE 0 END) as successful_sessions,
    ROUND(100.0 * SUM(CASE WHEN faiw.agent_instance_outcome = 'success' THEN 1 ELSE 0 END) / COUNT(DISTINCT faiw.agent_instance_tk), 1) as success_rate,
    COUNT(DISTINCT dt.ticket_tk) as tickets_worked,
    SUM(faic.total_token_cost_usd) as total_cost
FROM herd_dm.fact_agent_instance_work faiw
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
LEFT JOIN herd_dm.dim_ticket dt
    ON faiw.ticket_sk = dt.ticket_sk
```

<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
  <BigValue
    data={prompt_overview}
    value="total_sessions"
    title="Total Sessions"
  />

  <BigValue
    data={prompt_overview}
    value="successful_sessions"
    title="Successful"
  />

  <BigValue
    data={prompt_overview}
    value="success_rate"
    title="Success Rate"
    fmt="pct1"
  />

  <BigValue
    data={prompt_overview}
    value="total_cost"
    title="Total Cost"
    fmt="usd2"
  />
</div>

---

## First-Pass Success by Ticket Size

**Question**: Do smaller tickets have higher first-pass success rates?

```sql success_by_size
SELECT
    dt.ticket_tshirt_size,
    COUNT(DISTINCT faiw.agent_instance_tk) as sessions,
    SUM(CASE WHEN faiw.agent_instance_outcome = 'success' THEN 1 ELSE 0 END) as successes,
    ROUND(100.0 * SUM(CASE WHEN faiw.agent_instance_outcome = 'success' THEN 1 ELSE 0 END) / COUNT(DISTINCT faiw.agent_instance_tk), 1) as success_rate
FROM herd_dm.fact_agent_instance_work faiw
JOIN herd_dm.dim_ticket dt
    ON faiw.ticket_sk = dt.ticket_sk
WHERE dt.is_current = true
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
  data={success_by_size}
  x="ticket_tshirt_size"
  y="success_rate"
  title="Success Rate by Ticket Size"
  xAxisTitle="Size"
  yAxisTitle="Success Rate (%)"
  series={[
    { name: 'Success Rate', color: '#10B981' }
  ]}
/>

<DataTable data={success_by_size}>
  <Column id="ticket_tshirt_size" title="Size" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="successes" title="Successes" fmt="num0" />
  <Column id="success_rate" title="Success %" fmt="num1" />
</DataTable>

---

## Success Rate by Agent Role

**Question**: Which agent roles have the highest success rates?

```sql success_by_role
SELECT
    da.agent_role,
    COUNT(DISTINCT faiw.agent_instance_tk) as sessions,
    SUM(CASE WHEN faiw.agent_instance_outcome = 'success' THEN 1 ELSE 0 END) as successes,
    ROUND(100.0 * SUM(CASE WHEN faiw.agent_instance_outcome = 'success' THEN 1 ELSE 0 END) / COUNT(DISTINCT faiw.agent_instance_tk), 1) as success_rate,
    SUM(faic.total_token_cost_usd) as total_cost
FROM herd_dm.fact_agent_instance_work faiw
JOIN herd_dm.dim_agent da
    ON faiw.agent_sk = da.agent_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
WHERE da.is_current = true
  AND NOT da.is_deleted
GROUP BY da.agent_role
ORDER BY success_rate DESC
```

<BarChart
  data={success_by_role}
  x="agent_role"
  y="success_rate"
  title="Success Rate by Agent Role"
  xAxisTitle="Role"
  yAxisTitle="Success Rate (%)"
  series={[
    { name: 'Success Rate', color: '#3B82F6' }
  ]}
/>

<DataTable data={success_by_role}>
  <Column id="agent_role" title="Role" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="successes" title="Successes" fmt="num0" />
  <Column id="success_rate" title="Success %" fmt="num1" />
  <Column id="total_cost" title="Cost" fmt="usd2" />
</DataTable>

---

## Clean vs Churn (Session Outcomes)

**Question**: What are the most common session outcomes?

```sql session_outcomes
SELECT
    faiw.agent_instance_outcome,
    COUNT(*) as count,
    SUM(faic.total_token_cost_usd) as total_cost,
    ROUND(AVG(faiw.instance_duration_minutes), 1) as avg_duration
FROM herd_dm.fact_agent_instance_work faiw
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
WHERE faiw.agent_instance_outcome IS NOT NULL
GROUP BY faiw.agent_instance_outcome
ORDER BY count DESC
```

<BarChart
  data={session_outcomes}
  x="agent_instance_outcome"
  y="count"
  title="Sessions by Outcome"
  xAxisTitle="Outcome"
  yAxisTitle="Count"
  series={[
    { name: 'Sessions', color: '#8B5CF6' }
  ]}
/>

<DataTable data={session_outcomes}>
  <Column id="agent_instance_outcome" title="Outcome" />
  <Column id="count" title="Sessions" fmt="num0" />
  <Column id="total_cost" title="Cost" fmt="usd2" />
  <Column id="avg_duration" title="Avg Duration" fmt="num1" />
</DataTable>

---

## Craft Impact on Success

**Question**: Do specific craft standards correlate with higher success rates?

```sql craft_impact
SELECT
    dc.craft_code,
    dc.craft_description,
    COUNT(DISTINCT faiw.agent_instance_tk) as sessions,
    SUM(CASE WHEN faiw.agent_instance_outcome = 'success' THEN 1 ELSE 0 END) as successes,
    ROUND(100.0 * SUM(CASE WHEN faiw.agent_instance_outcome = 'success' THEN 1 ELSE 0 END) / COUNT(DISTINCT faiw.agent_instance_tk), 1) as success_rate
FROM herd_dm.fact_agent_instance_work faiw
JOIN herd_dm.dim_craft dc
    ON faiw.craft_sk = dc.craft_sk
GROUP BY dc.craft_code, dc.craft_description
ORDER BY success_rate DESC
```

<DataTable data={craft_impact} search=true>
  <Column id="craft_code" title="Craft Code" />
  <Column id="craft_description" title="Description" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="successes" title="Successes" fmt="num0" />
  <Column id="success_rate" title="Success %" fmt="num1" />
</DataTable>

---

## Success Trend (Last 30 Days)

**Question**: Is prompt quality improving over time?

```sql success_trend
SELECT
    dd.date_actual as date,
    COUNT(DISTINCT faiw.agent_instance_tk) as sessions,
    SUM(CASE WHEN faiw.agent_instance_outcome = 'success' THEN 1 ELSE 0 END) as successes,
    ROUND(100.0 * SUM(CASE WHEN faiw.agent_instance_outcome = 'success' THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT faiw.agent_instance_tk), 0), 1) as success_rate
FROM herd_dm.dim_date dd
LEFT JOIN herd_dm.fact_agent_instance_work faiw
    ON CAST(strftime(faiw.agent_instance_started_at, '%Y%m%d') AS INTEGER) = dd.date_sk
WHERE dd.date_actual >= CURRENT_DATE - INTERVAL '30 days'
  AND dd.date_actual <= CURRENT_DATE
GROUP BY dd.date_actual
ORDER BY dd.date_actual
```

<LineChart
  data={success_trend}
  x="date"
  y="success_rate"
  y2="sessions"
  yAxisTitle="Success Rate (%)"
  y2AxisTitle="Session Count"
  title="Success Rate Trend"
  series={[
    { name: 'Success Rate', color: '#10B981' },
    { name: 'Sessions', color: '#3B82F6' }
  ]}
/>

---

## Correlation: First-Pass QA vs Prompt Quality

**Question**: Does initial session success predict QA pass rate?

```sql qa_prompt_correlation
WITH first_session_per_ticket AS (
    SELECT
        dt.ticket_tk,
        dt.ticket_code,
        faiw.agent_instance_tk,
        faiw.agent_instance_outcome,
        ROW_NUMBER() OVER (PARTITION BY dt.ticket_tk ORDER BY faiw.agent_instance_started_at) as rn
    FROM herd_dm.dim_ticket dt
    JOIN herd_dm.fact_agent_instance_work faiw
        ON dt.ticket_sk = faiw.ticket_sk
    WHERE dt.is_current = true
      AND NOT dt.is_deleted
),
first_review_per_ticket AS (
    SELECT
        dpr.ticket_code,
        frq.review_round,
        frq.review_verdict,
        ROW_NUMBER() OVER (PARTITION BY dpr.ticket_code ORDER BY frq.review_completed_at) as rn
    FROM herd_dm.fact_review_quality frq
    JOIN herd_dm.dim_pull_request dpr
        ON frq.pull_request_sk = dpr.pull_request_sk
)
SELECT
    fs.agent_instance_outcome as prompt_quality,
    COUNT(*) as ticket_count,
    SUM(CASE WHEN fr.review_round = 1 AND fr.review_verdict = 'approved' THEN 1 ELSE 0 END) as first_pass_qa,
    ROUND(100.0 * SUM(CASE WHEN fr.review_round = 1 AND fr.review_verdict = 'approved' THEN 1 ELSE 0 END) / COUNT(*), 1) as first_pass_rate
FROM first_session_per_ticket fs
LEFT JOIN first_review_per_ticket fr
    ON fs.ticket_code = fr.ticket_code
    AND fr.rn = 1
WHERE fs.rn = 1
  AND fs.agent_instance_outcome IS NOT NULL
GROUP BY fs.agent_instance_outcome
ORDER BY first_pass_rate DESC
```

<BarChart
  data={qa_prompt_correlation}
  x="prompt_quality"
  y="first_pass_rate"
  title="First-Pass QA Rate by Initial Prompt Quality"
  xAxisTitle="Initial Session Outcome"
  yAxisTitle="QA First-Pass Rate (%)"
  series={[
    { name: 'First-Pass QA', color: '#10B981' }
  ]}
/>

<DataTable data={qa_prompt_correlation}>
  <Column id="prompt_quality" title="Prompt Quality" />
  <Column id="ticket_count" title="Tickets" fmt="num0" />
  <Column id="first_pass_qa" title="QA Pass" fmt="num0" />
  <Column id="first_pass_rate" title="Pass %" fmt="num1" />
</DataTable>

---

## Model Performance by Outcome

**Question**: Which models achieve the highest success rates?

```sql model_outcomes
SELECT
    dm.model_code,
    COUNT(DISTINCT faiw.agent_instance_tk) as sessions,
    SUM(CASE WHEN faiw.agent_instance_outcome = 'success' THEN 1 ELSE 0 END) as successes,
    ROUND(100.0 * SUM(CASE WHEN faiw.agent_instance_outcome = 'success' THEN 1 ELSE 0 END) / COUNT(DISTINCT faiw.agent_instance_tk), 1) as success_rate,
    SUM(faic.total_token_cost_usd) as total_cost
FROM herd_dm.fact_agent_instance_work faiw
JOIN herd_dm.dim_model dm
    ON faiw.model_sk = dm.model_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
GROUP BY dm.model_code
ORDER BY success_rate DESC
```

<DataTable data={model_outcomes}>
  <Column id="model_code" title="Model" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="successes" title="Successes" fmt="num0" />
  <Column id="success_rate" title="Success %" fmt="num1" />
  <Column id="total_cost" title="Cost" fmt="usd2" />
</DataTable>

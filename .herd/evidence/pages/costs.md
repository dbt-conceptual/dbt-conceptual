# Token Economics

> "Every brushstroke has a price." — Track costs, efficiency, and spending patterns.

## Cost Summary

```sql cost_summary
SELECT
    SUM(faic.total_token_cost_usd) as total_cost,
    SUM(faic.total_token_input_count + faic.total_token_output_count) as total_tokens,
    COUNT(DISTINCT faic.agent_instance_tk) as total_sessions,
    COUNT(DISTINCT dt.ticket_tk) as tickets_worked,
    ROUND(SUM(faic.total_token_cost_usd) / NULLIF(COUNT(DISTINCT dt.ticket_tk), 0), 2) as cost_per_ticket,
    ROUND(SUM(faic.total_token_cost_usd) / NULLIF(COUNT(DISTINCT faic.agent_instance_tk), 0), 4) as cost_per_session
FROM herd_dm.fact_agent_instance_cost faic
LEFT JOIN herd_dm.dim_ticket dt
    ON faic.ticket_sk = dt.ticket_sk
```

<div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
  <BigValue
    data={cost_summary}
    value="total_cost"
    title="Total Cost"
    fmt="usd"
  />

  <BigValue
    data={cost_summary}
    value="cost_per_ticket"
    title="Cost per Ticket"
    fmt="usd2"
  />

  <BigValue
    data={cost_summary}
    value="cost_per_session"
    title="Cost per Session"
    fmt="usd4"
  />
</div>

---

## Daily Cost Trend (Last 60 Days)

```sql daily_cost
SELECT
    dd.date_actual as date,
    COALESCE(SUM(faic.total_token_cost_usd), 0) as daily_cost,
    SUM(COALESCE(SUM(faic.total_token_cost_usd), 0)) OVER (
        ORDER BY dd.date_actual
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cumulative_cost
FROM herd_dm.dim_date dd
LEFT JOIN herd_dm.fact_agent_instance_work faiw
    ON CAST(strftime(faiw.agent_instance_started_at, '%Y%m%d') AS INTEGER) = dd.date_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
WHERE dd.date_actual >= CURRENT_DATE - INTERVAL '60 days'
  AND dd.date_actual <= CURRENT_DATE
GROUP BY dd.date_actual
ORDER BY dd.date_actual
```

<LineChart
  data={daily_cost}
  x="date"
  y="daily_cost"
  y2="cumulative_cost"
  yAxisTitle="Daily Cost (USD)"
  y2AxisTitle="Cumulative Cost (USD)"
  title="Daily & Cumulative Costs"
  series={[
    { name: 'Daily Cost', color: '#EF4444' },
    { name: 'Cumulative', color: '#8B5CF6' }
  ]}
/>

---

## Cost by Model

```sql cost_by_model
SELECT
    dm.model_code,
    dm.model_provider,
    COUNT(DISTINCT faic.agent_instance_tk) as sessions,
    SUM(faic.total_token_input_count) as input_tokens,
    SUM(faic.total_token_output_count) as output_tokens,
    SUM(faic.total_token_cache_read_count) as cache_read_tokens,
    SUM(faic.total_token_cache_create_count) as cache_create_tokens,
    SUM(faic.total_token_cost_usd) as total_cost,
    ROUND(AVG(faic.total_token_cost_usd), 4) as avg_cost_per_session
FROM herd_dm.fact_agent_instance_cost faic
JOIN herd_dm.dim_model dm
    ON faic.model_sk = dm.model_sk
GROUP BY dm.model_code, dm.model_provider
ORDER BY total_cost DESC
```

<BarChart
  data={cost_by_model}
  x="model_code"
  y="total_cost"
  title="Total Cost by Model"
  xAxisTitle="Model"
  yAxisTitle="Cost (USD)"
  series={[
    { name: 'Cost', color: '#EF4444' }
  ]}
/>

<DataTable data={cost_by_model}>
  <Column id="model_code" title="Model" />
  <Column id="model_provider" title="Provider" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="input_tokens" title="Input" fmt="num0" />
  <Column id="output_tokens" title="Output" fmt="num0" />
  <Column id="cache_read_tokens" title="Cache Read" fmt="num0" />
  <Column id="cache_create_tokens" title="Cache Create" fmt="num0" />
  <Column id="total_cost" title="Cost" fmt="usd2" />
  <Column id="avg_cost_per_session" title="Avg/Session" fmt="usd4" />
</DataTable>

---

## Cache Efficiency

```sql cache_efficiency
SELECT
    dd.date_actual as date,
    SUM(faic.total_token_input_count + faic.total_token_output_count) as direct_tokens,
    SUM(faic.total_token_cache_read_count + faic.total_token_cache_create_count) as cache_tokens,
    ROUND(100.0 * SUM(faic.total_token_cache_read_count + faic.total_token_cache_create_count) /
        NULLIF(SUM(faic.total_token_input_count + faic.total_token_output_count + faic.total_token_cache_read_count + faic.total_token_cache_create_count), 0), 1) as cache_ratio
FROM herd_dm.dim_date dd
LEFT JOIN herd_dm.fact_agent_instance_work faiw
    ON CAST(strftime(faiw.agent_instance_started_at, '%Y%m%d') AS INTEGER) = dd.date_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
WHERE dd.date_actual >= CURRENT_DATE - INTERVAL '30 days'
  AND dd.date_actual <= CURRENT_DATE
GROUP BY dd.date_actual
ORDER BY dd.date_actual
```

<LineChart
  data={cache_efficiency}
  x="date"
  y="cache_ratio"
  yAxisTitle="Cache Ratio (%)"
  title="Cache Utilization Trend"
  series={[
    { name: 'Cache Ratio', color: '#10B981' }
  ]}
/>

---

## Cost per Line of Code

```sql cost_per_line
SELECT
    dd.date_actual as date,
    SUM(fpd.pr_lines_added + fpd.pr_lines_deleted) as total_lines,
    SUM(faic.total_token_cost_usd) as total_cost,
    CASE
        WHEN SUM(fpd.pr_lines_added + fpd.pr_lines_deleted) > 0
        THEN SUM(faic.total_token_cost_usd) / SUM(fpd.pr_lines_added + fpd.pr_lines_deleted)
        ELSE 0
    END as cost_per_line
FROM herd_dm.dim_date dd
LEFT JOIN herd_dm.fact_pr_delivery fpd
    ON CAST(strftime(fpd.pr_merged_at, '%Y%m%d') AS INTEGER) = dd.date_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON fpd.agent_sk = faic.agent_sk
WHERE dd.date_actual >= CURRENT_DATE - INTERVAL '30 days'
  AND dd.date_actual <= CURRENT_DATE
  AND fpd.pr_merged_at IS NOT NULL
GROUP BY dd.date_actual
HAVING SUM(fpd.pr_lines_added + fpd.pr_lines_deleted) > 0
ORDER BY dd.date_actual
```

<LineChart
  data={cost_per_line}
  x="date"
  y="cost_per_line"
  yAxisTitle="Cost per Line (USD)"
  title="Cost per Line Trend"
  series={[
    { name: 'Cost/Line', color: '#F59E0B' }
  ]}
/>

---

## Cost Projection (30 Days)

```sql cost_projection
WITH recent_costs AS (
    SELECT
        dd.date_actual,
        COALESCE(SUM(faic.total_token_cost_usd), 0) as daily_cost
    FROM herd_dm.dim_date dd
    LEFT JOIN herd_dm.fact_agent_instance_work faiw
        ON CAST(strftime(faiw.agent_instance_started_at, '%Y%m%d') AS INTEGER) = dd.date_sk
    LEFT JOIN herd_dm.fact_agent_instance_cost faic
        ON faiw.agent_instance_tk = faic.agent_instance_tk
    WHERE dd.date_actual >= CURRENT_DATE - INTERVAL '30 days'
      AND dd.date_actual < CURRENT_DATE
    GROUP BY dd.date_actual
)
SELECT
    AVG(daily_cost) as avg_daily_cost,
    AVG(daily_cost) * 30 as projected_monthly_cost,
    AVG(daily_cost) * 365 as projected_annual_cost
FROM recent_costs
```

<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
  <BigValue
    data={cost_projection}
    value="avg_daily_cost"
    title="Avg Daily Cost"
    fmt="usd2"
  />

  <BigValue
    data={cost_projection}
    value="projected_monthly_cost"
    title="Projected Monthly"
    fmt="usd"
  />

  <BigValue
    data={cost_projection}
    value="projected_annual_cost"
    title="Projected Annual"
    fmt="usd"
  />
</div>

---

## Most Expensive Tickets

```sql expensive_tickets
SELECT
    dt.ticket_code,
    dt.ticket_title,
    dt.ticket_tshirt_size,
    COUNT(DISTINCT faic.agent_instance_tk) as sessions,
    SUM(faic.total_token_input_count + faic.total_token_output_count) as total_tokens,
    SUM(faic.total_token_cost_usd) as total_cost
FROM herd_dm.dim_ticket dt
JOIN herd_dm.fact_agent_instance_cost faic
    ON dt.ticket_sk = faic.ticket_sk
WHERE dt.is_current = true
  AND NOT dt.is_deleted
GROUP BY dt.ticket_code, dt.ticket_title, dt.ticket_tshirt_size
ORDER BY total_cost DESC
LIMIT 20
```

<DataTable data={expensive_tickets} search=true>
  <Column id="ticket_code" title="Ticket" />
  <Column id="ticket_title" title="Title" />
  <Column id="ticket_tshirt_size" title="Size" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="total_tokens" title="Tokens" fmt="num0" />
  <Column id="total_cost" title="Cost" fmt="usd2" />
</DataTable>

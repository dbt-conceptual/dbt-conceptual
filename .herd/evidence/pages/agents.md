# Agent Performance

> "Every stroke reveals the artist's hand." — Track agent output, quality, and efficiency.

## Agent Summary

**Question**: Which agents are delivering the most value relative to their cost?

```sql agent_summary
SELECT
    da.agent_code,
    da.agent_role,
    da.agent_status,
    COUNT(DISTINCT faiw.agent_instance_tk) as total_sessions,
    COUNT(DISTINCT CASE WHEN faiw.agent_instance_outcome = 'success' THEN faiw.agent_instance_tk END) as successful_sessions,
    COUNT(DISTINCT dt.ticket_tk) as tickets_worked,
    SUM(faic.total_token_input_count + faic.total_token_output_count) as total_tokens,
    SUM(faic.total_token_cost_usd) as total_cost,
    ROUND(AVG(faiw.instance_duration_minutes), 1) as avg_session_minutes
FROM herd_dm.dim_agent da
LEFT JOIN herd_dm.fact_agent_instance_work faiw
    ON da.agent_sk = faiw.agent_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
LEFT JOIN herd_dm.dim_ticket dt
    ON faiw.ticket_sk = dt.ticket_sk
WHERE da.is_current = true
  AND NOT da.is_deleted
GROUP BY da.agent_code, da.agent_role, da.agent_status
ORDER BY total_cost DESC NULLS LAST
```

<DataTable data={agent_summary} search=true>
  <Column id="agent_code" title="Agent" />
  <Column id="agent_role" title="Role" />
  <Column id="agent_status" title="Status" />
  <Column id="total_sessions" title="Sessions" fmt="num0" />
  <Column id="successful_sessions" title="Success" fmt="num0" />
  <Column id="tickets_worked" title="Tickets" fmt="num0" />
  <Column id="total_tokens" title="Tokens" fmt="num0" />
  <Column id="total_cost" title="Cost" fmt="usd2" />
  <Column id="avg_session_minutes" title="Avg Minutes" fmt="num1" />
</DataTable>

---

## QA Pass Rates by Agent

**Question**: Which agents produce clean code that passes QA on the first attempt?

```sql qa_pass_rates
SELECT
    da.agent_code,
    da.agent_role,
    COUNT(DISTINCT frq.review_submission_tk) as total_reviews,
    SUM(CASE WHEN frq.review_round = 1 AND frq.review_verdict = 'approved' THEN 1 ELSE 0 END) as first_pass_approvals,
    SUM(CASE WHEN frq.review_verdict = 'approved' THEN 1 ELSE 0 END) as total_approvals,
    ROUND(100.0 * SUM(CASE WHEN frq.review_round = 1 AND frq.review_verdict = 'approved' THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT CASE WHEN frq.review_round = 1 THEN frq.review_submission_tk END), 0), 1) as first_pass_rate,
    ROUND(AVG(frq.finding_count), 1) as avg_findings_per_review
FROM herd_dm.dim_agent da
LEFT JOIN herd_dm.fact_review_quality frq
    ON da.agent_sk = frq.agent_sk
WHERE da.is_current = true
  AND NOT da.is_deleted
  AND frq.review_submission_tk IS NOT NULL
GROUP BY da.agent_code, da.agent_role
ORDER BY first_pass_rate DESC NULLS LAST
```

<BarChart
  data={qa_pass_rates}
  x="agent_code"
  y="first_pass_rate"
  title="First-Pass QA Rate by Agent (%)"
  xAxisTitle="Agent"
  yAxisTitle="First-Pass Rate (%)"
  series={[
    { name: 'First-Pass Rate', color: '#10B981' }
  ]}
/>

<DataTable data={qa_pass_rates}>
  <Column id="agent_code" title="Agent" />
  <Column id="agent_role" title="Role" />
  <Column id="total_reviews" title="Reviews" fmt="num0" />
  <Column id="first_pass_approvals" title="1st Pass" fmt="num0" />
  <Column id="total_approvals" title="Total" fmt="num0" />
  <Column id="first_pass_rate" title="1st Pass %" fmt="num1" />
  <Column id="avg_findings_per_review" title="Avg Findings" fmt="num1" />
</DataTable>

---

## Cost Efficiency by Agent

**Question**: What is the cost per line of code for each agent?

```sql cost_efficiency
SELECT
    da.agent_code,
    dm.model_code,
    COUNT(DISTINCT fpd.pull_request_sk) as prs_delivered,
    SUM(fpd.pr_lines_added + fpd.pr_lines_deleted) as total_lines,
    SUM(faic.total_token_cost_usd) as total_cost,
    CASE
        WHEN SUM(fpd.pr_lines_added + fpd.pr_lines_deleted) > 0
        THEN SUM(faic.total_token_cost_usd) / SUM(fpd.pr_lines_added + fpd.pr_lines_deleted)
        ELSE 0
    END as cost_per_line
FROM herd_dm.dim_agent da
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON da.agent_sk = faic.agent_sk
LEFT JOIN herd_dm.dim_model dm
    ON faic.model_sk = dm.model_sk
LEFT JOIN herd_dm.fact_pr_delivery fpd
    ON faic.agent_sk = fpd.agent_sk
WHERE da.is_current = true
  AND NOT da.is_deleted
  AND fpd.pr_merged_at IS NOT NULL
GROUP BY da.agent_code, dm.model_code
HAVING SUM(fpd.pr_lines_added + fpd.pr_lines_deleted) > 0
ORDER BY cost_per_line ASC
```

<ScatterPlot
  data={cost_efficiency}
  x="total_lines"
  y="cost_per_line"
  series="agent_code"
  title="Cost per Line vs Total Lines by Agent"
  xAxisTitle="Total Lines Changed"
  yAxisTitle="Cost per Line (USD)"
/>

<DataTable data={cost_efficiency}>
  <Column id="agent_code" title="Agent" />
  <Column id="model_code" title="Model" />
  <Column id="prs_delivered" title="PRs" fmt="num0" />
  <Column id="total_lines" title="Lines" fmt="num0" />
  <Column id="total_cost" title="Cost" fmt="usd2" />
  <Column id="cost_per_line" title="Cost/Line" fmt="usd4" />
</DataTable>

---

## Model Comparison by Agent

**Question**: How do model choices affect agent costs?

```sql model_usage
SELECT
    da.agent_code,
    dm.model_code,
    dm.model_provider,
    COUNT(DISTINCT faic.agent_instance_tk) as sessions,
    SUM(faic.total_token_input_count + faic.total_token_output_count) as total_tokens,
    SUM(faic.total_token_cost_usd) as total_cost,
    ROUND(AVG(faic.total_token_cost_usd), 4) as avg_cost_per_session
FROM herd_dm.dim_agent da
JOIN herd_dm.fact_agent_instance_cost faic
    ON da.agent_sk = faic.agent_sk
JOIN herd_dm.dim_model dm
    ON faic.model_sk = dm.model_sk
WHERE da.is_current = true
  AND NOT da.is_deleted
GROUP BY da.agent_code, dm.model_code, dm.model_provider
ORDER BY da.agent_code, total_cost DESC
```

<BarChart
  data={model_usage}
  x="agent_code"
  y="total_cost"
  series="model_code"
  type="stacked"
  title="Cost by Agent and Model"
  xAxisTitle="Agent"
  yAxisTitle="Total Cost (USD)"
/>

<DataTable data={model_usage}>
  <Column id="agent_code" title="Agent" />
  <Column id="model_code" title="Model" />
  <Column id="model_provider" title="Provider" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="total_tokens" title="Tokens" fmt="num0" />
  <Column id="total_cost" title="Cost" fmt="usd2" />
  <Column id="avg_cost_per_session" title="Avg/Session" fmt="usd4" />
</DataTable>

---

## Agent Craft Assignments

**Question**: What craft (role specialization) has each agent performed?

```sql agent_crafts
SELECT
    da.agent_code,
    da.agent_role,
    dc.craft_code,
    dc.craft_description,
    COUNT(DISTINCT faiw.agent_instance_tk) as instance_count
FROM herd_dm.dim_agent da
LEFT JOIN herd_dm.fact_agent_instance_work faiw
    ON da.agent_sk = faiw.agent_sk
LEFT JOIN herd_dm.dim_craft dc
    ON faiw.craft_sk = dc.craft_sk
WHERE da.is_current = true
  AND NOT da.is_deleted
  AND dc.craft_code IS NOT NULL
GROUP BY da.agent_code, da.agent_role, dc.craft_code, dc.craft_description
ORDER BY da.agent_code, instance_count DESC
```

<DataTable data={agent_crafts} search=true>
  <Column id="agent_code" title="Agent" />
  <Column id="agent_role" title="Role" />
  <Column id="craft_code" title="Craft" />
  <Column id="craft_description" title="Description" />
  <Column id="instance_count" title="Instances" fmt="num0" />
</DataTable>

---

## Agent Work Distribution

**Question**: How active is each agent across different activity types?

```sql work_distribution
SELECT
    da.agent_code,
    COUNT(DISTINCT faiw.agent_instance_tk) as session_count,
    SUM(faiw.instance_duration_minutes) as total_minutes,
    SUM(faiw.lifecycle_event_count) as lifecycle_events,
    SUM(faiw.ticket_activity_count) as ticket_activities,
    SUM(faiw.pr_activity_count) as pr_activities
FROM herd_dm.dim_agent da
LEFT JOIN herd_dm.fact_agent_instance_work faiw
    ON da.agent_sk = faiw.agent_sk
WHERE da.is_current = true
  AND NOT da.is_deleted
GROUP BY da.agent_code
ORDER BY total_minutes DESC NULLS LAST
```

<BarChart
  data={work_distribution}
  x="agent_code"
  y="session_count"
  title="Session Count by Agent"
  xAxisTitle="Agent"
  yAxisTitle="Sessions"
  series={[
    { name: 'Sessions', color: '#3B82F6' }
  ]}
/>

<DataTable data={work_distribution}>
  <Column id="agent_code" title="Agent" />
  <Column id="session_count" title="Sessions" fmt="num0" />
  <Column id="total_minutes" title="Minutes" fmt="num0" />
  <Column id="lifecycle_events" title="Lifecycle" fmt="num0" />
  <Column id="ticket_activities" title="Ticket Activity" fmt="num0" />
  <Column id="pr_activities" title="PR Activity" fmt="num0" />
</DataTable>

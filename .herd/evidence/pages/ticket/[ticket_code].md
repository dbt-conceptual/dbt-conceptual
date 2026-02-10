# Ticket Deep Dive: {inputs.ticket_code}

> "Every masterpiece tells its own story." — Track ticket lifecycle, sessions, reviews, and costs.

## Ticket Details

```sql ticket_details
SELECT
    dt.ticket_code,
    dt.ticket_title,
    dt.ticket_description,
    dt.ticket_tshirt_size,
    dt.ticket_current_status,
    dt.current_sprint_code,
    dt.project_code,
    dt.valid_from as created_at
FROM herd_dm.dim_ticket dt
WHERE dt.ticket_code = '${inputs.ticket_code}'
  AND dt.is_current = true
```

<BigValue
  data={ticket_details}
  value="ticket_title"
  title="Ticket Title"
/>

<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
  <BigValue
    data={ticket_details}
    value="ticket_current_status"
    title="Status"
  />

  <BigValue
    data={ticket_details}
    value="ticket_tshirt_size"
    title="Size"
  />

  <BigValue
    data={ticket_details}
    value="current_sprint_code"
    title="Sprint"
  />

  <BigValue
    data={ticket_details}
    value="project_code"
    title="Project"
  />
</div>

---

## Ticket Summary

```sql ticket_summary
SELECT
    COUNT(DISTINCT faiw.agent_instance_tk) as total_sessions,
    COUNT(DISTINCT da.agent_code) as agents_involved,
    COUNT(DISTINCT fpd.pull_request_sk) as prs_created,
    COUNT(DISTINCT frq.review_submission_tk) as reviews_conducted,
    SUM(faic.total_token_cost_usd) as total_cost,
    SUM(fpd.pr_lines_added + fpd.pr_lines_deleted) as total_lines_changed
FROM herd_dm.dim_ticket dt
LEFT JOIN herd_dm.fact_agent_instance_work faiw
    ON dt.ticket_sk = faiw.ticket_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
LEFT JOIN herd_dm.dim_agent da
    ON faiw.agent_sk = da.agent_sk
LEFT JOIN herd_dm.fact_pr_delivery fpd
    ON dt.ticket_sk = fpd.ticket_sk
LEFT JOIN herd_dm.fact_review_quality frq
    ON fpd.pull_request_sk = frq.pull_request_sk
WHERE dt.ticket_code = '${inputs.ticket_code}'
  AND dt.is_current = true
```

<div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
  <BigValue
    data={ticket_summary}
    value="total_sessions"
    title="Sessions"
  />

  <BigValue
    data={ticket_summary}
    value="agents_involved"
    title="Agents"
  />

  <BigValue
    data={ticket_summary}
    value="total_cost"
    title="Total Cost"
    fmt="usd2"
  />
</div>

<div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
  <BigValue
    data={ticket_summary}
    value="prs_created"
    title="PRs"
  />

  <BigValue
    data={ticket_summary}
    value="reviews_conducted"
    title="Reviews"
  />

  <BigValue
    data={ticket_summary}
    value="total_lines_changed"
    title="Lines Changed"
  />
</div>

---

## Ticket Lifecycle

```sql ticket_lifecycle
SELECT
    ftl.event_ts,
    ftl.ticket_event_type,
    ftl.previous_status,
    ftl.ticket_status,
    da.agent_code,
    ftl.time_in_previous_status_minutes,
    ftl.sprint_code,
    ftl.blocker_ticket_code
FROM herd_dm.fact_ticket_lifecycle ftl
JOIN herd_dm.dim_ticket dt
    ON ftl.ticket_sk = dt.ticket_sk
LEFT JOIN herd_dm.dim_agent da
    ON ftl.agent_sk = da.agent_sk
WHERE dt.ticket_code = '${inputs.ticket_code}'
  AND dt.is_current = true
ORDER BY ftl.event_ts
```

<DataTable data={ticket_lifecycle}>
  <Column id="event_ts" title="Time" fmt="datetime" />
  <Column id="ticket_event_type" title="Event" />
  <Column id="previous_status" title="From" />
  <Column id="ticket_status" title="To" />
  <Column id="agent_code" title="Agent" />
  <Column id="time_in_previous_status_minutes" title="Duration (min)" fmt="num1" />
  <Column id="sprint_code" title="Sprint" />
  <Column id="blocker_ticket_code" title="Blocker" />
</DataTable>

---

## Agent Sessions

```sql agent_sessions
SELECT
    da.agent_code,
    da.agent_role,
    faiw.agent_instance_code,
    faiw.agent_instance_started_at,
    faiw.agent_instance_ended_at,
    faiw.instance_duration_minutes,
    faiw.agent_instance_outcome,
    dm.model_code,
    faic.total_token_input_count + faic.total_token_output_count as total_tokens,
    faic.total_token_cost_usd as cost
FROM herd_dm.fact_agent_instance_work faiw
JOIN herd_dm.dim_ticket dt
    ON faiw.ticket_sk = dt.ticket_sk
LEFT JOIN herd_dm.dim_agent da
    ON faiw.agent_sk = da.agent_sk
LEFT JOIN herd_dm.dim_model dm
    ON faiw.model_sk = dm.model_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
WHERE dt.ticket_code = '${inputs.ticket_code}'
  AND dt.is_current = true
ORDER BY faiw.agent_instance_started_at
```

<DataTable data={agent_sessions}>
  <Column id="agent_code" title="Agent" />
  <Column id="agent_role" title="Role" />
  <Column id="agent_instance_code" title="Instance" />
  <Column id="agent_instance_started_at" title="Started" fmt="datetime" />
  <Column id="agent_instance_ended_at" title="Ended" fmt="datetime" />
  <Column id="instance_duration_minutes" title="Duration" fmt="num1" />
  <Column id="agent_instance_outcome" title="Outcome" />
  <Column id="model_code" title="Model" />
  <Column id="total_tokens" title="Tokens" fmt="num0" />
  <Column id="cost" title="Cost" fmt="usd4" />
</DataTable>

---

## Review History

```sql review_history
SELECT
    frq.review_completed_at,
    da.agent_code as reviewer,
    frq.review_round,
    frq.review_verdict,
    frq.review_duration_minutes,
    frq.finding_count,
    frq.blocking_finding_count,
    frq.advisory_finding_count,
    dpr.pr_code
FROM herd_dm.fact_review_quality frq
JOIN herd_dm.dim_pull_request dpr
    ON frq.pull_request_sk = dpr.pull_request_sk
LEFT JOIN herd_dm.dim_agent da
    ON frq.agent_sk = da.agent_sk
WHERE dpr.ticket_code = '${inputs.ticket_code}'
ORDER BY frq.review_completed_at
```

<DataTable data={review_history}>
  <Column id="review_completed_at" title="Completed" fmt="datetime" />
  <Column id="reviewer" title="Reviewer" />
  <Column id="pr_code" title="PR" />
  <Column id="review_round" title="Round" fmt="num0" />
  <Column id="review_verdict" title="Verdict" />
  <Column id="finding_count" title="Findings" fmt="num0" />
  <Column id="blocking_finding_count" title="Blocking" fmt="num0" />
  <Column id="advisory_finding_count" title="Advisory" fmt="num0" />
  <Column id="review_duration_minutes" title="Duration" fmt="num1" />
</DataTable>

---

## Cost Breakdown by Agent

```sql cost_by_agent
SELECT
    da.agent_code,
    da.agent_role,
    dm.model_code,
    COUNT(DISTINCT faiw.agent_instance_tk) as sessions,
    SUM(faic.total_token_input_count) as input_tokens,
    SUM(faic.total_token_output_count) as output_tokens,
    SUM(faic.total_token_cache_read_count) as cache_read_tokens,
    SUM(faic.total_token_cost_usd) as total_cost
FROM herd_dm.fact_agent_instance_work faiw
JOIN herd_dm.dim_ticket dt
    ON faiw.ticket_sk = dt.ticket_sk
LEFT JOIN herd_dm.dim_agent da
    ON faiw.agent_sk = da.agent_sk
LEFT JOIN herd_dm.dim_model dm
    ON faiw.model_sk = dm.model_sk
LEFT JOIN herd_dm.fact_agent_instance_cost faic
    ON faiw.agent_instance_tk = faic.agent_instance_tk
WHERE dt.ticket_code = '${inputs.ticket_code}'
  AND dt.is_current = true
GROUP BY da.agent_code, da.agent_role, dm.model_code
ORDER BY total_cost DESC
```

<BarChart
  data={cost_by_agent}
  x="agent_code"
  y="total_cost"
  title="Cost by Agent"
  xAxisTitle="Agent"
  yAxisTitle="Cost (USD)"
  series={[
    { name: 'Cost', color: '#EF4444' }
  ]}
/>

<DataTable data={cost_by_agent}>
  <Column id="agent_code" title="Agent" />
  <Column id="agent_role" title="Role" />
  <Column id="model_code" title="Model" />
  <Column id="sessions" title="Sessions" fmt="num0" />
  <Column id="input_tokens" title="Input" fmt="num0" />
  <Column id="output_tokens" title="Output" fmt="num0" />
  <Column id="cache_read_tokens" title="Cache" fmt="num0" />
  <Column id="total_cost" title="Cost" fmt="usd4" />
</DataTable>

---

## Pull Requests

```sql pull_requests
SELECT
    dpr.pr_code,
    dpr.pr_title,
    dpr.pr_branch_name,
    fpd.pr_merged_at,
    dpr.pr_lines_added,
    dpr.pr_lines_deleted,
    dpr.pr_files_changed,
    da.agent_code as author
FROM herd_dm.fact_pr_delivery fpd
JOIN herd_dm.dim_pull_request dpr
    ON fpd.pull_request_sk = dpr.pull_request_sk
LEFT JOIN herd_dm.dim_agent da
    ON fpd.agent_sk = da.agent_sk
WHERE dpr.ticket_code = '${inputs.ticket_code}'
ORDER BY fpd.pr_merged_at DESC NULLS LAST
```

<DataTable data={pull_requests}>
  <Column id="pr_code" title="PR" />
  <Column id="pr_title" title="Title" />
  <Column id="author" title="Author" />
  <Column id="pr_branch_name" title="Branch" />
  <Column id="pr_merged_at" title="Merged" fmt="datetime" />
  <Column id="pr_lines_added" title="Added" fmt="num0" />
  <Column id="pr_lines_deleted" title="Deleted" fmt="num0" />
  <Column id="pr_files_changed" title="Files" fmt="num0" />
</DataTable>

---

## Time Distribution

```sql time_distribution
SELECT
    ftl.previous_status,
    SUM(ftl.time_in_previous_status_minutes) as total_minutes,
    ROUND(AVG(ftl.time_in_previous_status_minutes), 1) as avg_minutes
FROM herd_dm.fact_ticket_lifecycle ftl
JOIN herd_dm.dim_ticket dt
    ON ftl.ticket_sk = dt.ticket_sk
WHERE dt.ticket_code = '${inputs.ticket_code}'
  AND dt.is_current = true
  AND ftl.time_in_previous_status_minutes IS NOT NULL
  AND ftl.previous_status IS NOT NULL
GROUP BY ftl.previous_status
ORDER BY total_minutes DESC
```

<BarChart
  data={time_distribution}
  x="previous_status"
  y="total_minutes"
  title="Time Spent in Each Status"
  xAxisTitle="Status"
  yAxisTitle="Minutes"
  series={[
    { name: 'Time', color: '#8B5CF6' }
  ]}
/>

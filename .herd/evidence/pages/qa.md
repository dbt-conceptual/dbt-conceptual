# QA Effectiveness

> "The critic's eye sharpens the artist's hand." — Track review quality, finding patterns, and QA trends.

## QA Overview

**Question**: How effective is our QA process at catching issues early?

```sql qa_overview
SELECT
    COUNT(DISTINCT frq.review_submission_tk) as total_reviews,
    SUM(CASE WHEN frq.review_round = 1 THEN 1 ELSE 0 END) as first_round_reviews,
    SUM(CASE WHEN frq.review_round = 1 AND frq.review_verdict = 'approved' THEN 1 ELSE 0 END) as first_pass_approvals,
    ROUND(100.0 * SUM(CASE WHEN frq.review_round = 1 AND frq.review_verdict = 'approved' THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN frq.review_round = 1 THEN 1 ELSE 0 END), 0), 1) as first_pass_rate,
    SUM(frq.finding_count) as total_findings,
    SUM(frq.blocking_finding_count) as blocking_findings,
    SUM(frq.advisory_finding_count) as advisory_findings,
    ROUND(AVG(frq.review_duration_minutes), 1) as avg_review_minutes
FROM herd_dm.fact_review_quality frq
```

<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
  <BigValue
    data={qa_overview}
    value="total_reviews"
    title="Total Reviews"
  />

  <BigValue
    data={qa_overview}
    value="first_pass_rate"
    title="First Pass Rate"
    fmt="pct1"
  />

  <BigValue
    data={qa_overview}
    value="total_findings"
    title="Total Findings"
  />

  <BigValue
    data={qa_overview}
    value="avg_review_minutes"
    title="Avg Review Time"
    fmt="num1"
  />
</div>

---

## First-Pass Rate Trend (Last 30 Days)

**Question**: Is code quality improving over time?

```sql first_pass_trend
SELECT
    dd.date_actual as date,
    COUNT(DISTINCT frq.review_submission_tk) as reviews,
    SUM(CASE WHEN frq.review_round = 1 AND frq.review_verdict = 'approved' THEN 1 ELSE 0 END) as approvals,
    ROUND(100.0 * SUM(CASE WHEN frq.review_round = 1 AND frq.review_verdict = 'approved' THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT frq.review_submission_tk), 0), 1) as first_pass_rate
FROM herd_dm.dim_date dd
LEFT JOIN herd_dm.fact_review_quality frq
    ON CAST(strftime(frq.review_completed_at, '%Y%m%d') AS INTEGER) = dd.date_sk
    AND frq.review_round = 1
WHERE dd.date_actual >= CURRENT_DATE - INTERVAL '30 days'
  AND dd.date_actual <= CURRENT_DATE
GROUP BY dd.date_actual
ORDER BY dd.date_actual
```

<LineChart
  data={first_pass_trend}
  x="date"
  y="first_pass_rate"
  y2="reviews"
  yAxisTitle="First-Pass Rate (%)"
  y2AxisTitle="Review Count"
  title="First-Pass QA Rate Trend"
  series={[
    { name: 'First-Pass Rate', color: '#10B981' },
    { name: 'Reviews', color: '#3B82F6' }
  ]}
/>

---

## Findings by Category

**Question**: What types of issues are most common in reviews?

```sql findings_by_category
SELECT
    CASE
        WHEN frq.blocking_finding_count > 0 THEN 'Blocking'
        WHEN frq.advisory_finding_count > 0 THEN 'Advisory'
        ELSE 'Clean'
    END as finding_category,
    COUNT(DISTINCT frq.review_submission_tk) as review_count,
    SUM(frq.finding_count) as total_findings
FROM herd_dm.fact_review_quality frq
GROUP BY finding_category
ORDER BY review_count DESC
```

<BarChart
  data={findings_by_category}
  x="finding_category"
  y="review_count"
  title="Reviews by Finding Category"
  xAxisTitle="Category"
  yAxisTitle="Review Count"
  series={[
    { name: 'Reviews', color: '#3B82F6' }
  ]}
/>

<DataTable data={findings_by_category}>
  <Column id="finding_category" title="Category" />
  <Column id="review_count" title="Reviews" fmt="num0" />
  <Column id="total_findings" title="Findings" fmt="num0" />
</DataTable>

---

## Findings by Agent (Reviewed Work)

**Question**: Which agents generate the most QA findings?

```sql findings_by_agent
SELECT
    da.agent_code,
    da.agent_role,
    COUNT(DISTINCT frq.review_submission_tk) as reviews,
    SUM(frq.finding_count) as total_findings,
    SUM(frq.blocking_finding_count) as blocking_findings,
    SUM(frq.advisory_finding_count) as advisory_findings,
    ROUND(AVG(frq.finding_count), 1) as avg_findings_per_review
FROM herd_dm.fact_review_quality frq
JOIN herd_dm.dim_agent da
    ON frq.agent_sk = da.agent_sk
WHERE da.is_current = true
  AND NOT da.is_deleted
GROUP BY da.agent_code, da.agent_role
ORDER BY total_findings DESC
```

<BarChart
  data={findings_by_agent}
  x="agent_code"
  y="blocking_findings"
  y2="advisory_findings"
  title="Findings by Agent"
  xAxisTitle="Agent"
  yAxisTitle="Finding Count"
  series={[
    { name: 'Blocking', color: '#EF4444' },
    { name: 'Advisory', color: '#F59E0B' }
  ]}
/>

<DataTable data={findings_by_agent}>
  <Column id="agent_code" title="Agent" />
  <Column id="agent_role" title="Role" />
  <Column id="reviews" title="Reviews" fmt="num0" />
  <Column id="total_findings" title="Total" fmt="num0" />
  <Column id="blocking_findings" title="Blocking" fmt="num0" />
  <Column id="advisory_findings" title="Advisory" fmt="num0" />
  <Column id="avg_findings_per_review" title="Avg/Review" fmt="num1" />
</DataTable>

---

## Review Rounds Distribution

**Question**: How many review rounds does typical work require?

```sql review_rounds
SELECT
    frq.review_round,
    COUNT(DISTINCT frq.review_submission_tk) as review_count,
    SUM(CASE WHEN frq.review_verdict = 'approved' THEN 1 ELSE 0 END) as approved_count,
    ROUND(100.0 * SUM(CASE WHEN frq.review_verdict = 'approved' THEN 1 ELSE 0 END) / COUNT(DISTINCT frq.review_submission_tk), 1) as approval_rate
FROM herd_dm.fact_review_quality frq
GROUP BY frq.review_round
ORDER BY frq.review_round
```

<Histogram
  data={review_rounds}
  x="review_round"
  y="review_count"
  title="Reviews by Round"
  xAxisTitle="Review Round"
  yAxisTitle="Count"
/>

<DataTable data={review_rounds}>
  <Column id="review_round" title="Round" fmt="num0" />
  <Column id="review_count" title="Reviews" fmt="num0" />
  <Column id="approved_count" title="Approved" fmt="num0" />
  <Column id="approval_rate" title="Approval %" fmt="num1" />
</DataTable>

---

## Rework Cost Analysis

**Question**: What is the cost of rework due to failed QA?

```sql rework_cost
SELECT
    dt.ticket_code,
    dt.ticket_title,
    COUNT(DISTINCT frq.review_submission_tk) as review_attempts,
    MAX(frq.review_round) as max_rounds,
    SUM(faic.total_token_cost_usd) as total_cost,
    SUM(CASE WHEN frq.review_round > 1 THEN faic.total_token_cost_usd ELSE 0 END) as rework_cost,
    ROUND(100.0 * SUM(CASE WHEN frq.review_round > 1 THEN faic.total_token_cost_usd ELSE 0 END) / NULLIF(SUM(faic.total_token_cost_usd), 0), 1) as rework_cost_pct
FROM herd_dm.dim_ticket dt
JOIN herd_dm.fact_agent_instance_cost faic
    ON dt.ticket_sk = faic.ticket_sk
LEFT JOIN herd_dm.fact_pr_delivery fpd
    ON dt.ticket_sk = fpd.ticket_sk
LEFT JOIN herd_dm.fact_review_quality frq
    ON fpd.pull_request_sk = frq.pull_request_sk
WHERE dt.is_current = true
  AND NOT dt.is_deleted
  AND faic.total_token_cost_usd > 0
GROUP BY dt.ticket_code, dt.ticket_title
HAVING COUNT(DISTINCT frq.review_submission_tk) > 1
ORDER BY rework_cost DESC
LIMIT 20
```

<DataTable data={rework_cost} search=true>
  <Column id="ticket_code" title="Ticket" />
  <Column id="ticket_title" title="Title" />
  <Column id="review_attempts" title="Attempts" fmt="num0" />
  <Column id="max_rounds" title="Rounds" fmt="num0" />
  <Column id="total_cost" title="Total Cost" fmt="usd2" />
  <Column id="rework_cost" title="Rework Cost" fmt="usd2" />
  <Column id="rework_cost_pct" title="Rework %" fmt="num1" />
</DataTable>

---

## Review Duration Distribution

**Question**: How long do reviews typically take?

```sql review_duration
SELECT
    frq.review_duration_minutes as duration,
    COUNT(*) as count
FROM herd_dm.fact_review_quality frq
WHERE frq.review_duration_minutes IS NOT NULL
```

<Histogram
  data={review_duration}
  x="duration"
  y="count"
  title="Review Duration Distribution"
  xAxisTitle="Duration (minutes)"
  yAxisTitle="Count"
/>

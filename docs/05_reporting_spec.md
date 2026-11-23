# Workstream E · Stage 1 reporting specification

Evidence baseline: Specification Freeze v1.0 and independently reviewed C-1.0.1. The project demonstrates an end-to-end BI solution for a hypothetical digital bank. The decision remains with marketing leadership.

## Strategic Acquisition Performance

Open the [static strategic wireframe](../exhibits/dashboards/strategic_acquisition.html). The Head of Growth uses it for quarterly allocation discussions and monthly historical review.

| Page area | Recommended layout and calculation | Reporting source |
|---|---|---|
| Context and cards | Month, channel, age, spend method and model controls. Cards show distinct canonical signups, eligible paid spend and paid attribution coverage = matched ÷ all canonical signups. Display mature count and cutoff beside the selected age. | channel_cohort.parquet, one row per channel × signup month × age × allocation × model × run. Fix age, method and model before summing. |
| Channel table | Show spend and registrations beside each ratio. CAC = eligible spend ÷ aligned registrations. 90-day revenue ROAS = signed 90-day revenue ÷ eligible spend. Predicted first-year LTV/CAC = summed fixed 365-day forecasts ÷ eligible spend. Realized contribution per acquisition dollar = same-age cumulative contribution ÷ eligible spend. Use output ratio fields and preserve denominator states. | registrations, eligible_spend_cents, cac_usd, revenue_roas, predicted_ltv_cac, realized_per_spend and paid_metric_status. |
| Cohort trend | Grouped points or bars. X = signup month. Y = USD contribution per mature customer. Compare expected_comparable_cents and contribution_cents divided by the same mature_customers count. Small multiples by channel or one selected channel. Add eligible n and show pending periods with no realized result. | channel_cohort.parquet. The wireframe presents the validated March and September 2025 extracts at 90 days. |
| Product economics | Diverging contribution bars by product with a revenue/cost companion table. The approved evidence panel shows the full visible ledger. Label its population and window separately. A cohort-filtered product drilldown is a proposed extension using customer and ledger data at equivalent ages. | D independent reconciliation JSON for the visible ledger. Drilldown path financial_event → product_account and acquisition → attribution → customer_age window. Never use mortgage origination principal as earnings. |

Keep unknown attribution in coverage and customer results. Display N/A for its paid ratios and for spend-only CAC/ROAS. Never treat an immature realized result as zero. Apply month eligibility before comparing channel trends. Allow a proposed drilldown from channel/month to campaign spend, customer age, and event lineage. Show a fixed comparison snapshot with monthly cohorts and daily upstream refresh. The forecast and realized contribution represent model assumptions and simulated outcomes, respectively.

**Decision example.** Calendar allocation gives Google the highest March 2025 90-day revenue ROAS at 2.29× and Meta the highest September value at 3.22×. Use counts and coverage in the wireframe and examine product mix before considering a capped budget experiment. Mortgage net contribution is $888,044.36, about 95.9% of full visible net contribution. Avoid treating that share as a breakdown of either selected cohort.

## Operational Campaign Monitoring

Open the [static operational wireframe](../exhibits/dashboards/operational_campaigns.html). The Performance Marketing Manager monitors spend daily and reviews efficiency weekly. Investigate data quality before reacting to budget or activation signals.

| Page area | Recommended layout and calculation | Reporting source |
|---|---|---|
| Context and cards | Date, channel, campaign controls. Cards show actual and planned spend, daily attributed registrations, same-day CAC, cumulative pacing and observed activation. Month-to-date pacing = cumulative actual ÷ complete positive cumulative plan. Missing or incomplete plans result in unavailable pacing. | campaign_performance_day.parquet, one row per campaign × UTC day × run. Use actual_cents, planned_cents, actual_to_date_cents, plan_to_date_cents, pacing_status, pace_ratio. |
| Spend trend | Grouped bars by UTC day for actual and planned USD. Leave a gap for missing daily plans. A second chart may show cumulative actual and plan with the plan series breaking at the first incomplete day. Never label an unavailable ratio as 0%. | Same campaign-day mart. The F1 June 1–7 case shows a zero-signup spend day and a missing plan. |
| Campaign comparison | Campaign rows with spend, registrations, eligible-spend CAC, activated and mature counts, baseline expected 365-day contribution total and mean per signup where available. Mature activation = activated_30_customers ÷ mature_30_customers. Report pending counts = registrations − mature_30_customers. Same-day CAC is a monitoring proxy affected by conversion lag. | registrations, eligible_spend_cents, cac_usd, activated_30_customers, mature_30_customers, baseline_forecast_total_cents. Weekly preview sums matching daily spend/counts before division. Avoid averaging ratios or presenting totals when a required observation is missing. |
| Data availability | Detail panel for run cutoff, missing plan/spend, pending maturity, overall attribution coverage and exception drilldown. Coverage uses all canonical acquisitions for the selected compatible period. Campaign-only rows cannot supply its denominator. | pipeline_manifest.json, attribution and acquisition marts, exception_log.parquet and campaign-day data_status. Do not suggest that feed freshness was independently observed in a live environment. |

On June 4, F1 spent $97.77 for three signups and had $400.94 in actual spend to date. The daily plan and cumulative pacing were unavailable. No June 4 F1 signups had a mature activation window. Confirm the approved plan with the campaign owner and review data completeness before altering daily limits. Prototype alerts from A use pacing above 110% of a complete positive plan. Weekly investigation defaults use at least 20 registrations with CAC above target by 20% or mature activation below target by 10 percentage points. Show thresholds as illustrative pending business ownership and target approval. Keep spending adjustments within approved budgets. Activation depends on qualifying events and validated operational refund links. C-1.0.1 passed the correction regressions.

## Shared assumptions and claims

- Prototype attribution uses synthetic identities and touches with a 30-day last-tracked-touch rule. Production would ingest attribution outputs from a Mobile Measurement Partner (MMP) API and join them to internal identifiers and financial activity. Availability, vendor windows, identity matching, freshness and coverage require onboarding. No live connector was demonstrated.
- Production campaign budgets and targets are externally supplied approved inputs. Campaign ownership, revisions and escalation thresholds require more business context.
- Financial contribution excludes acquisition spend and uses confirmed principal charge-offs and recoveries. Expected-loss provisioning and explicit deposit/funding reversals remain outside the verified scope.
- DuckDB demonstrates daily batch ELT, reproducible outputs and two timestamp clocks. The proposed warehouse and SQL/dbt design needs separate evaluation for production freshness, volume, access, cost and reliability.
- Forecast values use frozen synthetic assumptions. Channel rankings and model sensitivities illustrate system behavior. They cannot support claims about real-channel effectiveness or empirical forecast accuracy.

## Presentation placement and Stage 2 decisions

The approved [10-slide blueprint](../presentation/README.md) reserves slide 03 for the physical schema and slide 04 for ELT. Use the strategic historical extract on slide 06. Slide 07 uses both dashboard blueprints with the operational F1 June 1–7 example visually dominant. Keep the full-history mortgage concentration callout in the appendix by default, separate from the mature 90-day cohort results. The [evidence inventory](../presentation/evidence_inventory.md) supplies exact sources. Confirm main-deck crops, illustrative threshold wording, member names and contributions, AI-use disclosure and accessibility extracts before drafting final copy.

## Dashboard visualization enhancement

The offline strategic dashboard now opens with cohort filters, coverage cards and the Customer Cohort Evolution chart. The chart uses actual age spacing and the same mature population for fixed forecast and realized USD per acquired customer. Its companion channel chart displays a single selected metric and unit. A maturity/coverage table replaces a separate product chart in the main view. The whole-ledger financial product breakdown stays in Appendix C.

The operational dashboard opens with campaign and date filters, then daily and cumulative actual/plan plots. Separate aligned charts report registrations and CAC. The activation chart distinguishes activated mature, mature not activated and pending signups using corrected C-1.0.1 counts. Missing plans, zero registration days and incomplete activation windows remain visible without imputing targets or outcomes. The fixed operational slide extract remains F1 June 1–7, 2026.

See the [chart-to-source mapping](../exhibits/presentation/dashboard_chart_sources.md) for fields, aggregation, maturity, static assets and independent reconciliation checks. The HTML is an offline snapshot with filters. PowerPoint uses the fixed, portable SVG or PNG extracts.

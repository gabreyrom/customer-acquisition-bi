# Workstream E · Reporting specification

Evidence baseline: Specification Freeze v1.0 and independently reviewed C-1.0.1. The project demonstrates an end-to-end BI solution for a hypothetical digital bank. The decision remains with marketing leadership.

Both dashboards are published at [gabrielreynosoromero.com/customer-acquisition-bi](https://gabrielreynosoromero.com/customer-acquisition-bi/) and also open offline from `site/`. Their data files are generated from the analytical marts by `src/build_dashboards.py` (see [Dashboard build and extracts](#dashboard-build-and-extracts)).

## Strategic Acquisition Performance

Open the [strategic dashboard](../site/strategic_acquisition.html). The Head of Growth uses it for quarterly allocation discussions and monthly historical review. Every view reads `channel_cohort.parquet` for the manifest run with CALENDAR spend allocation.

| Page area | Implemented layout and calculation | Reporting source |
|---|---|---|
| Filters | Start cohort; how many later cohorts to compare (next 3, 6, 9 or 12 months); acquisition channel (all signups, all paid channels, or one channel including unknown); maximum customer age (30/90/180/365 days); expected-value assumptions (baseline or equal-channel sensitivity). Defaults: January 2025, next 6 months, all signups, 365 days, baseline. | channel_cohort.parquet, one row per channel × signup month × age × allocation × model × run. Fix age, method and model before summing. |
| Payback (top of page) | X = cohort. Stacked bars = eligible spend per paid channel in scope (spend month = signup month under CALENDAR allocation). Line = total contribution (default) or revenue of the cohort's customers by the selected age (30/90/180/365, default 365). Payback multiple = value ÷ spend, shown above each cohort, green at 1.0× or more. A cohort is pending until every populated row in scope is mature at that age. The table shows, for each channel in scope and the total, spend, customers and the multiple at each age, each computed over the cohorts that have reached that age, plus the first age at which the multiple reaches 1.0×. Unknown attribution has no spend; its customers' value counts toward the all-signups total. Respects the channel filter. | eligible_spend_cents, contribution_cents, revenue_cents, registrations, mature_customers, cohort_status. |
| Cohort summary | Cohorts and customers in range. Start cohort realized ÷ expected at its latest complete age. Paid attribution coverage = paid-attributed ÷ all canonical signups, across all channels. Average realized contribution per customer at each age = Σ contribution_cents ÷ Σ registrations over the cohorts complete at that age, with the number of complete cohorts shown. | registrations, mature_customers, paid_attributed_customers, contribution_cents, expected_comparable_cents. |
| Cumulative contribution per customer | One line per cohort across 30/90/180/365 days at true age spacing. The start cohort is highlighted with its fixed expected path (expected_comparable_cents ÷ registrations). A cohort point appears only when every populated row in scope is MATURE and mature_customers = registrations, so expected and realized always share the same customers. Hovering isolates one cohort. | Same rows, filtered by channel scope and model. |
| Contribution per customer by channel | X = cohort, one line per channel including unknown, plus a dashed all-signups line. Y = contribution_cents ÷ registrations at a selectable age. A cohort that has not reached that age leaves a gap. Not affected by the channel filter. | Same rows. |
| Cohort table | Rows = cohorts, columns = ages. Realized contribution per customer with the signup-time expectation underneath, shaded by value (negative values in red). Pending cells show how many customers have reached the age. | Same rows. |
| Signups by acquisition channel | Stacked registrations per cohort for the three paid channels and unknown, to show channel-mix shifts between cohorts. | registrations at age 30. |
| Channel efficiency by cohort | One line per paid channel. Metric selector: CAC = eligible spend ÷ registrations; 90-day revenue ROAS = signed 90-day revenue ÷ eligible spend (always 90 days); realized contribution per $1 of spend = same-age cumulative contribution ÷ eligible spend at the selected age. Unknown attribution has no spend and is excluded. | cac_usd, revenue_roas, realized_per_spend. |

Keep unknown attribution in coverage and customer results. Display unavailable values for its paid ratios and for spend-only CAC/ROAS. Never treat an immature realized result as zero. The forecast and realized contribution represent model assumptions and simulated outcomes, respectively. Predicted first-year LTV/CAC (`predicted_ltv_cac`) and a product-level cohort drilldown remain available in the mart and appendix but are not dashboard views.

**Payback example.** For January–July 2025 across all signups, contribution passes spend between 90 and 180 days: 0.88× at 90 days and 1.94× at 180 days. Google Ads, Meta Ads and paid affiliates all pay back by 180 days, while the January cohort returns 4.5× its spend by 365 days. Mortgage activity drives much of that value (see below), so read payback alongside the product appendix.

**Decision example.** Calendar allocation gives Google the highest March 2025 90-day revenue ROAS at 2.29× and Meta the highest September value at 3.22× (channel efficiency view, start cohort March 2025). Read the channel-mix and cohort table before considering a capped budget experiment. Mortgage net contribution is $888,044.36, about 95.9% of full visible net contribution. Avoid treating that share as a breakdown of any selected cohort.

## Operational Campaign Monitoring

Open the [operational dashboard](../site/operational_campaigns.html). The Performance Marketing Manager monitors spend daily and reviews efficiency weekly. Investigate data quality before reacting to budget or activation signals. The dashboard opens on all channels for May 1–7, 2026: the latest full week in which every campaign has a plan for every day and every signup has passed its 30-day activation window.

| Page area | Implemented layout and calculation | Reporting source |
|---|---|---|
| Filters | Channel, then one campaign within it or all of its campaigns; start date; period of 7, 14 or 28 days. The end date is derived, and a window that runs past the last available day is shortened with a note. | campaign_performance_day.parquet, one row per campaign × UTC day × run. |
| Combining campaigns | Selected campaigns are summed by day. A day's plan or plan-to-date is unavailable if any selected campaign lacks it, so one campaign's gap is never hidden by the others. CAC = Σ eligible spend ÷ Σ registrations; ratios are never averaged. | actual_cents, eligible_spend_cents, planned_cents, actual_to_date_cents, plan_to_date_cents, registrations. |
| Period summary | Actual spend with % of plan when every day has a plan; signups; CAC; 30-day activation = activated ÷ mature with the count still under 30 days; expected first-year contribution in total, per signup and per $1 of eligible spend. Each tile is compared with the prior period of the same length. | mature_30_customers, activated_30_customers, baseline_forecast_total_cents. |
| Data checks | Missing plan days listed by campaign, days with spend but no signups, signups still under 30 days old, and shortened windows. | Same mart; data_status. |
| Channels and campaigns | Channel subtotal rows with their campaign rows and an all-channel total, for the same period and metrics. Clicking a row selects it. | Same mart. |
| Daily charts | Spend vs plan (grouped bars; days without a plan shaded). Month-to-date actual vs plan (resets on the 1st; plan line stops at the first incomplete day). Signups (zero-signup spend days shaded). Daily CAC (gaps without signups). Activation stacked as activated, not activated and under 30 days old. | Same mart. Same-day CAC is a monitoring proxy affected by conversion lag. |
| Daily detail | Weekday-dated rows, flagged missing plans and zero-signup spend days, and a totals row. | Same mart. |

**Investigation example.** Select Paid affiliates → F1 from June 1, 2026. On June 4, F1 spent $97.77 for three signups and had $400.94 in actual spend to date. The daily plan and cumulative pacing were unavailable, and the data checks name the gap. No June 4 F1 signups had a mature activation window. Confirm the approved plan with the campaign owner and review data completeness before altering daily limits. Prototype alerts from A use pacing above 110% of a complete positive plan. Weekly investigation defaults use at least 20 registrations with CAC above target by 20% or mature activation below target by 10 percentage points. Show thresholds as illustrative pending business ownership and target approval. Keep spending adjustments within approved budgets. Activation depends on qualifying events and validated operational refund links. C-1.0.1 passed the correction regressions.

## Shared assumptions and claims

- Prototype attribution uses synthetic identities and touches with a 30-day last-tracked-touch rule. Production would ingest attribution outputs from a Mobile Measurement Partner (MMP) API and join them to internal identifiers and financial activity. Availability, vendor windows, identity matching, freshness and coverage require onboarding. No live connector was demonstrated.
- Production campaign budgets and targets are externally supplied approved inputs. Campaign ownership, revisions and escalation thresholds require more business context.
- Financial contribution excludes acquisition spend and uses confirmed principal charge-offs and recoveries. Expected-loss provisioning and explicit deposit/funding reversals remain outside the verified scope.
- DuckDB demonstrates daily batch ELT, reproducible outputs and two timestamp clocks. The proposed warehouse and SQL/dbt design needs separate evaluation for production freshness, volume, access, cost and reliability.
- Forecast values use frozen synthetic assumptions. Channel rankings and model sensitivities illustrate system behavior. They cannot support claims about real-channel effectiveness or empirical forecast accuracy.

## Presentation placement and Stage 2 decisions

The approved [10-slide blueprint](../presentation/README.md) reserves slide 03 for the physical schema and slide 04 for ELT. Use the strategic historical extract on slide 06. Slide 07 uses both dashboards with the operational F1 June 1–7 investigation example visually dominant. Keep the full-history mortgage concentration callout in the appendix by default, separate from the mature cohort results. The [evidence inventory](../presentation/evidence_inventory.md) supplies exact sources. Confirm main-deck crops, illustrative threshold wording, member names and contributions, AI-use disclosure and accessibility extracts before drafting final copy.

## Dashboard build and extracts

`src/build_dashboards.py` reads `channel_cohort.parquet` and `campaign_performance_day.parquet` for the run in `pipeline_manifest.json`, checks basic invariants (mature ≤ registrations, activated ≤ mature, one shared campaign calendar) and writes `site/data/strategic.js` and `site/data/operational.js` with the snapshot cutoff. The pages share `site/assets/charts.js`; page logic lives in `site/assets/strategic.js` and `site/assets/operational.js`. The site needs no server: it runs from disk and on GitHub Pages, where `.github/workflows/static.yml` publishes `site/` on every push to `main`.

`src/export_presentation_extracts.py` renders the slide SVG and PNG files in `exhibits/presentation/` with the dashboards' own chart code and fixed filters. See the [chart-to-source mapping](../exhibits/presentation/dashboard_chart_sources.md) for each extract's fields, filters and checks.

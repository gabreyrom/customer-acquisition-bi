# Dashboard visualizations · C-1.0.1

All charts use FULL_PRIMARY_V1. Effective cutoff is July 1, 2026, 00:00 UTC exclusive. Recorded cutoff is the same instant inclusive. The [strategic](../../site/strategic_acquisition.html) and [operational](../../site/operational_campaigns.html) dashboards read data files that `src/build_dashboards.py` generates from the marts below. The SVG and PNG files here are fixed PowerPoint extracts rendered by `src/export_presentation_extracts.py` with the dashboards' own chart code. Hover points in the dashboards for exact values, and use their tables for all available counts. Synthetic outputs demonstrate reporting logic.

## Strategic extracts

Filters for every strategic extract: start cohort January 2025 plus the next 6 cohorts (January–July 2025), all signups, ages through 365 days, baseline model, CALENDAR allocation.

| Chart and static asset base name | Source and fields | Definition and limits |
|---|---|---|
| Payback · `cohort_payback` | `channel_cohort.parquet` · eligible_spend_cents, contribution_cents, registrations, mature_customers, cohort_status | Bars = spend per paid channel per cohort; line = total contribution by 365 days; label = contribution ÷ spend. July 2025 is pending at 365 days. January 2025 returns 4.5× ($85,187.60 contribution on $18,729.99 spend). The dashboard can switch to revenue (January 9.9×) or another age. |
| Cumulative contribution per customer · `customer_cohort_evolution` | `channel_cohort.parquet` · signup_month, channel, age_days, model_version, cohort_status, registrations, mature_customers, contribution_cents, expected_comparable_cents | One line per cohort at 30/90/180/365 days. January 2025 highlighted with its fixed expected path. Values = summed cents ÷ 100 ÷ registrations, shown only when every row in scope is mature, so expected and realized use the same customers. July 2025 stops at 180 days because its 365-day checkpoint is pending. In this extract January realized is $317.86 per customer at 365 days against $55.98 expected. |
| Contribution per customer by channel · `channel_contribution_by_cohort` | Same mart · contribution_cents, registrations by channel | At 90 days: one line per channel including unknown, plus the all-signups average (dashed). Unknown cohorts have about 25–35 customers, so that line is the most volatile. |
| Signups by acquisition channel · `cohort_channel_mix` | Same mart · registrations at age 30 | Stacked counts per cohort for Google Ads, Meta Ads, paid affiliates and unknown. Explains channel-mix differences between cohorts. |
| Channel efficiency by cohort · `channel_efficiency_comparison` | Same mart · revenue_roas, cac_usd, realized_per_spend, eligible_spend_cents | 90-day revenue ROAS for the three paid channels across the cohorts. Unknown attribution has no spend and is excluded. The dashboard can switch to CAC or realized contribution per $1 of spend. |

The cohort summary tiles, cohort table (ages × cohorts) and paid-coverage figure are HTML-only; copy their values into native PowerPoint tables when needed.

## Operational extracts

Filters for every operational extract: Paid affiliates → campaign F1, June 1–7, 2026. This is the investigation example; the live dashboard opens on all channels for May 1–7, 2026, where all plans are present and all signups are past 30 days.

| Chart and static asset base name | Source and fields | Definition and limits |
|---|---|---|
| Daily spend vs plan · `campaign_daily_spend` | `campaign_performance_day.parquet` · campaign_id, report_date, actual_cents, planned_cents | Grouped bars, USD = cents ÷ 100. June 4 has no plan and is shaded. |
| Month-to-date spend vs plan · `campaign_cumulative_spend` | Same mart · actual_to_date_cents, plan_to_date_cents | Month-to-date totals reset on the 1st of each month, not at the filter start. The plan line stops at June 4; June 4–7 are shaded as plan incomplete. |
| Daily signups · `campaign_registrations` | Same mart · registrations | Attributed same-day signups. June 2 and June 7 had spend but zero signups and are shaded. |
| Daily cost per signup · `campaign_cac` | Same mart · cac_usd, eligible_spend_cents, registrations | Stored USD per same-day signup; no averaging of daily ratios. Zero-signup days are gaps. Same-day CAC is a monitoring proxy. |
| Activation within 30 days · `campaign_activation_maturity` | Same mart · registrations, mature_30_customers, activated_30_customers | Stacked activated, not activated (mature − activated) and under 30 days old (registrations − mature). All 11 signups in this week are still under 30 days old. |

June 4 F1 actual = $97.77, actual month to date = $400.94, registrations = 3 and mature = 0. A complete positive plan is required for pacing. Plans remain externally assumed inputs. No missing plan or forecast point was filled.

## Validation and design decisions

- `src/build_dashboards.py` output was compared row by row with the data previously embedded in the dashboards: all 576 cohort rows and 3,276 campaign-day rows matched. The script also asserts mature ≤ registrations, activated ≤ mature and one shared campaign calendar before writing.
- Payback was checked against an independent DuckDB query on `channel_cohort.parquet`: January 2025 at 365 days 4.548× contribution and 9.859× revenue per dollar of spend; Google Ads January–July 2025 at 90 days 0.919× on $43,185.63 spend. The dashboard shows the same values.
- Verified all 26 released analytical output hashes. Independently rejoined `customer_age`, `acquisition`, `attribution` and `prediction_age`. All 576 populated calendar mart rows matched signup and mature counts. Every fully mature comparison matched both signed contribution totals and fixed forecast totals.
- Checked campaign inequalities, zero-registration CAC nulls and missing-plan pacing nulls across the full mart. The dashboards were exercised in headless Chrome across edge cases (last cohort, shortened windows, single campaign versus whole channel), and a combined channel total was checked against the sum of its campaigns.
- No cohort-filtered product financial breakdown was added. Appendix C retains the labeled whole-ledger product extract. The campaign mart supports the three disjoint activation categories shown, but it does not separate causes of mature non-activation. Dashboard freshness is the snapshot timestamp. There is no live feed check, dashboard service, drilldown endpoint, or new forecast.

# Customer Acquisition Value Intelligence

**MIS 636 · Team 3**

An end-to-end business intelligence prototype for a hypothetical digital bank. It connects acquisition records with customer and financial activity so a growth team can see what it spent to acquire customers, what contribution it expected at signup, and what contribution those customers generated as they matured.

**Dashboard Prototype** : https://gabrielreynosoromero.com/customer-acquisition-bi/

## The business question

**How should a digital bank decide where to invest its customer acquisition budget?**

Registrations and revenue return on ad spend (ROAS) tell part of the story. Two groups can generate similar revenue and still contribute different amounts after funding, servicing, rewards, and credit losses. The timing matters, too. A customer acquired last month has had less time to generate value than one acquired a year ago.

Assignment 1 proposed a reporting architecture centered on 90-day revenue ROAS. Assignment 2 implements and tests that proposal with a broader view of customer value. The prototype retains revenue ROAS, adds contribution measures, and makes historical comparisons at the same customer age.

| Who uses it | Decision | What the system shows |
|---|---|---|
| Growth leadership | Review quarterly acquisition budgets | Acquisition cost, revenue ROAS, initial expected contribution, and same-age realized contribution by channel and signup cohort |
| Performance marketing | Monitor daily pacing and review weekly campaign activity | Actual and planned spend, signups, acquisition cost, activation maturity, and gaps in reporting inputs |
| Finance and analytics | Verify reported figures and investigate exceptions | Source records, recognized revenue and cost components, reconciliation results, and the reporting cutoffs behind each result |

## How the solution works

1. **Connect acquisition to customers.** The system links campaign spending, marketing touches, customer registrations, and product accounts. In the prototype, simulated attribution uses the last eligible tracked touch within 30 days before signup. Unresolved attribution stays visible as unknown.
2. **Measure realized customer contribution.** Financial activity becomes traceable revenue or cost entries across savings, debit cards, credit cards, personal loans, and mortgages. Contribution is recognized revenue less attributable financial and operating costs. Acquisition spend is tracked separately, and movements such as deposits and loan principal stay outside earnings.
3. **Keep a fixed view of what was expected at signup.** The prototype records a rule-based estimate of first-year contribution using the information available at acquisition. It preserves that estimate and its expected path at 30, 90, 180, and 365 days as actual activity comes in.
4. **Compare customers at the same age.** The reporting layer shows expected and realized contribution over equivalent observation windows. If a group has not had enough time to reach a checkpoint, its result remains pending. Campaign pacing is unavailable when the necessary plan data is missing.

## Dashboards

Live at **https://gabrielreynosoromero.com/customer-acquisition-bi/**, or open [`site/index.html`](site/index.html) from a downloaded copy (no server needed, JavaScript enabled). Both dashboards use the fixed synthetic snapshot as of July 1, 2026.

### [Strategic Acquisition Performance](site/strategic_acquisition.html)

For growth leadership deciding where acquisition budget creates value. Pick a **start cohort** (signup month) and compare it with the **next 3, 6, 9 or 12 cohorts**. Filter by acquisition channel, customer age and expected-value assumptions.

| View | What it shows |
|---|---|
| Payback | What each cohort cost to acquire (bars split by paid channel) against the contribution its customers returned by a chosen age (30, 90, 180 or 365 days), with the payback multiple above each cohort. A table shows the multiple at every age by channel and when each channel pays back. Switch to revenue for the gross view. |
| Cohort summary | Cohorts and customers in range, the start cohort's realized-vs-expected multiple, paid-channel coverage, and average contribution per customer at 30, 90, 180 and 365 days. |
| Cumulative contribution per customer | One line per cohort as its customers age. The start cohort is highlighted next to the contribution expected at signup. Hover over a line to isolate a cohort. |
| Contribution per customer by channel | One line per channel across the cohorts at a chosen age, plus the all-signups average. |
| Cohort table | Cohorts × ages: realized contribution per customer with the expectation underneath, shaded by value. Pending cells show how many customers have reached that age. |
| Signups by acquisition channel | Each cohort's channel mix, which helps explain why cohorts differ. |
| Channel efficiency by cohort | CAC, 90-day revenue ROAS or realized contribution per $1 of spend for each paid channel. |

### [Operational Campaign Monitoring](site/operational_campaigns.html)

For performance marketing tracking daily pacing and weekly campaign results. Choose a **channel**, then one of its **campaigns** or all of them, a **start date** and a **7-, 14- or 28-day period**. It opens on all channels for May 1–7, 2026, the latest week with complete plans and fully observed activation.

| View | What it shows |
|---|---|
| Period summary | Spend against plan, signups, cost per signup, 30-day activation and expected first-year contribution, each compared with the prior period. |
| Data checks | Missing plans (named by campaign), spend days with no signups, and signups too young to judge activation, listed before any chart. |
| Channels and campaigns | Every channel with its campaigns and an overall total for the same period. Click a row to select it. |
| Daily charts | Spend vs plan, month-to-date pacing, signups, cost per signup and activation, with problem days shaded. |
| Daily detail | One row per day with flagged gaps and a totals row. |

To see how missing inputs are handled, select Paid affiliates → F1 from June 1, 2026: June 4 has no plan, and every signup's activation is still pending.

### Rebuilding the dashboards

The dashboards read `site/data/*.js`, which are generated from the pipeline's analytical outputs:

```sh
python3 src/build_dashboards.py               # site/data/ from data/analytical_outputs
python3 src/export_presentation_extracts.py   # slide SVG/PNG charts (needs Chrome and rsvg-convert)
```

Pushing to `main` republishes `site/` through GitHub Pages.

## More to explore

| Start here | What to look for |
|---|---|
| [Worked customer example](exhibits/tables/d2_customer_trace.md) | Follow an underlying balance through revenue recognition, then reconcile one customer's 90-day contribution across five products. |
| [Presentation materials](presentation/README.md) | The ten-slide plan, speaker notes, appendix, evidence references, and PowerPoint assembly guide. |
| [PowerPoint-ready charts](exhibits/presentation/) | SVG and PNG extracts of the dashboard charts, with their [sources and filters](exhibits/presentation/dashboard_chart_sources.md). |

## What the validation established

The demonstration uses **5,000 synthetic customers** acquired from January 2025 through June 2026. The team compared the outputs with independently calculated expectations and reconciled source activity to reported results. **329 controlled comparisons matched**, **10 refund regression cases passed after correction**, and **26 analytical output files reproduced** on a clean rerun.

One test exposed a meaningful distinction between financial and operational accuracy. A refund referencing a purchase on another account incorrectly cleared a valid debit activation, even though the financial ledger still reconciled. The corrected build validates the purchase reference and refund eligibility before it changes activation. The [validation report](docs/04_validation_report.md) and [architecture decisions](docs/06_architecture_decisions.md) explain the evidence and remaining limits.

## Scope and limitations

This is a working BI prototype using synthetic acquisition and financial records. Its results demonstrate traceability, comparable historical measurement, and tested calculation behavior. They do not establish real-world channel effectiveness or predictive accuracy.

A production implementation would need live product-system feeds, acquisition attribution from a Mobile Measurement Partner (MMP), and approved campaign plans from the business. The prototype uses a simplified confirmed-charge-off and recovery convention. Deposit and funding reversal scenarios, live integrations, operational controls, and production scalability still require separate evaluation.

## Repository guide

| Folder | What it contains |
|---|---|
| [docs](docs/) | Business and measurement specifications, reporting definitions, validation report, and architecture decisions |
| [data](data/) | Synthetic input extracts, controlled validation cases, and analytical outputs |
| [site](site/) | The published dashboards: pages, shared chart code and generated data files |
| [exhibits](exhibits/) | Slide chart extracts, technical diagrams, and validation evidence |
| [presentation](presentation/) | Slide-ready copy, speaker cues, appendix material, and submission checklist |
| [src](src/) and [tests](tests/) | Reproducible pipeline, dashboard build, and regression checks |

For technical review or reproduction, start with the [frozen specification](docs/07_specification_freeze_v1.0.md) and the [pipeline guide](docs/03_pipeline_design.md).

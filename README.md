# Customer Acquisition Value Intelligence

**MIS 636 · Team 3**

An end-to-end business intelligence prototype for a hypothetical digital bank. It connects acquisition records with customer and financial activity so a growth team can see what it spent to acquire customers, what contribution it expected at signup, and what contribution those customers generated as they matured.

**Prototype** : http://gabrielreynosoromero.com/customer-acquisition-bi/

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

## What you can explore

| Start here | What to look for |
|---|---|
| [Strategic Acquisition Performance dashboard](exhibits/dashboards/strategic_acquisition.html) | Compare customer contribution trajectories across signup cohorts. Change the channel, maturity checkpoint, or forecast scenario. The companion efficiency chart lets you switch between metrics with different units. |
| [Operational Campaign Monitoring dashboard](exhibits/dashboards/operational_campaigns.html) | Follow daily and cumulative actual versus planned spend, registrations, acquisition cost, and activation. The F1 example shows how a missing plan and an incomplete activation window appear. |
| [Worked customer example](exhibits/tables/d2_customer_trace.md) | Follow an underlying balance through revenue recognition, then reconcile one customer's 90-day contribution across five products. |
| [Presentation materials](presentation/README.md) | Find the ten-slide plan, speaker notes, appendix, evidence references, and PowerPoint assembly guide. |

To use the dashboards, download the repository and open the HTML files in a browser with JavaScript enabled. The dashboard filters run locally against a fixed synthetic snapshot. [PowerPoint-ready charts and extracts](exhibits/presentation/) are also available.

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
| [exhibits](exhibits/) | Dashboard blueprints, charts, technical diagrams, and validation evidence |
| [presentation](presentation/) | Slide-ready copy, speaker cues, appendix material, and submission checklist |
| [src](src/) and [tests](tests/) | Reproducible pipeline and regression checks |

For technical review or reproduction, start with the [frozen specification](docs/07_specification_freeze_v1.0.md) and the [pipeline guide](docs/03_pipeline_design.md).

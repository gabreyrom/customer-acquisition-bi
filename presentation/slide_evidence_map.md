# Slide-to-source evidence index

Project paths refer to the accompanying ZIP. **P** is FULL_PRIMARY_V1, with effective time before July 1, 2026, 00:00 UTC and recorded time at or before that instant. **R** keeps P effective cutoff and advances recorded time to July 3, 2026, 00:00 UTC. **Correction pair** uses recorded cutoffs March 11 and March 13, 2025, 00:00 UTC with P effective cutoff. Values are synthetic. Customer windows are UTC, exclusive at the age endpoint.

| Slide or section | Evidence and fields | Exact source and check | Cutoff and caveat |
|---|---|---|---|
| 01 | Assignment 1 decision and revised design | `Marketing Budget Allocation for a Fintech Company.pptx` slides 2–3; `Executive Summaray MIS 636 Project.docx`; `docs/01_project_spec.md` | Proposal versus implemented prototype. Cite prior deck briefly. |
| 02 | Counts and source grain. R02703 → reg:02703 → A027030 → D00457542. R1/T02/T03 availability. | `data/synthetic_sources/manifest_v1.0.json`; `registration.jsonl.gz`, `product_account.jsonl.gz`, `product_activity_delivery.jsonl.gz` in same folder; `data/validation_cases/controlled_source.json`; `data/analytical_outputs/controlled_comparison.json` | Coverage Jan 2025–Jun 2026. Touch eligibility uses signup cutoff. Frozen cases illustrate rules. |
| 03 / A | 24 physical tables, declared keys, grain and two clocks | `src/schema.sql`; `docs/02_data_dictionary.md`; `exhibits/architecture/logical_erd.md`; `exhibits/presentation/final_exhibits.md` | Freeze v1.0 and C-1.0.1. Dashed arrows include logical steps or omitted intermediates. |
| 04 / B1 | Typed load, identity/spend, finance, forecast, reporting and checks | `src/ingest.py`, `src/calculate_ltv.py`, `src/transformations/01_identity_spend.sql`, `02_financial.sql`, `03_reporting.sql`; `docs/03_pipeline_design.md`; `docs/02_source_target_mapping.md` | P and controlled replay paths. MMP ingestion is proposed. |
| 05 / B2 | C02703 component link, signed amounts, 90-day tie-out and March unknown cohort | `data/analytical_outputs/worked_customer_trace.csv` source keys, balance, rate, class and signed cents; `worked_customer_summary.csv` age 90; `exhibits/tables/d2_customer_trace.md`; `channel_cohort.parquet`, March/UNKNOWN/90/CALENDAR/A_v0.3_BASELINE | P. C02703 exclusive endpoint June 14, 2025, 13:00 UTC. One example. |
| 06 / C1 | Fixed and realized at all ages. Google example and coverage for mature 90-day cohorts. | `data/analytical_outputs/worked_customer_summary.csv` expected_cents and contribution_cents; `channel_cohort.parquet` or `cohort_comparison.csv`: Mar and Sep 2025, MATURE/90/CALENDAR/A_v0.3_BASELINE, registrations, paid_attributed_customers, eligible_spend_cents, cac_usd, revenue_roas, realized_per_spend; model formulas in `docs/01_project_spec.md` | P. Coverage includes unknown. Ratios use paid cohorts. Forecast is assumption-based. |
| 07 | Growth and campaign views. F1 spend and plan availability, activation denominator and daily CAC. | `data/analytical_outputs/campaign_performance_day.parquet` F1 June 1–7, 2026, including June 4; actual_cents, planned_cents, registrations, mature_30_customers, pace_ratio, cac_usd; both `site/` dashboards, portable SVG/PNG assets under `exhibits/presentation/`, [chart-level sources](../exhibits/presentation/dashboard_chart_sources.md) and `docs/05_reporting_spec.md` | P. Daily CAC is a monitoring proxy. Missing and pending stay distinct. |
| 08 / D1 | Controlled outcomes, independent totals and reproducibility | `data/validation_cases/independent_expected.json`; `data/analytical_outputs/controlled_comparison.json`, `pipeline_manifest.json`; `exhibits/tables/d2_independent_reconciliation.json`; `docs/04_validation_report.md` | Full-visible P totals and controlled P/R/correction pair. No production validation. |
| 09 / D2 | Original failed probe, same-account integrity fix and observed retest | `exhibits/tables/d2_refund_integrity_probe.json`, `refund_regression_results.json`, `refund_regression_signoff.md`; `src/ingest.py`; `docs/06_architecture_decisions.md` | P cutoffs in scratch fixtures. Corrected C-1.0.1. Untested operational reversal categories remain. |
| 10 / E | Implemented results, limits and preserved baseline | `docs/07_specification_freeze_v1.0.md`, `docs/06_architecture_decisions.md`, `exhibits/architecture/d2_design_evidence.md`, `data/analytical_outputs/pipeline_manifest.json` | Local daily batch. Production and live-source assumptions are proposed. |
| C2 | Spend and forecast sensitivities and independent product concentration | `data/analytical_outputs/allocation_comparison.csv`, `scenario_comparison.csv`; `exhibits/tables/d2_sensitivity.md`, `d2_independent_reconciliation.json` | P. 15 mature 90-day months for ranking-order checks. Same frozen 365-day population for multiplier case. Full-visible ledger for product mix. |
| F | Sources, AI use and contribution ownership | Official Assignment 2 instructions; Assignment 1 and executive summary above; root `README.md` responsibility matrix as context; `presentation/final_appendix_content.md` pending disclosures | Team human review and member-specific attribution require confirmation. Embed any restricted excerpt in the deck. |

## Assessment coverage check

| Requirement | Main slides | Appendix |
|---|---|---|
| Brief Assignment 1 alignment | 01 | F |
| Q1 · Representative evidence | 02 | A, D |
| Q2 · Analytical path | 03–05 | A, B |
| Q3 · Useful outputs | 05–07 | B, C |
| Q4 · Independent validation | 08 | D |
| Q5 · Design refinement | 09–10 | D, E |

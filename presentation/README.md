# Workstream E · Revised Stage 1 presentation blueprint

Team 3 · **10 main slides · 12 minutes of presentation + 3 minutes of initial questions**  
Evidence baseline: Specification Freeze v1.0 and corrected implementation C-1.0.1.

Submit one consolidated group PowerPoint for business and technical leadership. Use the deck to communicate the demonstration, observations, and design refinement without requiring narration, external access, or code execution. Briefly reference the Assignment 1 deck and the revised executive summary on slide 01. The work below is a presentation blueprint for manual assembly.

## Main deck

| Slide · working title | Requirement and planning takeaway | Evidence and recommended layout | Supporting artifact and detail boundary | Time |
|---|---|---|---|---:|
| 01 · Business Problem and Assignment Alignment | Alignment. The project moves from proposed acquisition ROAS reporting to a working contribution and customer-value BI prototype. | Two compact panels comparing original and revised scope, then one sentence each on quarterly allocation and daily/weekly campaign review. | Assignment 1 slides 2–3, revised executive summary, and [project spec](../docs/01_project_spec.md). Cite Assignment 1 by title and slide. Keep full background out. | 0:45 |
| 02 · Representative Data and Sources | Q1. The sample exercises identity, attribution, product ownership, financial recognition and timing exceptions. | Source-grain overview plus contrasting R1/T02/T03 records. Show 5,000 canonical customers, 6,383 product accounts and 850,786 deliveries, January 2025–June 2026, three paid channels and five products. | Synthetic source manifest and controlled source JSON. Show signup and touch availability, with the record extracts and limits in A/D. | 1:00 |
| 03 · Database Design and Schemas | Q2. Physical keys and grains preserve account ownership, timestamp history and event lineage. | Simplified eight-entity diagram beside one or two typed schema excerpts. Differentiate source and derived records. | [Schema exhibit](../exhibits/architecture/e_schema_elt_exhibits.md), DDL and dictionary. Selected columns on main slide, all 24 table names and fuller keys in A. | 1:10 |
| 04 · ELT Pipeline and Transformations | Q2. Python and DuckDB SQL turn raw synthetic records into reproducible marts. | One vertical or wrapped pipeline with checkpoints for typed load, identity/attribution, standardization, fixed LTV, age histories and reporting. Include a short proposed MMP API callout. | [ELT exhibit](../exhibits/architecture/e_schema_elt_exhibits.md), pipeline design, SQL stages and run manifest. Place code and reconciliation details in B/D. | 1:20 |
| 05 · Customer Contribution Calculation | Q2/Q3. Independently trace source amounts to signed components, customer contribution and cohort. | Savings source calculation plus five-product rollup. C02703 has $321.71 at 90 days. Mark deposit, loan principal and purchase face value as excluded under approved rules. | `worked_customer_trace.csv`, `worked_customer_summary.csv`, `d2_customer_trace.md`. Show selected IDs and a compact bridge, with fuller calculations in B/D. | 1:20 |
| 06 · Customer LTV and Historical Cohort Analysis | Q3. Frozen expectations and realized values are comparable at the same age. | Two panels. Expected/realized trajectory at 30, 90, 180 and 365 days, then March vs September 2025 mature 90-day channel comparison. Include CAC, revenue ROAS, contribution per spend, coverage and counts. | Customer summary, channel cohort mart and strategic dashboard. Keep horizon eligibility and distinct forecast/realized series visible. Model details and sensitivity in C. | 1:35 |
| 07 · Strategic and Operational BI Reporting | Q3. Management can review channel performance and investigate missing campaign plan evidence. | Small strategic view and larger operational F1 June 1–7 view with a June 4 investigation cue. June 4 spent $97.77 with three signups, unavailable pacing and pending activation. | Both dashboards and campaign-day mart. Show a readable cropped extract. Place full metric and target details in C/E as relevant. | 1:15 |
| 08 · Independent Validation | Q4. Independent calculations support the tested synthetic results and reproducibility. | Scorecard separates 329/329 frozen comparisons, 10/10 refund regressions and 26/26 reproduced outputs. Compact tie-out with $2,170,710.13 revenue, $1,244,633.72 costs, $926,076.41 contribution and $330,676.79 eligible spend per method. | Validation report, comparison JSON, independent audit and regression results. State what was independently recalculated and which reversal tests remain open. Detail in D. | 1:20 |
| 09 · What Validation Changed in Our Design | Q5. Financial reconciliation and operational referential integrity require separate checks. | Before/after defect diagram. Invalid cross-account refund originally cleared valid activation. C-1.0.1 quarantines it and preserves $60.00 net purchase activity. Pair with three compact ELT, ledger and daily batch decisions. | Original failed probe, regression sign-off and architecture decision record. Full alternatives and caveats in E. Avoid unmeasured cost or scalability claims. | 1:25 |
| 10 · Conclusions and Assignment 3 | Q5. A reproducible synthetic baseline can be tested against changed source evidence and an operating requirement. | Three findings, principal limitations and the preserved baseline. Reference proposed warehouse/MMP, external plans and simplified realized loss. | Spec freeze, run manifest and architecture decision record. Preserve sources, cutoffs, code, tests and analytical outputs. | 0:50 |

## Explicit assessment coverage

| Requirement | Main slides | Specific evidence | Appendix | Project source |
|---|---|---|---|---|
| Brief Assignment 1 alignment | 01 | Original budget allocation and 90-day ROAS proposal, then revised contribution and monitoring scope | F | Assignment 1 deck slides 2–3, executive summary, `docs/01_project_spec.md` |
| Q1 · Representative evidence | 02 | Nine source tables, contrasting touch availability and source-to-account grain | A, D | `manifest_v1.0.json`, `controlled_source.json`, data dictionary |
| Q2 · Analytical path | 03–05 | Eight central entities, typed columns, Python/SQL stages, independent signed component trace | A, B | `src/schema.sql`, `docs/03_pipeline_design.md`, `worked_customer_trace.csv` |
| Q3 · Useful outputs | 05–07 | $321.71 worked customer, matched age outcomes, March/September cohort comparisons and F1 missing-plan response | B, C | `worked_customer_summary.csv`, `channel_cohort.parquet`, `campaign_performance_day.parquet` and both dashboards |
| Q4 · Validation | 08 | Controlled reference checks, independent full-source financial and spend reconciliation, regression tests and repeat run | D | `docs/04_validation_report.md`, C comparison and manifest, D audit and refund results |
| Q5 · Design refinement | 09–10 | Original operational failure and corrected reference control. Retained-source ELT, canonical ledger, daily cadence and Assignment 3 baseline | D, E | Original failed probe, corrected regression exhibit and `docs/06_architecture_decisions.md` |

## Appendix slide blueprint

These slides support questions and sit outside the 12-minute run. Use readable crops, excerpts and summaries with plain-language captions.

| Slide | Requirement and takeaway | Necessary evidence and visual layout | Artifact and detail limit |
|---|---|---|---|
| A1 · Physical table inventory | Q1/Q2. Each table serves a defined source, integration or reporting purpose. | Three groups listing all 24 names with a short grain or purpose subtitle. | [Schema and ELT exhibit](../exhibits/architecture/e_schema_elt_exhibits.md), `src/schema.sql` and dictionary. Use one readable inventory or split across two pages. |
| A2 · Relationships and types | Q2. Foreign keys address lineage and source identity links are resolved by transformation. | Detailed ERD plus selected PK/FK, types and timestamp examples. | `exhibits/architecture/logical_erd.md`, schema and dictionary. Show legible excerpts. |
| B1 · Financial rules and mappings | Q2. Recognition and exclusions are consistent across all five products. | Five-row taxonomy, signed formula, one source-to-target row, one fee-restatement row. | `docs/01_project_spec.md`, `docs/02_source_target_mapping.md` and validated E028/E029 evidence. |
| B2 · Worked trace detail | Q2/Q3. Individual source keys and signed components reconcile to the cohort. | Small readable source and ledger extract plus the five-product tie-out. | `worked_customer_trace.csv`, `d2_customer_trace.md`. Show a subset and referenced full extract. |
| C1 · Frozen forecast and maturity | Q3/Q4. Feature availability freezes the forecast and comparable age windows exclude immature outcomes. | Parameter grid or formula, small checkpoint example and a timeline with exclusive boundary. | `docs/01_project_spec.md`, forecast model mart and customer-age output. |
| C2 · Sensitivity and product mix | Q3. Spend-method changes and forecast multiplier changes affect different quantities. | Two small comparison tables and a separate mortgage contribution callout labeled full visible history. | `d2_sensitivity.md` and D independent reconciliation JSON. Keep denominators and populations separate. |
| D1 · Independent cases and actuals | Q1/Q4. Multiple cutoffs distinguish valid observations from late records. | A few expected/observed rows, four snapshot labels and revenue/cost/spend reconciliation. | `independent_expected.json`, `controlled_comparison.json`, validation report. Include controlled IDs and amounts. |
| D2 · Refund regression and reproduction | Q4/Q5. Operational link checks correct a distinct failure even when financial totals reconcile. | Original failing row, corrected row and concise regression matrix. | `d2_refund_integrity_probe.json`, `refund_regression_results.json`, `pipeline_manifest.json`. Use excerpts and repeat-run count. |
| E1 · Alternatives and boundaries | Q5. The observed evidence supports the local design and defines outstanding production conditions. | Decision table for ETL/ELT, aggregation/ledger and batch/streaming plus timestamp and forecast choices. | `docs/06_architecture_decisions.md`. Clearly mark proposed production MMP/warehouse, external budgets, expected-loss and reversal limits, and unmeasured scaling. |
| F1 · Sources and evidence access | Submission. A reviewer can identify and read the basis for every claim. | Assignment 1 short citation, official instructions, scope documents and selected exhibit references. | [Evidence inventory](evidence_inventory.md). Embed readable extracts where access would otherwise be restricted. |
| F2 · AI use and contributions | Submission. The group identifies material assistance, human checks and individual responsibilities. | Five rows with [Member name] and [verified contribution/evidence] placeholders. Add actual material AI use and how the team checked definitions, code, source generation and reporting as applicable. | Root README responsibility matrix and validation artifacts. Confirm human contributions and checks with members before submission. |

## Submission completeness checklist

Items marked ready refer to Stage 1 evidence or planning. The team still needs to assemble and review the PowerPoint.

- [ ] One consolidated group PowerPoint assembled and reviewed.
- [x] Brief Assignment 1 alignment planned for slide 01.
- [x] Explicit answers to all five questions mapped.
- [x] Representative synthetic input evidence identified.
- [x] Database schema and ELT architecture exhibits prepared.
- [x] Actual calculated results and historical comparison selected.
- [x] Strategic and operational reporting blueprints available.
- [x] Independent validation evidence available.
- [x] Evidence-based design refinement selected.
- [ ] Readable technical appendix assembled and checked against the blueprint.
- [ ] Five team member names confirmed.
- [x] Source and artifact references mapped. Verify placement in the assembled deck.
- [ ] Material AI-use disclosure and verification explanation confirmed.
- [ ] Short individual contribution statements confirmed.
- [ ] Readable restricted-access extracts embedded and checked.
- [x] Limitations and Assignment 3 implications planned.

## Supporting package and Stage 2 decisions

Keep the executable schema, dictionary, ERDs, Python and SQL, synthetic source manifest, run manifest, analytical extracts, controlled references, observations, and architecture decisions as supporting evidence. The ZIP supports reproduction. Embed readable excerpts of any private or paid material directly in the deck, and include the actual numbers and interpretation on the slide or appendix. Verify the submitted PowerPoint opens offline with its visuals intact.

For Stage 2, agree on the final crops for slide 03 and the dashboard balance on slide 07. Confirm placement of the mortgage concentration callout, keep alert thresholds illustrative unless approved, and collect member names, actual contributions and AI-use verification details. Develop final slide copy against these approved sources after review.

## Stage 2 assembly materials

Use [final slide copy](final_slide_content.md), [appendix copy](final_appendix_content.md), [evidence index](slide_evidence_map.md), and the [assembly guide](assembly_guide.md). The Stage 1 tables above retain the approved plan. Stage 2 follows the system-demonstration emphasis.

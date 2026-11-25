# Main slides · Copy and speaker notes

Team 3 · MIS 636 Assignment 2 · C-1.0.1 · 12:00 speaking time, 3:00 questions  
Copy only the **On slide** text, visual labels, and footers. The timing, layout, and notes guide assembly. Use the [visual kit](../exhibits/presentation/final_exhibits.md) and [evidence index](slide_evidence_map.md).

## 01 · From acquisition ROAS design to a working BI system
**Requirement:** Brief Assignment 1 alignment. **Time:** 0:45.  
**Takeaway:** The team turned the proposed reporting architecture into an inspectable prototype.

**On slide**

- **Assignment 1** · Proposed using 90-day revenue ROAS to inform acquisition budget allocation.
- **Assignment 2** · Implemented and independently checked a BI prototype that links acquisition spend to customer contribution and expected value.
- **Strategic decision** · Compare comparable cohorts when reviewing quarterly acquisition budgets.
- **Operational decision** · Monitor campaign pacing and investigate acquisition or activation signals.

**Layout and visual:** Two connected alignment panels across the top, then two decision boxes.  
**Footer/source:** Team 3, MIS 636. Synthetic digital bank. Assignment 1, *Marketing Budget Allocation for a Fintech Company*, slides 2–3. Revised executive summary and frozen project spec.  
**Say:** Revenue ROAS stays available. Contribution adds attributable costs while preserving acquisition spend as a separate measure.

## 02 · Representative records exercise joins and timing rules
**Question:** Q1. **Time:** 1:00.  
**Takeaway:** The inputs exercise ownership, attribution, heterogeneous product rules and exceptions.

**On slide**

- **Coverage** · Jan 2025–Jun 2026 · 5,000 canonical customers · 6,383 product accounts · 850,786 financial activity deliveries.
- **Acquisition** · Google Ads, Meta Ads and paid affiliates. Campaign spend is daily. Registrations and touches are timestamped observations.
- **Products** · Savings, debit, credit cards, personal loans and mortgages.
- **Two source examples** · Registration and account identity link a customer to a financial delivery. An eligible touch recorded after signup tests point-in-time attribution.

**Layout and visual:** Three source-grain labels above the two compact actual record extracts in the visual kit.  
**Footer/source:** Synthetic records. Source manifest, registration/account/activity extracts, and controlled R1/T02/T03. A delivery can be a duplicate, late or non-economic.  
**Say:** Walk from `reg:02703` to account `A027030` and delivery `D00457542`. Separately, T03 occurred before R1 signup but was recorded afterward, so T02 wins.

## 03 · Physical keys preserve ownership and event lineage
**Question:** Q2. **Time:** 1:10.  
**Takeaway:** The schema distinguishes source delivery, identity, contribution event and reporting grains.

**On slide**

- `acquisition` records canonical signups. `attribution` preserves the selected campaign or an unknown status.
- `financial_event` stores signed integer cents by component and run, with source and original-event links.
- Forecasts retain customer, model and age keys. Cohorts add month, channel and allocation method.

**Layout and visual:** Eight-table principal diagram with solid foreign keys and dashed processing relationships. Place two compact typed schema excerpts beside it.  
**Footer/source:** `src/schema.sql` and data dictionary. Appendix A inventories all 24 physical tables.  
**Say:** Explain why the ledger keys differ from customer and campaign keys, and point to the separate effective and recorded timestamps.

## 04 · Implemented ELT turns sources into analytical marts
**Question:** Q2. **Time:** 1:20.  
**Takeaway:** The local pipeline preserves source evidence and produces reproducible outputs.

**On slide**

- **Load** · Python verifies source hashes and loads typed DuckDB tables.
- **Transform** · SQL resolves identity and applies simulated 30-day last-touch attribution. SQL and Python standardize financial events and validate adjustments.
- **Measure and export** · Freeze acquisition-time forecasts, build customer-age and reporting marts, export results and check reconciliation.
- **Proposed production** · MMP API attribution, live product-system feeds, warehouse-based transformations and live BI.

**Layout and visual:** Use the implemented process diagram in the visual kit. Keep proposed production in a visibly separate callout.  
**Footer/source:** `src/ingest.py`, `src/calculate_ltv.py`, three SQL stages and `pipeline_manifest.json`. No live MMP connection was implemented.  
**Say:** Explain how source preservation makes defects and late observations traceable. Compare the implemented simulated attribution path with the proposed vendor feed.

## 05 · From source balance to $321.71 at customer age 90 days
**Questions:** Q2/Q3. **Time:** 1:20.  
**Takeaway:** The contribution result is independently reproducible from source components.

**On slide**

- **Source** · `core:E00457542` contains an eligible balance of 104,900 cents.
- **Standardize** · 104,900 × 0.073 ÷ 365, rounded half-up, yields **21 cents** of treasury revenue.
- **Aggregate** · 479 recognized components across five products for C02703. **$1,348.67 revenue − $1,026.96 cost = $321.71**.
- **Publish** · Include that customer’s contribution in the mature March 2025 unknown-attribution cohort. Deposits and loan principal remain outside earnings.

**Layout and visual:** Three-step trace, then a simple customer-to-cohort arrow.  
**Footer/source:** `worked_customer_trace.csv`, `worked_customer_summary.csv`, and `d2_customer_trace.md`. Window ends Jun 14, 2025, 13:00 UTC, exclusive. Synthetic calculation example.  
**Say:** The balance is an input to an accrual rule. The principal balance itself is excluded from recognized revenue.

## 06 · Frozen forecasts and realized contribution use matching ages
**Question:** Q3. **Time:** 1:35.  
**Takeaway:** Fixed predictions and maturity controls make historical comparisons consistent.

**On slide**

- **At signup** · Freeze the 365-day contribution estimate, the eligible inputs, and its 30/90/180/365-day trajectory.
- **After signup** · Accumulate realized contribution to the same exclusive ages. Keep immature results pending.
- **Compare** · Use the same age, model, spend-allocation method and eligibility rules for both signup months.
- **Efficiency measures** · CAC uses spend per signup. Revenue ROAS uses revenue per spend. Contribution efficiency uses net contribution per spend.

**Layout and visual:** Four-age chart for C02703 beside the March/September coverage and Google example in the visual kit. The broader channel table stays in the appendix.  
**Footer/source:** `worked_customer_summary.csv` and `channel_cohort.parquet`. Mature 90-day cohorts, CALENDAR and A_v0.3_BASELINE. Paid ratios exclude unknown attribution, while coverage includes it.  
**Say:** The example demonstrates a measurement capability. The difference between simulated realization and forecast does not establish model accuracy or channel effectiveness.

## 07 · Two dashboards support different decision rhythms
**Question:** Q3. **Time:** 1:15.  
**Takeaway:** The same marts serve quarterly planning and daily campaign review, while missing inputs remain visible.

**On slide**

- **Growth leadership** · Pick a start cohort and compare it with the next 3–12 cohorts at 30, 90, 180 and 365 days. Payback sets each cohort's acquisition spend against the contribution it returned: January–July 2025 passes break-even between 90 and 180 days. Read contribution per customer by channel, channel mix, CAC, ROAS and contribution per dollar spent. Pending ages stay visible. Product-level cohort drilldown is proposed.
- **Campaign manager** · Select a channel, then a campaign, and a 7-, 14- or 28-day window. Review spend against plan, signups, CAC, activation and acquisition-time forecast, each against the prior period. Data checks list missing inputs first.
- **F1, June 4** · $97.77 actual spend, 3 signups, $32.59 daily CAC. **Missing plan → pacing unavailable.** **0 mature signups → 30-day activation pending.**

**Layout and visual:** One-third strategic area with the [payback chart](../exhibits/presentation/cohort_payback.svg) or the [cumulative contribution chart](../exhibits/presentation/customer_cohort_evolution.svg) (January–July 2025 cohorts). Give the two-thirds operational area to [F1 spend versus plan](../exhibits/presentation/campaign_daily_spend.svg), with June 4 shaded as missing plan, and the [activation chart](../exhibits/presentation/campaign_activation_maturity.svg) showing all signups pending. Keep the full comparable-age explanation on slide 06. Use the [PowerPoint chart extracts](../exhibits/presentation/dashboard_chart_sources.md) and dashboard tables for legible labels.  
**Footer/source:** Campaign-day and channel-cohort marts, exported to the dashboards by `build_dashboards.py`. Daily batch prototype. Campaign plans are externally assumed inputs. Daily CAC is a monitoring proxy.  
**Say:** The strategic chart follows several cohorts at the same customer age, so a cohort that is too young simply stops instead of looking weak. On the operational side, the data checks flag F1's missing June 4 plan before anyone reads pacing. June 2 shows spend with zero signups. Activation is still pending because no signup is 30 days old; a complete week such as May 1–7 shows 75% activation across all channels.

## 08 · Independent checks reconcile the implemented results
**Question:** Q4. **Time:** 1:20.  
**Takeaway:** Controlled cases and source-based recalculation support correctness within the tested synthetic scope.

**On slide**

- **329/329** original comparisons matched across 11 controlled cases and four snapshots.
- **10/10** refund regressions passed after correction.
- **26/26** analytical output files reproduced.
- **Financial tie-out** · $2,170,710.13 recognized revenue − $1,244,633.72 attributable costs = **$926,076.41** contribution before acquisition spend.
- **Marketing tie-out** · **$330,676.79** eligible spend under each allocation method, with zero difference.

**Layout and visual:** Three scorecard tiles and two reconciliation lines.  
**Footer/source:** Stage 1 frozen expectations, Stage 2 independent audit, refund regression results and full run manifest. Synthetic full-visible ledger.  
**Say:** The independent audit read source records, recalculated cents, and checked timestamps, forecast trajectories and rollups. Deposit and funding reversals were outside tested scope.

## 09 · The refund test added an operational integrity control
**Question:** Q5. **Time:** 1:25.  
**Takeaway:** A balanced financial ledger can coexist with an incorrect operational metric.

**On slide**

- **Observed defect** · A malformed credit-account refund referenced a debit purchase and incorrectly cleared its activation. The financial ledger still reconciled.
- **Correction** · Validate original purchase, same account/customer, settlement, chronology and remaining refundable cents. Quarantine invalid links.
- **Observed retest** · Valid debit activation remains qualified at **$60.00 net purchase activity**. All 10 refund regressions pass.
- **Design decisions** · Retain source-level ELT, signed canonical events and a daily batch cadence for the demonstrated use.

**Layout and visual:** Before/after flow above the three architecture decisions.  
**Footer/source:** Original D probe, C-1.0.1 regression sign-off and architecture decision record. Performance and scalability of alternatives were not measured.  
**Say:** The initial grouping trusted the source key alone. Explain why operational references require validity checks independent of the signed ledger.

## 10 · Assignment 3 starts from a reproducible baseline
**Question:** Q5. **Time:** 0:50.  
**Takeaway:** The team can test new source and operating conditions against a documented implementation.

**On slide**

1. Integrated acquisition and product-financial source records with preserved lineage.
2. Produced customer, cohort and campaign outputs for strategic and operational reporting.
3. Independently reproduced the results and corrected an observed business-rule defect.
- **Carry forward** · Frozen inputs, code, cutoffs, reference tests, analytical marts and decisions.
- **Scope boundaries** · Synthetic data, proposed MMP and live warehouse feeds, assumed plans, rule-based forecasts, realized-loss convention, untested deposit/funding reversals and no production scaling benchmark.

**Layout and visual:** Three findings above a compact baseline and limits strip.  
**Footer/source:** Freeze v1.0, C-1.0.1 manifest, validation report and architecture record.  
**Say:** Assignment 3 can change the evidence source or operating requirement and measure its effect against this baseline.

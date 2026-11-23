# Workstream D · Stage 1 independent reference results

Frozen reference with v1.0 assertion addendum. **Expected only. Actual ELT outcomes and pass/fail status are pending execution.** All inputs and values are synthetic.

Source authority: [frozen controlled input](../data/validation_cases/controlled_source.json), [case inventory](../data/validation_cases/README.md), [Frozen project specification](01_project_spec.md) (financial calculations anchored to Workstream A v0.3) and [Workstream B contract](02_data_contract.md). The [machine-readable reference](../data/validation_cases/independent_expected.json) records the fixture SHA-256, cutoffs, source IDs, signed cents, exclusions, counts, ratios as exact numerator/denominator pairs and two fixture forecast versions. Its records are reference assertions, not inserts into production-shaped tables. Missing keys indicate out-of-scope assertions. Null values indicate expected unavailable values. The preserved historical UNRESOLVED_DISPLAY marker is interpreted using the freeze addendum below.

## Independence and snapshots

Read and classified source deliveries by source key before implementation. Transcribed accounting entries directly from the fixture, recalculated the eight daily accruals as balance cents × annual rate / 365, and summed exact cents by account and age. Selected winning touches by inspecting timestamps and identity links. Derived expected forecasts with separate dot products using A's published parameters and exact decimal arithmetic. Neither pipeline SQL nor derived database tables were used.

Primary (P): effective time < 2026-07-01 00:00 UTC; recorded time ≤ the same instant. Replay (R): same effective cutoff, recorded time ≤ 2026-07-03 00:00 UTC. For E029 only, compare ledger visibility at recorded cutoffs 2025-03-11 00:00 UTC and 2025-03-13 00:00 UTC, holding effective cutoff fixed. These two partial views do not assert cohort completeness. Forecast inputs and marketing decision freeze at each individual signup instant.

## Financial reference

Amounts in cents. Parenthesized delivery IDs are business evidence; the JSON preserves their full source keys. Costs are shown as positive expenses except linked reductions, which are negative within their original class. Net contribution subtracts costs.

| Account | Revenue derivation | Cost derivation | P total R / C / net |
|---|---|---|---|
| S · Savings | E002 100000 × .073 / 365 = 20, E004 fee 250 once, E032–E035 +30+90+180+365 | E003 100000 × .0365 / 365 = 10, E006 service 3 | 935 / 13 / 922 |
| D · Debit | E008 150, E012 −60 | E009 30, E010 20, E013 −8 | 90 / 42 / 48 |
| C · Credit | E015 160, E016 100000 × .219 / 365 = 60 | E017 100000 × .073 / 365 = 20, E018 principal charge-off 300, E019 recovery −100 | 220 / 220 / 0 |
| P · Personal | E021 100000 × .146 / 365 = 40, E028 200, E029 −50 | E022 100000 × .073 / 365 = 20 | 190 / 20 / 170 |
| H · Mortgage | E025 10000000 × .073 / 365 = 2000, E030 30000 | E026 10000000 × .0365 / 365 = 1000, E031 20000 | 32000 / 21000 / 11000 |
| **C1 · All visible** | **33435** | **21295** | **33435 / 21295 / 12140** |

Of 36 deliveries, P produces 26 signed components. The other 10 are eight non-economic records (E001, E007, E011, E014, E020, E023, E024 and E027), one duplicate delivery (E005) and one unavailable record (E036). No net income is recognized on face-value purchases/refunds, deposits, loan funding or principal repayment. E029 targets E028, effective March 2, and enters only once available March 12. Net fee is 200 before availability and 150 after. E012 and E013 use the actual March 4 adjustment date. E019 uses May 2 and reduces cost rather than creating revenue. Charge-off/recovery is a realized-loss simplification. In R, E036 contributes 125 revenue cents and no cost, so C1 all-visible net becomes 12265.

## Identity, attribution and spending

| Registration | Canonical result | Touch and explanation |
|---|---|---|
| R1 | C1 via L01, visitor L02 | T02/G. T01 is earlier. T03 occurred before signup and was recorded after it. February touch, March signup. |
| R2 | C2 via L03, visitor L04 | T04/M. |
| R3 | C3 via L05, visitor L06 | T05/F. |
| R4 | C4 via L07 | Unknown, missing visitor link. |
| R5 | C5 via L08, visitor L09 | T06/M exactly at the lower bound. T07 at signup is excluded. |
| R6 | Identity missing | No canonical signup or attribution. |
| R7 | Identity ambiguous, L10–L11 | Visitor L12 does not resolve the conflicting registration identity. |
| R8 | C8 via L13 | Unknown. L14–L15 conflict on the visitor for T08. |

Coverage = 4/6 overall, 3/5 March 2025 and 1/1 June 2026. R6 and R7 are excluded from the canonical denominator. Calendar spend keeps 4200 for G February 26 in February. Touch weighting moves all 4200 to March because T02 is the only winner for that campaign-day. The 900 G March 2 row stays in March under both methods, including with no winning touches. M March 1 (3000) and F March 2 (2000) stay in March, each with a next-day winning signup. Each method independently conserves all 10100 cents, with zero unallocated balance. On the daily mart, all four supplied spend dates have zero same-day signups for that campaign and null CAC. Signup days without corresponding spend rows also have null daily CAC.

| March 2025 campaign and channel | Calendar spend / CAC in cents | Touch-weight spend / CAC in cents | 90-day revenue cents | Calendar → touch-weight ROAS |
|---|---:|---:|---:|---|
| G / Google Ads | 900 / 900 | 5100 / 5100 | 32800 | 32800/900 → 32800/5100 |
| M / Meta Ads | 3000 / 3000 | 3000 / 3000 | 0 | 0 → 0 |
| F / Paid affiliates | 2000 / 2000 | 2000 / 2000 | 0 | 0 → 0 |

Each March paid group has one signup and one campaign. CAC ordering changes from G, F, M to F, M, G from cheapest to most expensive. ROAS ordering is unchanged. Unknown has two March signups and no paid spend assignment. June 2026 M has no supplied spend and a pending 90-day outcome. Neither can support paid CAC or ROAS. February G is a calendar spend-only row. Its CAC has a zero denominator. Freeze v1.0 requires null ROAS, displayed as N/A alongside CAC. Daily ROAS is outside the daily mart contract. M has a partial budget plan and F has a missing daily plan. A full period pacing assertion would require the omitted dates and verified plan coverage.

## Cohort windows and frozen forecast

| Age | C1 upper bound UTC midnight | Primary revenue | Primary cost | Primary net | Replay net |
|---:|---|---:|---:|---:|---:|
| 30 | 2025-03-31 | 32770 | 21095 | 11675 | 11800 |
| 90 | 2025-05-30 | 32800 | 21295 | 11505 | 11630 |
| 180 | 2025-08-28 | 32890 | 21295 | 11595 | 11720 |
| 365 | 2026-03-01 | 33070 | 21295 | 11775 | 11900 |

E032–E035 are excluded at their own upper bound and eligible at later horizons. E035 belongs to all-visible totals and falls outside all four age outputs. E018 and E019 yield +300 −100 cost starting at 90 days. E036 is absent in P and adds 125 revenue and contribution at all ages in R. C1 is the only customer with financial activity. March's five canonical customers are mature and C2/C3/C4/C8 have zero outcomes. Google Ads March totals equal C1, the other March groups sum to zero, and June C5 stays pending with null realized values. On March 2, C1 has all five qualifying actions and counts once overall. Debit's net face value remains 6000 after the linked refund. March overall activation is 1/5 and June has no mature denominator.

Expected cents below use A's per-product weights. EVERYDAY unadjusted 365-day cents by product are (990, 1560, 1950, 450, 180), UNKNOWN is (630, 1080, 1950, 900, 360). Multiply each product amount by the age fraction, sum, apply the acquisition channel multiplier and round half-up once. For C2 at 365 this is 5130 × .95 = 4873.5 → 4874 cents.

| Customer and frozen intent | Baseline 30 / 90 / 180 / 365 | Equal channel 30 / 90 / 180 / 365 |
|---|---|---|
| C1 · I1 EVERYDAY | 226 / 962 / 2269 / 5130 | 226 / 962 / 2269 / 5130 |
| C2 · I2 EVERYDAY | 215 / 914 / 2155 / 4874 | 226 / 962 / 2269 / 5130 |
| C3 · I3 EVERYDAY | 203 / 866 / 2042 / 4617 | 226 / 962 / 2269 / 5130 |
| C4 · UNKNOWN, late I4 | 176 / 827 / 2085 / 4920 | 176 / 827 / 2085 / 4920 |
| C5 · UNKNOWN, no feature | 168 / 785 / 1981 / 4674 | 176 / 827 / 2085 / 4920 |
| C8 · UNKNOWN, no feature | 176 / 827 / 2085 / 4920 | 176 / 827 / 2085 / 4920 |

I1–I3 are available at signup. I4 arrives the following day, so its BORROW value and pointer cannot enter the frozen score. Later product activity and late T03 do not change baseline features or forecasts. Equal-channel scores are separate and acquisition spend, sample and features remain fixed. C5's forecasts are available even while its realized outcomes are pending.

## Workstream C execution matrix

All entries are **awaiting implementation comparison**. Compare exact keys, cents, timestamps, counts and statuses. Compare ratios to independently rounded exact fractions at the declared output scale. Derivations are in the sections above and row-level assertions are in the JSON. Record build/run IDs, observed rows, mismatches and explanations alongside this reference.

| Case and source | Assertion to execute | Error it can detect | Context / determinacy |
|---|---|---|---|
| B01 R1, L01–02, T01–03 | C1 → T02/G remains frozen after T03 availability. | Scoring on future-observed or earliest touch. | Signup, determined. |
| B02 R4/R6/R7/R8, L07/L10–15, T08 | Two unknowns and two identity rejects; coverage 4/6 overall. | Treating ambiguous identity as a valid acquisition, dropping unknowns. | Signup and P counts, determined. |
| B03 R5 and T06–07 | T06 lower-bound inclusion, T07 signup-time exclusion and pending realized ages. | Off-by-one touch window and immature zero filling. | Signup and P, determined. |
| B04 four campaign_day rows, T02/T04/T05, M budget | 10100 conserved in each method, G March CAC changes, zero-registration spend retained, missing plan visible. | Spend loss from inner join, duplicate spend and silent missing-plan zero. | P, allocation and March metrics determined; full pacing unavailable on sparse evidence; spend-only ratios are null under v1.0. |
| B05 E001–E006 | S accrual and signed fee totals; E005 duplicate; E001 source-only and qualifies. | Double fee, deposit as revenue, misapplied rate. | P, DEP_SETTLED represents an external deposit under the v1.0 fixture assumption. |
| B06 E007–E013 | D 90 revenue, 42 cost; partial operational refund; activation stays. | Refund face value booked as expense or sign assigned to wrong class. | P, determined. |
| B07 E014–E019 | C 220 revenue, 220 cost after recovery; check 30- vs 90-day cost. | Provisioning or treating recovery as unrelated revenue. | P, determined. |
| B08 E020–E023, E028–E029 | P totals and 200→150 fee trace; E029 inherits E028 effective time. | Double accounting for principal or changing effective date on restatement. | P and correction snapshots, determined. |
| B09 E024–E027, E030–E031 | H 32000 revenue, 21000 cost, activation on funding. | Recognition of funded principal as revenue or omission of direct origination cost. | P, determined. |
| B10 R1/R5, E032–E036 | Exact boundary exclusions, mature zero vs pending null, 125-cents replay delta. | Inclusive age upper bound, leakage across recorded cutoff. | P/R, determined. |
| B11 I1–I4, R1–R5/R8, T02/T04/T05/T06 | Both forecast grids from same frozen inputs. Confirm baseline immutability on replay. | Using late intent, rescoring from purchases, overwriting baseline. | Signup and P/R, determined. |

## v1.0 assertion addendum

- B04: February G CALENDAR keeps 4200 eligible cents and zero registrations. Assert null CAC and ROAS with ZERO_DENOMINATOR and display N/A. The preserved JSON marker UNRESOLVED_DISPLAY represented a previously unset display rule, not an expected numeric result. Calendar winner_count was absent from its assertions. It is now required to be null. Existing TOUCH_WEIGHT counts remain authoritative.
- B04: Missing or incomplete plan coverage produces unavailable pacing with a null pace_ratio. The sparse fixture establishes no full-period pacing value. Confirm feed coverage during implementation before producing an operational pacing figure.
- B05: DEP_SETTLED in E001 denotes an external settled deposit. Existing activation and exclusion expectations stand.
- B10/B11: UTC cutoffs, exclusive age ends, published weights and scenario multipliers are frozen. Compare money as exact signed cents; use exact fraction inputs rounded half-up at eight decimal places when comparing stored ratios. Baseline and scenario labels in the JSON remain historical fixture version IDs.
- No previously determined expectation changes. Workstream D’s machine-readable reference is preserved verbatim. Actual outcomes remain pending execution.

## Stage 2 · Observed validation and sign-off

**Recommendation: approve the synthetic financial, acquisition, forecasting and cohort evidence for Workstream E drafting. Withhold final sign-off on operational activation until the cross-account refund defect is corrected and the impacted checks are rerun.**

### What was independently executed

- Ran `src/ingest.py` from frozen sources into a separate empty output directory with DuckDB 2.0.1. The new manifest and all 26 output files matched the published run byte for byte. Reviewed the manifest source counts, v1.0 DDL, three SQL stages, Python adjustment logic and two model payloads. Independently hashed the model payloads and confirmed both stored hashes and the sensitivity parent link.
- Ran [the independent audit](../src/audit_workstream_d.py). Its direct gzip reads, integer-cent checks and rational arithmetic do not import the ELT. It recalculated full-source identity, attribution, spend and forecast rows, compared every recognized financial component to its source delivery, then independently rolled ledger amounts to customer age and calendar cohort. Results are preserved in [the audit extract](../exhibits/tables/d2_independent_reconciliation.json). This verifies arithmetic and the generated-source shapes. The full source contains no identity retraction sequences.
- Reran the four controlled snapshots and inspected all 329 reported comparisons against the immutable Stage 1 JSON, including the explicit freeze addendum. This used C's comparison runner and the independently established D reference. The raw-source audit was a separate method. See [the validation exhibit](../exhibits/tables/d2_validation_summary.md).
- Ran a distinct in-memory negative probe by appending an invalid source delivery to a copy of the controlled fixture. The archived fixture and independent expectations remained unchanged. See [the probe record](../exhibits/tables/d2_refund_integrity_probe.json).

### Executed controlled results

| Case | Observed reference agreement |
|---|---|
| B01–B03 | R1 → C1 → T02 despite late T03. R4/R8 remain unknown for different reasons. R6/R7 do not enter canonical counts. T06 qualifies at the lower bound and T07 at signup does not. |
| B04 | Both allocations reconcile 10,100 cents. G's 4,200-cent February spend moves to March only under touch weighting. Its calendar spend-only rows suppress CAC and ROAS. Missing plans leave pacing unavailable. |
| B05–B06 | Savings fee E004 is included once and E005 is a duplicate. Deposit is source-only. Debit partial refund leaves the purchase qualifying and recognizes linked component reductions only. |
| B07–B09 | Credit confirms E018 and nets E019 as cost recovery. E029 appears after its recorded time and inherits E028's effective date. Personal and mortgage principal remain source-only. All five account totals match. |
| B10 | Four maturity boundaries are exclusive. C5 remains pending. E036 increases C1's realized contribution by 125 cents in the later snapshot. |
| B11 | Both forecast scenarios match at all ages on both recorded snapshots. Late I4, late T03 and subsequent product activity leave the baseline unchanged. |

All frozen-case checks passed. The failed probe used `E_D2_BAD_REFUND` / `core:d2-bad-refund`, a settled 10,000-cent refund on credit account C, referencing debit purchase `core:d-purchase` on account D. Expected outcome was invalid-reference quarantine and retention of C1's debit activation. Observed debit activation was `NO_QUALIFYING_EVENT`, with no exception row for the malformed refund. To reproduce, clone E011 from the controlled fixture in memory, replace delivery ID, source key, account and amount with the probe values, and run the primary cutoffs in a separate scratch connection. The failure occurs because the refund aggregate in `03_reporting.sql` keys on the original source key without validating same-account ownership or a cumulative operational refund cap. The test did not introduce a signed economic component or invalidate the frozen case outcomes.

### Independently verified full snapshot

| Product | Revenue | Attributable costs | Contribution |
|---|---:|---:|---:|
| Savings | $48,740.31 | $26,440.38 | $22,299.93 |
| Debit | $9,172.88 | $8,130.30 | $1,042.58 |
| Credit | $67,912.82 | $162,959.20 | −$95,046.38 |
| Personal loans | $195,628.32 | $85,892.40 | $109,735.92 |
| Mortgages | $1,849,255.80 | $961,211.44 | $888,044.36 |
| **Total** | **$2,170,710.13** | **$1,244,633.72** | **$926,076.41** |

From 850,786 financial deliveries, 827,038 are recognized, 23,703 are non-economic, 23 fall after the recorded cutoff, and 22 are duplicates. The accepted canonical activity count is 850,741. Every recognized component matched source key, delivery, customer, class, exact cents, timestamps and original component link. These all-visible amounts include eligible activity outside the four age windows. Of 5,000 accepted customers, 4,512 (90.24%) match a paid touch. The 488 unknowns remain identifiable, including 284 with no eligible touch, 161 with missing visitor links, and 43 with ambiguous visitor links. The two unresolved registrations stay outside the canonical denominator.

Each of the 6,896 spend allocation rows matched the separate source-cent reroll. Both methods preserve **$330,676.79**. The full campaign-day mart retains 859 zero-registration days with positive spend ($81,257.19). The full channel cohort mart has no spend-only cohort. The controlled February G row provides that check. Of 3,276 campaign-day outputs, 612 have unavailable cumulative plan and all 612 have null pacing ratios. Thirty-six source plan days are explicitly missing. These nulls preserve the information about plan coverage.

The [worked C02703 trace](../exhibits/tables/d2_customer_trace.md) reconciles 479 components over five products to $321.71 at 90 days and to that customer's inclusion in the March unknown cohort. The independent audit matched 20,000 history rows and 576 populated calendar cohort rows across both forecast scenarios. It verified that pending realized values remain null and the forecast numerator uses the same mature customers and age as each finalized comparison. Spend allocations under both methods were independently rebuilt. Published ratio and historical exhibits were inspected for their numerator/denominator context. The separate cohort reroll focused on calendar rows.

### Forecast and sensitivity findings

The independent audit rebuilt 40,000 forecast checkpoints for 5,000 customers, including one baseline and one sensitivity trajectory per customer. It checked feature ID, normalized intent, and absence of a feature-available timestamp after cutoff. The rerun and controlled replay reproduce the baseline. The equal-channel scenario has a distinct version and parameter hash and uses the same cohort, customers and spend. It adds $11,679.11 to summed 365-day forecasts, with the changes concentrated in Meta and paid affiliates. The paid-channel mean range shrinks from about $5.52 to $0.41. The remaining difference is model-input composition. These results establish assumption sensitivity rather than predictive accuracy.

Spend allocation changes CAC ordering in six of 15 mature 90-day months and ROAS ordering in one. The [sensitivity exhibit](../exhibits/tables/d2_sensitivity.md) preserves the same sample and underlying observed revenue in both allocation methods. March and September 2025 are fully mature 90-day comparisons. Interpret such cohort differences as synthetic scenario outcomes using reported customer counts and aligned age, keeping revenue ROAS separate from net contribution. The mortgage-heavy financial mix and sampled acquisition channels can make month-level rankings volatile. There is no evidence of causal or generalized channel effectiveness.

### Fixes and remaining limitations

| Item | Disposition |
|---|---|
| Cross-account refund | **Correction and regression required.** Resolve original purchase before aggregation. Require matching account and valid chronology, settled state and cumulative reduction ≤ original purchase. Log and exclude invalid or over-cap links. Add the cross-account test, repeated-refund cap and conflicting-source cases. Rerun frozen cases, probe and full snapshot before using activation in final exhibits. |
| Deposit or funding reversal | **Additional source-contract decision and test.** No explicit compatible operational reversal events were exercised. Define how a valid original-link reversal affects product activation and test a full and partial reversal before claiming coverage. |
| Realized-loss simplification | **Document.** Confirmed charge-offs and recoveries are recognized under v1.0. Expected-loss provisions and reserve reconciliation require a separate expanded scope. |
| Borrowing behavior and channel differences | **Document.** Synthetic volume, product probabilities, observed purchaser mix and imposed forecast multipliers explain the analytical variation. |
| Local DuckDB | **Additional production evaluation if adopted.** No empirical production costs, scaling, SLAs, concurrency or reliability advantages were established. |

No frozen input or expected result was altered. Stage 2 does not change the pipeline. Operational activation should remain labeled provisional until the correction is reviewed.

## Correction review · C-1.0.1

**Sign-off recommendation: approve the corrected synthetic demonstration, including operational activation within the tested scope, for Workstream E.** The earlier Stage 2 hold above records the C-1.0.0 result. This addendum supersedes that hold for C-1.0.1.

The original failing diagnostic added a settled credit-account refund pointing to a debit-account purchase. C-1.0.0 grouped refunds by the original source key alone. C-1.0.1 now validates the original's existence, type, settlement, account/customer match, effective and recorded chronology, and remaining refundable cents before SQL considers the deduction. The existing canonical activity stage handles identical and conflicting deliveries first. The corrected run rejected E_D2_BAD_REFUND as INVALID_REFERENCE with ACCOUNT_OR_CUSTOMER_MISMATCH. It retained the 4,000-cent valid refund, net 6,000 cents, and C1's debit activation. The original [failed probe](../exhibits/tables/d2_refund_integrity_probe.json) remains archived.

D independently checked the separate regression expectations against the 10,000-cent original purchase and the overlaid source records. That arithmetic, observed purchase qualification, activation, and exception classification match in all ten cases. In the cumulative case, the valid 6,000 cents left 4,000 available, the 4,500-cent event was rejected in full, and the later 1,000-cent event was accepted. In the duplicate case, the 6,000 cents were accepted once. In the conflicting case, both payloads were rejected upstream. See the [regression exhibit](../exhibits/tables/refund_regression_signoff.md) and [observed data](../exhibits/tables/refund_regression_results.json). All 329 frozen-case comparisons across the original 11 cases still match.

The corrected full run used the same nine verified source files and cutoffs. All 26 published output files are byte-identical to the C-1.0.0 copies, including activation, campaign performance, the ledger, both spend allocations, cohort and customer histories, and both forecast scenarios. The manifest's build version is the sole manifest difference. The separate full-source audit reproduced its prior exact output. Verified amounts remain $2,170,710.13 in revenue, $1,244,633.72 in attributable costs, $926,076.41 in contribution before acquisition spend, and $330,676.79 in eligible spend under each allocation method. No full-dataset metric changed. The negative probe now has a corrected activation result and an explicit exception.

Deposit and funding reversals still require explicit source-representation decisions and additional cases. Confirmed principal charge-offs and recoveries remain a simplified realized-loss recognition convention. Expected-loss provisioning and production scaling remain outside the validated scope.

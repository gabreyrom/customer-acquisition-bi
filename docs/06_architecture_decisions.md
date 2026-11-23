# Architecture decisions

Draft v0.1 · Member 4

| Choice | Assignment 1 baseline | Assignment 2 design | Evidence to collect |
|---|---|---|---|
| Processing | Daily warehouse batch with SQL/dbt and Metabase, compared with streaming (slides 8 and 10) | Daily batch for quarterly and daily/weekly decisions, static prototype | Show freshness and reconciled source snapshot supporting these decision cycles |
| Transform placement | SQL transformations in baseline architecture; ETL versus ELT discussed in revised summary | Controlled source staging followed by ELT in DuckDB | Replay a correction and trace changes back to retained records. Compare with pre-load ETL for sensitive fields and upstream controls |
| Financial representation | Savings and card revenue inputs aggregated for 90-day ROAS | Canonical signed events across five products | Compare event-level audit and correction trace with preaggregated totals, including the grain needed to reproduce each KPI |
| Historical representation | Fully mature 90-day cohorts (slide 7) | Fixed versioned forecast and multiple comparable age checkpoints | Demonstrate exclusions at an observation cutoff and unchanged forecast after later data arrives |

Conclusions pending actual demonstration. Preserve schemas, business rules, evidence and result snapshots to support Assignment 3 source and operating changes.

## D Stage 1 · Evidence plan

| Decision | Prototype evidence C/D can collect | Reasoned judgment requiring other evidence |
|---|---|---|
| ELT versus ETL | Use identical fixture and compare preservation of rejected, late and duplicate deliveries, replay of E029/E036, and ability to explain a report cell by source key. Document what must be filtered before loading. | Enterprise cost, scale, privacy exposure and maintainability depend on actual infrastructure and governance. |
| Canonical ledger versus product totals | Compare whether a product total alone explains the same linked refund, fee restatement and recovery across two cutoffs. Test reconciliation and whether any necessary source lineage would have to be retained alongside totals. | Production storage/latency tradeoffs and recurring maintenance effort require observed workloads. |
| Daily batch versus streaming | Record batch cutoffs, reproducible delivery/run IDs, when E036 becomes visible, and whether an output snapshot can serve daily pacing and weekly review. | Streaming latency, throughput, incident recovery and uptime need deployed systems and measured workloads. |
| Effective versus recorded timestamps | Compare age boundary rows and cutoff replay. Test whether using only one timestamp would admit E036 early, place E029 in the wrong business window, or change a frozen forecast. | Source clock accuracy, upstream delivery guarantees and acceptable restatement policy require operational evidence. |

Use the controlled fixture to substantiate traceability and reproducibility claims. Record actual architecture observations after implementation. No comparative production performance, cost or reliability claim is established at Stage 1.

## Stage 2 · Decision outcomes

| Choice and selected approach | Credible alternative and relevant constraint | Executed prototype evidence | Limitation and verdict |
|---|---|---|---|
| Batch ELT with retained source history | ETL can apply validation or de-identification before warehouse load. The design still needs traceable original rows and replay as rules evolve. | 26 exports reproduced byte for byte. Source deliveries explain duplicate suppression and recorded-time exclusions. | **Confirmed for prototype auditability.** Sensitive-field loading, governance and production execution cost remain untested. |
| Canonical event ledger before aggregation | Product totals with attached source provenance are possible. A summary alone loses component timing, class and reversal links needed for replays. | All 827,038 component rows match source-based calculations, including the recovery and effective-date restatement. A 479-component worked example ties to age and cohort. | **Confirmed with refinement.** Add validation to operational event links. A balanced ledger coexisted with a failed activation probe. Storage and query workload comparisons were not run. |
| Daily batch with explicit freshness | Streaming could deliver intraday spend and activation updates if users need a tighter decision window and feeds support it. | Same-snapshot reruns agree; missing plans stayed unavailable and daily spend retained zero-registration days. | **Confirmed as a fit for the stated daily/weekly cadence.** No measured streaming or batch service-level comparison. |
| Separate effective and recorded timestamps | A single processing clock is simpler, but cannot independently represent economic timing and source availability. | E036 adds 125 cents only in replay. E029 retains its original effective date after the correction arrives. Exclusive age boundaries agree at all four checkpoints. | **Confirmed.** Real source clock accuracy, correction finality and data completeness guarantees need operational evidence. |
| Immutable acquisition-time prediction with separate sensitivity | Continuously updated predictions could support retention decisions, but would change the baseline used to assess acquisition. | 40,000 point-in-time forecast rows agree independently. Controlled replay leaves baseline unchanged. Sensitivity changes only the multiplier model parameter. | **Confirmed for acquisition comparability.** No accuracy claim. A later retention forecast needs a separately labeled snapshot and purpose. |

### Consequential refinement and Assignment 3

Validate operational reference links at the same standard as financial adjustments. The malformed refund changed activation despite leaving the signed ledger unaffected. Before treating activation as evidence, quarantine unmatched or cross-account references, enforce refund caps in ordered source time, and verify that the original qualifying purchase is preserved when a bad reference is rejected. Assignment 3 can change operating cadence or source delivery rules and compare with these frozen snapshots. Preserve this negative case and its corrected replay as a baseline for future reliability evaluation.

### Operational reference refinement · corrected and retested

C-1.0.1 retains the v1.0 ELT design and enforces operational refund eligibility before activation aggregation. The original failure is preserved as evidence that financial reconciliation and operational referential integrity answer different questions. The corrected cross-account probe preserves valid activation and emits an inspectable exception. The other nine refund regressions and 329 original comparisons agree, and the full outputs reproduce without analytic changes. The design refinement is verified for the tested refund cases. Deposit/funding reversals need additional scenarios and production performance remains unmeasured.

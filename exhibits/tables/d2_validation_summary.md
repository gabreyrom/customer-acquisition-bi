# What the validation established

| Check | Result | Evidence |
|---|---|---|
| Clean rerun | Pass | All 26 output files and the run manifest reproduced byte for byte. |
| Frozen controlled cases B01–B11 | Pass | 329 matching comparisons across primary, replay and two fee-correction snapshots. No discrepancy in the frozen cases. |
| Independent full source-to-ledger check | Pass | 850,786 deliveries accounted for. All 827,038 recognized components agree by source key, cents, class and timestamps. |
| Independent acquisition, history and forecast checks | Pass | 5,000 identities and attribution records, 20,000 age rows, 40,000 forecast checkpoints and 576 populated calendar cohort/scenario rows match. |
| Independent spend check | Pass | All 6,896 allocation rows match. Each method preserves $330,676.79. |
| Malformed cross-account refund probe | **Fail** | The invalid link silently voided C1's valid debit activation. Quarantine invalid links before activation aggregation. |
| Deposit and funding reversal coverage | Untested | No explicit reversal-link examples were executed. |

Scope: synthetic source and local execution only. Frozen-case and financial results are suitable as synthetic demonstration evidence. Activation sign-off remains conditional on the refund correction and regression rerun.

## C-1.0.1 retest and sign-off

The C-1.0.0 failure above remains part of the validation history. The corrected build passed the original malformed probe and all nine additional refund cases, with all 329 frozen comparisons still matching. The full-source outputs are identical, and the independent financial and analytical audit reproduced its prior results. Workstream E can use activation for the tested synthetic conditions. See the [refund regression evidence](refund_regression_signoff.md).

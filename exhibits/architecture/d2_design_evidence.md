# What the implementation changed or confirmed

| Decision | Evidence | Assessment |
|---|---|---|
| Keep source and use ELT | Raw delivery IDs survive duplicates, late observations, and correction replay. | Confirm auditability for this prototype. Keep source handling controls and exception policies explicit. |
| Standardize financial events before aggregating | A cross-product 479-component trace reconciles to a customer and cohort. | Confirm component-level lineage. Refine operational reference checks after the malformed refund test. |
| Use daily batch for this business cadence | Identical source snapshots reproduced all outputs, with missing pacing inputs left unavailable. | Supports daily/weekly inspection. Streaming benefits were not measured. |
| Maintain two clocks | A late fee changes replay totals without changing its economic date. A restatement preserves its original effective date. | Confirm distinct effective and recorded dates. Preserve snapshots and label restatements. |
| Keep a frozen acquisition forecast | Both scenarios reproduce from the same immutable features. | Confirm immutable baseline for attribution of differences. Supplement with a separate recalibration product if needed later. |

**Design lesson:** Source lineage must cover operational links as well as recognized financial events. A malformed refund did not alter the controlled ledger, yet it altered the activation decision. A balanced ledger by itself cannot establish operational metric correctness.

## Corrected operational control

C-1.0.1 validates the original purchase, ownership, settlement, chronology and remaining cents before applying a refund to activation. The previously failing link now produces an exception and leaves the valid purchase qualified. Ten targeted cases passed. This refinement is independent of financial-ledger reconciliation and preserves the existing batch ELT design.

# Operational refund regression · C-1.0.1

The Stage 2 cross-account refund probe failed on C-1.0.0. It is preserved in [the original probe record](d2_refund_integrity_probe.json). C-1.0.1 quarantines invalid links before the activation calculation.

All amounts below are cents. The original debit purchase is `core:d-purchase` on account D for 10,000 cents. All expected and observed values matched under the primary snapshot. See [the expected-versus-observed record](refund_regression_results.json) for exact delivery IDs, reason codes, and scratch-input hashes.

| Case | Independent derivation and observed net cents | Activation | Observed exception |
|---|---:|---|---|
| Original cross-account probe | 10,000 − 4,000 valid refund = 6,000 | Qualified | Cross-account reference rejected |
| Missing purchase | 10,000 − 0 = 10,000 | Qualified | Missing original rejected |
| Refund exceeds purchase | 10,001 exceeds the 10,000 cap, leaving 10,000 | Qualified | Over-reversal |
| Cumulative cap | 6,000 accepted, 4,500 rejected, 1,000 accepted. Net 3,000 | Qualified | Over-reversal on the middle refund only |
| Valid partial | 10,000 − 4,000 = 6,000 | Qualified | None |
| Valid full | 10,000 − 10,000 = 0 | No qualifying event | None |
| Duplicate delivery | 10,000 − 6,000 once = 4,000 | Qualified | Second delivery logged as duplicate |
| Invalid chronology | Refund predates purchase, leaving 10,000 | Qualified | Chronology violation |
| Conflicting deliveries | Both versions quarantined, leaving 10,000 | Qualified | Two conflicting-source-key exceptions |
| Original purchase pending | Neither purchase nor refund qualifies. Face value remains 10,000 | No qualifying event | Invalid settlement state |

The cap rejects the entire offending refund and does not consume any of the remaining refundable amount. The next valid refund can still use that capacity. Purchase qualification depends on positive net value and settled source state. All original 329 assertions also matched.

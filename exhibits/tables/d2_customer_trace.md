# C02703 · From source records to 90-day contribution

Signup `R02703`, 2025-03-16 13:00 UTC. The realized window ends 2025-06-14 13:00 UTC, exclusive. Primary effective cutoff is July 1, 2026 00:00 UTC, exclusive, and recorded cutoff is the same instant, inclusive.

| Account and product | Recognized components | Revenue | Costs | Contribution |
|---|---:|---:|---:|---:|
| A027030 · Savings | 151 | $17.25 | $9.29 | $7.96 |
| A027031 · Debit | 11 | $4.15 | $3.73 | $0.42 |
| A027032 · Credit | 133 | $51.35 | $20.33 | $31.02 |
| A027033 · Personal loan | 98 | $135.44 | $46.10 | $89.34 |
| A027034 · Mortgage | 86 | $1,140.48 | $947.51 | $192.97 |
| **Customer total** | **479** | **$1,348.67** | **$1,026.96** | **$321.71** |

Example source line `D00457542` / `core:E00457542` has a 104,900-cent savings balance and 0.073 annual treasury rate. Its standardized component is `core:E00457542/SAV_TREASURY_INCOME`, for 21 cents after half-up rounding of 104,900 × 0.073 / 365. The corresponding depositor interest source `core:E00457543` contributes 10 cents of cost. The personal loan's fee `core:E00457847` contributes 4,700 cents of revenue. Funding and repaid principal remain source-only.

The customer has no eligible marketing touch. The history contributes **$321.71 of the $2,373.53** 90-day contribution for the 36 mature March 2025 unknown-channel customers. The same customer's frozen 90-day expectation is $9.62. The full 479-row trace is in `data/analytical_outputs/worked_customer_trace.csv`. The difference is synthetic and has no predictive interpretation outside this exercise.

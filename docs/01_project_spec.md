# Workstream A · Financial rules and acquisition value

v1.0 · Frozen for implementation · [Freeze record](07_specification_freeze_v1.0.md)

## Decision log

| Status | Decision |
|---|---|
| Agreed scope | Hypothetical US digital bank; Google Ads, Meta Ads and paid affiliates; savings, debit, credit, personal loans and mortgages; approximately 5,000 synthetic customers; January 2025–June 2026; USD; Python/DuckDB/SQL and static reporting. |
| Approved | 30-day last tracked touch, unknown reported separately, compatible CAC and cohort grains, zero-registration spend included, principal and deposit movements excluded, fixed acquisition-time forecast at 30/90/180/365 days, daily pacing and weekly efficiency review. |
| Frozen conventions | UTC rolling elapsed-day boundaries, immutable attribution at acquisition, base spend by original spend month, touch-weighted allocation as sensitivity, 30-day product-use activation, realized-loss accounting and published synthetic forecast parameters. |
| Implementation defaults | Operational alert thresholds are prototype defaults. Keep the D reference values independent of pipeline execution. |

Assignment 1 used 90-day revenue ROAS as its primary measure. Keep that series for continuity and use contribution for quarterly allocation discussions. The original architecture used daily batch, SQL/dbt and Metabase. The prototype uses daily batch ELT and static outputs. Acquisition measures are descriptive and support investigation or budget tests.

## Identity, attribution and spend

Resolve source registration, account and visitor identifiers through effective, timestamped identity links before attributing marketing. Use the earliest valid signup per canonical customer. Identical re-deliveries collapse by source key; conflicting duplicates or ambiguous links are flagged. An unresolved canonical identity is excluded from customer denominators and counted in the exception ledger. A resolved customer with no eligible touch stays in the denominator for overall activation and in the unknown attribution bucket.

At registration instant t, use an identity link available and effective by t. Among touches in [t − 30 days, t) recorded by t, select the latest eligible touch in an approved paid campaign. Break equal timestamps by ascending touch ID. Keep the selected touch, rule version and status. Distinguish missing link, ambiguous visitor linkage and no eligible touch as unknown reasons. Later touches or backfills cannot change the acquisition-time forecast snapshot. Keep unknown customers visible without assigning paid spend to them.

**Base allocation:** A campaign's eligible actual spend for each UTC day belongs to that campaign and the calendar month containing that day. A customer's assigned campaign and UTC signup month determine cohort membership, even if the touch occurred in the prior month. Sum spend independently of the customer join, retaining spend-only campaigns, and aggregate to channel-month before dividing. This is a calendar-period proxy and can misalign costs near month boundaries.

**Sensitivity:** For each campaign-day spend row, distribute its spend across signup months in proportion to counts of customers whose winning touches came from that campaign-day. Where no winners are observed, leave the full row in the spend day's month. Break penny ties by earliest signup month after distributing residual cents by largest remainder. Use the same registered population and cutoff for both methods, show changes in ranking and reconcile total spend in each. Flag end-of-history spend dates whose 30-day conversion opportunity is incomplete.

## Time, product activation and reporting

Use UTC elapsed time. An N-day horizon covers [registration_at, registration_at + N × 24 hours). A checkpoint is mature when its exclusive end is at or before the data completeness cutoff. Use records available at the declared reporting as-of time, with recorded_at at or before that instant. Use July 1, 2026 00:00 UTC as the proposed exclusive effective-data cutoff. For signup-month comparisons require the entire month to have had N days to mature. Include all customers with zero activity at mature ages. Keep later cohorts visible with outcomes pending. Historical published snapshots retain their cutoffs and can be replayed.

A qualifying action must occur within the first 30 days, and count once per customer for overall activation. Product-level flags can overlap. A qualifying payment or funding event fully invalidated by a correction available at reporting as-of loses eligibility. Product opening, application and authorization alone do not qualify.

| Product | First qualifying activation |
|---|---|
| Savings | First settled external deposit of at least $10. In the frozen synthetic fixture, DEP_SETTLED denotes an external settled deposit. |
| Debit card | First settled purchase with positive net purchase amount |
| Credit card | First settled purchase with positive net purchase amount |
| Personal loan | First settled funding with positive net disbursement |
| Mortgage | First settled funding with positive net disbursement |

| KPI | Calculation and grain |
|---|---|
| Registrations | Distinct canonical new customers by signup date or month and assigned campaign/channel; show unknown and identity exceptions separately. |
| Attribution coverage | Paid-attributed canonical registrations ÷ all canonical registrations in the signup period. |
| CAC | Eligible actual spend ÷ new attributed customers for the same campaign or channel and reporting period; daily operational CAC uses spend date with same-day registrations as a pacing proxy, subject to conversion lag. |
| 30-day activation rate | Mature customers with at least one qualifying event ÷ mature acquired customers in the group. Recent registrations are pending. |
| 90-day revenue per customer | Signed recognized eligible revenue in first 90 days ÷ all customers in the eligible group. |
| 90-day revenue ROAS | Same revenue ÷ the group's allocated acquisition spend. |
| Predicted LTV/CAC | Mean fixed 365-day contribution ÷ group CAC, equivalent to sum of frozen predictions ÷ matching spend when populations match. |
| Realized cumulative contribution | Signed revenue less attributable costs for the first N days; display total and mean per acquired customer. Compare with the sum or mean of the same customers' frozen N-day expectations. |
| Realized contribution per spend / after spend | Group realized contribution at age N ÷ matched acquisition spend / group realized contribution minus matched spend, respectively. |

Calculate group ratios from summed inputs. Return null with a reason for zero denominators and unmatched spend; publish a spend-only row with its spend and zero registrations. Store null CAC and ROAS and display both as N/A. Unknown attribution has null paid efficiency ratios. For pacing, use actual spend to date ÷ planned spend to date only when the plan is complete and positive and the actuals are available. If the plan is missing or incomplete, show plan-to-date pacing as unavailable and never substitute zero. Remaining approved budget = period budget − actual spend to date, when cap and actuals are known. Start weekly investigations at 20 or more registrations when CAC exceeds target by 20% or mature activation is 10 percentage points below target. For daily pacing flag actual above 110% of positive cumulative plan. Thresholds are proposed. Surface feed freshness, missing plans and attribution coverage before changes to campaign limits.

## Recognition and canonical financial events

USD amounts are rounded half-up to cents per source-derived component; aggregate cents exactly. Revenue and cost classes each store positive normal amounts; a reversal stores the negative amount in the same class. Contribution = sum(revenue) − sum(cost). Use either gross component inputs plus their costs or a documented decomposed source feed. Recognize each source component once. Exclude transfers, deposits, withdrawals, purchase face values, draws, principal repayments and funded principal from earnings. Direct servicing is per account or activity as applicable. Acquisition costs stay in the spend ledger. Exclude overhead, tax and capital charges for the prototype.

| Product | Revenue event codes and recognition | Cost event codes and recognition |
|---|---|---|
| Savings | SAV_TREASURY_INCOME on end-of-day settled balance × annual treasury yield / 365; SAV_FEE when posted | SAV_DEPOSIT_INTEREST on same balance × annual depositor rate / 365; SAV_SERVICE when incurred. Treasury income is allocated once, with no additional treasury charge in this simplified model. |
| Debit | DEBIT_INTERCHANGE at settlement, gross; DEBIT_FEE when posted | DEBIT_PROCESSING at settlement, DEBIT_REWARD when earned, DEBIT_FRAUD for separately borne confirmed loss, DEBIT_SERVICE when incurred |
| Credit card | CREDIT_INTERCHANGE at settlement; CREDIT_INTEREST on eligible end-of-day revolving balance × annual rate / 365; CREDIT_FEE when posted | CREDIT_PROCESSING, CREDIT_REWARD, CREDIT_SERVICE as incurred; CREDIT_FUNDING on funded receivables × funding rate / 365; CREDIT_LOSS at confirmed net principal charge-off |
| Personal loan | PERSONAL_INTEREST on funded performing end-of-day principal × annual rate / 365; PERSONAL_FEE when earned and posted | PERSONAL_FUNDING on funded outstanding principal × rate / 365; PERSONAL_SERVICE, PERSONAL_COLLECTION as incurred; PERSONAL_LOSS at confirmed principal charge-off |
| Mortgage | MORTGAGE_INTEREST on funded performing end-of-day principal × annual rate / 365; MORTGAGE_FEE when earned and posted | MORTGAGE_FUNDING on funded outstanding principal × rate / 365; MORTGAGE_ORIGINATION at funding; MORTGAGE_SERVICE as incurred; MORTGAGE_LOSS at confirmed principal charge-off |

Proposed simplifications: credit interest accrues on performing revolving balances after applicable grace rules as supplied by the source. Stop accrual on nonperforming amounts and stop funding charges after principal is removed from funded balances. Interest cash receipts settle accrued balances. Loan repayments and prepayment reduce principal without generating revenue. A waived posted fee reverses fee revenue. A refund or chargeback reverses only actual refunded revenue or reimbursed costs and only books unrecovered fraud as a separate loss where borne. Credit recoveries reduce the associated credit-loss cost. This realized-loss ledger carries no expected loss provision. The forecast can incorporate expected losses through its net assumptions. Exclude mortgage sales, refinance gain and secondary-market adjustments. Simplified posted fee treatment is for prototype economics.

Corrections to misstated recognition use an append-only signed adjustment at the original effective instant with their own recorded timestamp. Actual later economic events, such as recoveries and settled customer refunds, use their own effective instant. Reference the original event and cap cumulative linked reductions at the original component amount. A restatement requiring a replacement books the reversal and a distinct replacement. For pending, ambiguous or over-reversal records, retain source evidence and quarantine the invalid component.

### Worked examples in USD

| Product | Source facts and signed components | Contribution |
|---|---|---:|
| Savings | A $1,000 settled deposit leaves a $1,000 daily balance. Treasury yield 7.30% gives 0.20, depositor interest 3.65% gives 0.10, servicing costs 0.03. Deposit excluded. | 0.07 |
| Debit | $100 settled purchase yields interchange 1.50, processing 0.30 and reward 0.20. Partial refund reverses 0.60 interchange and 0.08 reward; processing unchanged. Net revenue 0.90, net cost 0.42. | 0.48 |
| Credit card | $100 settled purchase yields 1.60 interchange, processing 0.30, rewards 0.40. Separate $1,000 eligible daily revolving balance yields 0.60 interest at 21.90% and 0.20 funding at 7.30%. Earlier principal charge-off of 3.00 and recovery of 1.00 yield net loss 2.00. | −0.70 |
| Personal loan | $1,000 performing daily balance earns 0.40 interest at 14.60%; funding at 7.30% costs 0.20; eligible fees 2.00 less a 0.50 waiver and servicing 0.30. Subsequent $100 principal repayment reduces future balance. | 1.40 |
| Mortgage | A $100,000 mortgage funds and accrues one day: 20.00 interest at 7.30%, 10.00 funding at 3.65%, earned fee 300, direct origination 200 and servicing 2. Funded principal excluded. | 108.00 |

## Frozen acquisition forecast v1

For every canonical acquisition, create one snapshot as of registration and one rule-versioned prediction. Use only the attributed channel known then (including UNKNOWN) and a registration-time intent enum (EVERYDAY, BORROW, UNKNOWN) collected independently from observed product adoption. If intent is missing, invalid or recorded after registration, use UNKNOWN. Store the normalized feature values, source IDs, availability times, feature cutoff, scoring timestamp, immutable parameter version and parameter content hash. A delayed computation uses the same historical inputs and a separate write timestamp. No PII or post-acquisition transactions, activation or funding status enter the score.

Use expected 365-day product contributions = assumed likelihood of product activity during the year × conditional net first-year contribution × channel multiplier. Sum product amounts; product activations may overlap and each conditional amount already nets attributable costs and assumed losses. These parameters are frozen synthetic demonstration assumptions, with no empirical channel claim. Preserve the baseline and score the all-1.00 channel-multiplier sensitivity separately using the identical frozen snapshots.

| Product | P(EVERYDAY) | P(BORROW) | P(UNKNOWN) | Conditional net USD | Cumulative fractions at 30 / 90 / 180 / 365 |
|---|---:|---:|---:|---:|---|
| Savings | .55 | .25 | .35 | 18 | .07 / .22 / .47 / 1 |
| Debit | .65 | .30 | .45 | 24 | .06 / .23 / .48 / 1 |
| Credit card | .30 | .45 | .30 | 65 | .03 / .17 / .43 / 1 |
| Personal loan | .05 | .25 | .10 | 90 | .01 / .10 / .38 / 1 |
| Mortgage | .01 | .06 | .02 | 180 | .00 / .05 / .25 / 1 |

Channel multiplier: Google Ads 1.00, Meta Ads 0.95, paid affiliates 0.90, UNKNOWN 1.00. For each checkpoint, multiply each unrounded product expectation by its cumulative fraction, sum, then round half-up to cents. Day 365 equals the headline forecast. Example: Google Ads + EVERYDAY has product expectations 9.90, 15.60, 19.50, 4.50 and 1.80. Checkpoints are 2.26, 9.62, 22.69 and 51.30. Use same-aged realized outcomes even when realized contribution is negative. A second model agreeing is insufficient validation.

## B and D handoff

- B: Update source grain and constraints in the data contract. Include identity bridges, late touches, spend-only days and a cross-month touch; product-specific balances, fees, purchase settlement, funding and repayment; original/correction links and available-at features. Propose source fields and accepted exception statuses before generation.
- D: Independently compute expected mappings, coverage, both spend-allocation variants, reconciled ROAS/CAC, each product ledger, activation and an age-boundary case. Check that spend and ledger totals reconcile and independently calculate frozen checkpoints from inputs, including a recorded-late feature case. Prepare cases before full generation. Validate observed outputs only once the pipeline is available.

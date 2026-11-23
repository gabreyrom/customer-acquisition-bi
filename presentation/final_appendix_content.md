# Technical appendix · Slide-ready evidence

Use A–F after main slide 10. The tables and examples below can be pasted into PowerPoint as editable text and tables. Split pages where necessary to keep text readable. Numbers describe the synthetic demonstration.

## A1 · Physical schema inventory

| Layer | Tables and grains |
|---|---|
| Acquisition sources · 7 | `campaign` per campaign, `campaign_day` per campaign/day/version, `campaign_budget` per campaign budget period/version, `registration` per source signup, `identity_link` per identity claim, `marketing_touch` per touch, `registration_feature` per observed feature record |
| Financial sources · 2 | `product_account` per account, `product_activity_delivery` per source delivery |
| Integration · 7 | `run_manifest` per run, `exception_log` per run/source/reason, `acquisition` per canonical customer, `attribution` per canonical customer, `canonical_activity` per run/source key, `financial_event` per run/component, `activation` per run/customer/product |
| Forecast and reporting · 8 | `feature_snapshot` per canonical customer, `forecast_model` per model version, `prediction` per customer/model, `prediction_age` per customer/model/age, `spend_allocation` per run/campaign/spend date/method/signup month, `customer_age` per run/customer/age, `channel_cohort` per run/channel/month/age/method/model, `campaign_performance_day` per run/campaign/day |

## A2 · Relationships and physical keys

Use the two editable relationship panels in [the logical ERD](../exhibits/architecture/logical_erd.md) for the detailed visual. Mark effective identity matching and reporting joins separately from declared FKs.

| Relationship | How it is enforced or resolved |
|---|---|
| Registration → acquisition → attribution | `acquisition.registration_id VARCHAR` is a unique FK to `registration`. `attribution.customer_id VARCHAR` is PK/FK to `acquisition`. The identity claims that establish the customer are resolved in ELT. |
| Account → raw delivery → canonical activity | `product_activity_delivery.account_id VARCHAR` is an FK to `product_account`. `canonical_activity.delivery_id VARCHAR` references the chosen delivery. Account owner identity is resolved separately by time and canonical customer. |
| Canonical activity → signed event | `financial_event(run_id, source_key)` references canonical activity. PK is `(run_id, event_id)`. Signed cents use BIGINT, and effective and recorded clocks use TIMESTAMPTZ. |
| Feature → prediction → age | `prediction.customer_id` references `feature_snapshot`, `model_version` references `forecast_model`, and the prediction-age composite FK references the prediction. |

Source: frozen `src/schema.sql` and `docs/02_data_dictionary.md`.

## B1 · Recognition, costs and exclusions

| Product | Recognized revenue examples | Attributable cost examples |
|---|---|---|
| Savings | Treasury accrual and posted fees | Depositor interest and servicing |
| Debit | Settled interchange and posted fees | Processing, rewards, servicing and separately borne confirmed fraud |
| Credit card | Settled interchange, eligible accrued interest and posted fees | Processing, rewards, servicing, funding and confirmed charge-off less recoveries |
| Personal loan | Performing funded-principal interest and earned/posted fees | Funding, service, collection and confirmed charge-off less recoveries |
| Mortgage | Performing funded-principal interest and earned/posted fees | Funding, origination, servicing and confirmed charge-off less recoveries |

**Contribution = sum of signed revenue − sum of signed costs.** Round recognized components half-up to integer cents before summation. Deposits, purchase face values and loan funding or principal repayments do not become earnings. Acquisition spend is a separate ledger. Later economic refunds and recoveries use their own effective time. Restatements use the original event’s effective time and retain their distinct recorded time.

| Source-to-target extract | Implemented transformation |
|---|---|
| `product_activity_delivery` → `canonical_activity` | Group deliveries by source key. Keep one identical delivery and quarantine conflicting payloads. Resolve customer ownership. |
| `canonical_activity` → `financial_event` | Map product/activity codes to recognized revenue or cost and preserve source keys. Apply valid linked signed adjustments. |
| `financial_event` → `customer_age` | Sum available signed components in the exclusive customer-age window. |
| Signup, spend, ledger and forecast marts → BI | Aggregate separately before joining cohort grids. Daily campaign reporting keeps missing plans and pending activation visible. |

The controlled E029 fee correction points to E028. It reduces fee revenue by 50 cents, from 200 to 150 once visible, and retains E028’s original March 2 effective date. Sources: specification, mapping, SQL stages and D validation report.

## B2 · C02703 reconciliation extract

| Product | Components | Revenue | Cost | Net contribution |
|---|---:|---:|---:|---:|
| Savings | 151 | $17.25 | $9.29 | $7.96 |
| Debit | 11 | $4.15 | $3.73 | $0.42 |
| Credit | 133 | $51.35 | $20.33 | $31.02 |
| Personal loan | 98 | $135.44 | $46.10 | $89.34 |
| Mortgage | 86 | $1,140.48 | $947.51 | $192.97 |
| Total | 479 | $1,348.67 | $1,026.96 | $321.71 |

Source `core:E00457542` maps to its treasury revenue component of 21 cents. Source `core:E00457543` contributes 10 cents of depositor-interest cost. Source `core:E00457847` contributes 4,700 cents of fee revenue. The 90-day window runs from March 16, 2025, 13:00 UTC through June 14, 2025, 13:00 UTC exclusive. The customer enters the mature March unknown cohort. Sources: worked trace, summary and independent D exhibit.

## C1 · Forecast and matched-age methodology

For each product and age, multiply the frozen intent-conditioned activity probability by conditional first-year net contribution, the assigned channel multiplier and the cumulative age fraction. Sum unrounded product values, then round half-up to cents. Use signup-time intent and attributed channel available at signup. Preserve feature references and cutoff, model version and hash, score time and write time. A later-recorded feature cannot change the baseline.

| Product | P(EVERYDAY) / P(BORROW) / P(UNKNOWN) | Conditional net USD | 30/90/180/365-day fraction |
|---|---|---:|---|
| Savings | .55 / .25 / .35 | 18 | .07 / .22 / .47 / 1 |
| Debit | .65 / .30 / .45 | 24 | .06 / .23 / .48 / 1 |
| Credit | .30 / .45 / .30 | 65 | .03 / .17 / .43 / 1 |
| Personal | .05 / .25 / .10 | 90 | .01 / .10 / .38 / 1 |
| Mortgage | .01 / .06 / .02 | 180 | .00 / .05 / .25 / 1 |

Baseline Google / Meta / affiliates / unknown multipliers: 1.00 / .95 / .90 / 1.00. Equal-channel scenario: all 1.00 on the same snapshots. Checkpoints use [signup, signup + N UTC days). Maturity requires a complete observation window, with entire signup month elapsed for mature cohort comparisons. The recorded-time filter separately controls evidence availability.

## C2 · Attribution, allocation and scenario verification

| Convention | What to show |
|---|---|
| Attribution | Last eligible simulated tracked touch in [signup − 30 days, signup), recorded by signup. Unknown stays visible. Coverage = paid-attributed signups ÷ all canonical signups. |
| Spend allocation | Calendar groups spend by original spend month. Touch weighting splits by winning-touch signups, conserving cents. No-winner spend remains in the source month. |
| Allocation check | Both methods preserve $330,676.79. The independent sensitivity check found CAC ordering changes in six of 15 mature months and ROAS ordering in one. These counts demonstrate denominator sensitivity. |
| Forecast sensitivity | Identical customers, frozen features and spend. Removing multipliers adds $11,679.11 to summed day-365 predictions. The paid-channel mean spread changes from $5.52 to $0.41. The change follows from model assumptions. |
| Full visible ledger mix | The mortgage component contributes $888,044.36 of $926,076.41. This is a full-history synthetic arithmetic cross-check, with a separate window from the historical cohorts. |

For the supporting full cohort extract, show the selected 90-day baseline/calendar rows from the strategic wireframe. Include coverage, counts and metrics. Keep product concentration and cohort comparisons separately labeled. Sources: D sensitivity and reconciliation assets, strategy wireframe and forecast model.

## D1 · Independent expected versus observed

| Case evidence | Independent expected result | Observed |
|---|---|---|
| R1, T02, T03 · acquisition | T02 wins. T03 first becomes available after signup. | Matched |
| E004/E005 · recognized fee | E004 recorded once. E005 duplicate excluded. | Matched |
| E028/E029 · fee restatement | E028 revenue 200 cents before correction becomes available. Net 150 cents in the later snapshot, original effective time retained. | Matched |
| E036 · late fee | Excluded at primary recorded cutoff. Replay adds 125 cents to C1. | Matched |
| C5 · cutoff maturity | Realized fields remain pending/null. | Matched |

Primary effective cutoff is July 1, 2026, 00:00 UTC exclusive. Recorded cutoff is the same instant inclusive. Replay uses July 3 as its recorded cutoff. The two correction-only recorded cutoffs are March 11 and March 13, 2025, 00:00 UTC. All 329 original comparisons matched. The independent full-source reconciliation produced $926,076.41 contribution before acquisition spend and $330,676.79 eligible spend per allocation method.

## D2 · Operational regression and repeat run

Original cross-account probe: `E_D2_BAD_REFUND` on credit account C referenced the debit purchase on account D. Before correction it silently changed activation to `NO_QUALIFYING_EVENT`. Corrected C-1.0.1 logs `INVALID_REFERENCE` with `ACCOUNT_OR_CUSTOMER_MISMATCH`. The real 4,000-cent refund remains accepted against the 10,000-cent purchase, preserving 6,000 cents and qualified activation.

The expanded regressions cover cross-account, missing original, over-limit, cumulative cap, partial and full refunds, duplicate delivery, invalid chronology, conflicting payloads and unsettled original. All 10 passed. The full rerun matched 26 published output files byte for byte. The run manifest identifies the corrected build. Sources: original probe, regression fixture and observed results, independent audit and run manifest.

## E1 · Architectural tradeoffs and open requirements

| Choice | Evidence and boundary |
|---|---|
| Source-first ELT vs pre-load ETL | Retained deliveries support duplicate inspection, late availability and restatement replay. Production loading controls still need evaluation. |
| Canonical events vs product totals | Component source and adjustment keys explain the customer calculation and preserve economic time. Product rollups alone would hide this detail unless paired with source lineage. |
| Daily batch vs streaming | The local batch supports stated daily/weekly reporting and repeat runs. Streaming latency, uptime and cost were not tested. |
| Two clocks and fixed forecast | Cutoff cases support point-in-time history. Immutable signup forecast preserves the baseline during realized monitoring. |
| Prototype → production | Proposed live product feeds, MMP API attribution, approved campaign plans, warehouse SQL/dbt and BI. Live IDs, source quality, security, scaling and SLAs need validation. Expected-loss provisioning and deposit/funding reversals are outside tested scope. |

## F1 · Sources and readable evidence

- Assignment 1, *Marketing Budget Allocation for a Fintech Company*, slides 2–3. Cite as the alignment baseline.
- Official MIS 636 Assignment 2 instructions and the revised project executive summary.
- Team 3 Specification Freeze v1.0, source manifest, C-1.0.1 run manifest and signed D validation report.
- For each exhibit use the [slide evidence index](slide_evidence_map.md). Copy the selected table rows and diagrams into the PowerPoint. The deck should contain readable schema, source-row, dashboard and validation examples without private links or code execution.

## F2 · Team contributions and AI-use disclosure

| Member | Confirmed assignment-stage contribution and evidence |
|---|---|
| [Member 1 name] | [Confirm contribution and artifact] |
| [Member 2 name] | [Confirm contribution and artifact] |
| [Member 3 name] | [Confirm contribution and artifact] |
| [Member 4 name] | [Confirm contribution and artifact] |
| [Member 5 name] | [Confirm contribution and artifact] |

**Draft disclosure for team confirmation:** AI assisted with project planning, financial and schema specification drafts, synthetic-data and ELT implementation, validation material, and presentation drafting. Document the actual member review performed for each material area. The project’s verification artifacts include frozen specification comparisons, source-based recalculations, regression outputs and deterministic reruns. Confirm which AI suggestions the team adopted or revised and how member review verified the submitted claims. Do not attribute unconfirmed manual checks to any member.

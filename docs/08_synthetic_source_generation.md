# Workstream B · Stage 2 synthetic source extract

Specification v1.0 · Generator 1.0.0 · Default seed 6362025

The extract contains the nine source relations from the frozen DuckDB schema. Each relation has one gzip-compressed newline-delimited JSON file named after the table. Every row has the source columns from the data contract, including explicit nulls. Annual rates use exact decimal strings for ingestion into the declared DuckDB decimal types. Money is integer USD cents. The exception inventory and manifest are metadata alongside the nine relations.

## Generation assumptions

| Area | Synthetic rule |
|---|---|
| Coverage | Exactly 5,000 resolvable signup identities across 18 months, with two additional intake exceptions. Dates are sampled uniformly. No product activity precedes signup. Product activation and outcomes are generated independently of channel, conditional on submitted intent and the product simulation. |
| Campaigns | Two per channel. Primary touch weights for G1/G2/M1/M2/F1/F2 are 22/13/23/15/17/10. Touch lags vary from 0 to 19 calendar days, truncated at the start of the source period. Some earlier touches provide competing evidence. Daily plan baselines are 12000/8500/14500/9000/10000/7500 cents. Actual spend generally ranges from 70% to 130% of plan, independent of signups, with injected zero-spend and missing-plan days. |
| Customer mix | Submitted intents are sampled as EVERYDAY/BORROW/absent at 56%/29%/15%. A 12% segment bypasses all products. For others, per-product adoption probabilities in savings/debit/credit/personal/mortgage order are .39/.42/.26/.21/.065 for BORROW and .55/.58/.30/.10/.028 otherwise. Adoption lags vary and are censored at end of history, so realized ownership differs from these trial probabilities. These are generation parameters, separate from A's frozen LTV assumptions. |
| Savings | Customers make an external deposit and can make subsequent deposits. Daily interest bases are emitted for an active period of 45–105 days or until cutoff. Closing the balance spell uses a settled withdrawal where observed. Service costs and occasional account fees are posted separately. |
| Debit and credit | Debit has 1–5 purchase attempts per account before horizon truncation and a 17% refund trial per purchase. Card economics have separate interchange, processing and reward components. Credit simulates a revolving purchase balance for 35–95 days, with a 14% charge-off trial when the episode completes. Other completed episodes repay principal. Some charge-offs have partial recoveries. |
| Loans | Personal loan and mortgage funding, fee, cost and principal repayment inputs are distinct. Scheduled principal payments reduce future balance bases every 30 days. Their sizes vary by loan. Daily interest and funding bases extend until payoff or the reporting cutoff. Some fees carry a linked restatement. |
| Exceptions | A separate audit lists injected identity gaps and ambiguities, missing touches, delayed touches/features, late fees, re-deliveries and missing plans. Partial refunds, recoveries and fee restatements are valid source activity. They retain original source keys. |
| Contribution variation | Zero-product cases provide zero-activity evidence. Positive interest spreads and fee observations support positive contribution. Credit-only charge-off cases provide loss-heavy evidence with recoveries capped at a fraction of principal. Realized contribution and any channel ranking remain to be calculated by C and checked by D. |

No weights or post-generation filters enforce a preferred channel ranking. Synthetic APRs, costs and spending are classroom demonstration assumptions. No real company records or customer identifiers are used.

## Reproduce and verify

From the project root, use Python 3.11+ and DuckDB 2.0.1 for the recorded checks. The generator itself uses the Python standard library. Keep reproduction directories separate from the released extract.

```sh
python3 src/generate_data.py --output /tmp/mis636-sources-a --seed 6362025
python3 src/generate_data.py --output /tmp/mis636-sources-b --seed 6362025
python3 src/verify_synthetic_sources.py /tmp/mis636-sources-a /tmp/mis636-sources-b
```

Generation uses fixed ordering and gzip timestamps. The verifier compares all generated file hashes and the generation manifest contents, loads sources into frozen DuckDB DDL, applies source-level integrity checks, and annotates the first manifest with observed results. See [manifest v1.0](../data/synthetic_sources/manifest_v1.0.json) for the exact counts, checks, hashes and cutoff. The second manifest intentionally remains a raw generation record. Annotations do not alter any extract file.

## Handoff to Workstream C

1. Use [schema.sql](../src/schema.sql), the [frozen specification](07_specification_freeze_v1.0.md) and the [source-to-target mapping](02_source_target_mapping.md). Read only the nine named source extracts from `data/synthetic_sources/`. Confirm hashes against the manifest and use its source cutoffs in the run manifest. The primary cutoffs are exclusive effective and inclusive recorded at July 1, 2026 00:00 UTC. The late fee replay uses the same effective cutoff and July 4, 2026 00:00 UTC recorded cutoff.
2. Treat `expected_source_exceptions.json` as source QA metadata. Use the source keys to inspect exceptions. Keep incomplete plan coverage unavailable and retain spend-only rows. Derive marketing attribution and all analytical results under frozen v1.0. Apply confirmed realized-loss treatment and preserve frozen feature provenance and both model scenarios.
3. In a separate DuckDB input run, load the unchanged controlled fixture and compare C's observed outputs to D's independent JSON and v1.0 assertions. The full extract is separate from those cases. Do not substitute independent expected rows for pipeline outputs.

Source verification covers ingestion compatibility and structural integrity. Financial reconciliation, cohort computations, production forecast scores, and final validation remain pending.

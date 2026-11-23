# Controlled cases · source fixture only

Use [controlled_source.json](controlled_source.json), keyed by physical source table. Each array contains the source rows for that table. All amounts are integer USD cents. Numeric rate strings are exact decimals to cast using the contract types. Source keys in the inventory omit the core: prefix for readability. These rows are a hand-authored subset, so absent balances do not imply a complete daily coverage feed.

## Inputs and intended behavior

| Case | Source records | Rule exercised and intended behavior |
|---|---|---|
| B01 | R1, reg:1/web:v1 links, T01–T03 | Resolve canonical identity first. Choose latest eligible pre-registration touch using availability, even though a newer touch appears in a later recorded snapshot. Demonstrates February touch and March signup. |
| B02 | R4, R6–R8 and corresponding links, T08 | Keep a resolved customer with missing visitor link or ambiguous visitor mapping in unknown attribution. Unresolved signup identity is an exception and does not create a canonical acquisition. Distinguish missing from ambiguous links. |
| B03 | R5, T06–T07 | Touch at exactly t−30 days qualifies; touch at registration is excluded. R5 is too recent for a 30-day or longer outcome in the main reporting snapshot. |
| B04 | G 2025-02-26 and 2025-03-02, M 2025-03-01, F 2025-03-02 | Base spend stays in UTC calendar month. Touch-weighted spend follows observed winning-touch registrations, with no-winner spend retained in spend month. Include zero-registration dates. Reconcile both methods to eligible source spend. Review M budget plan and F missing plan. |
| B05 | S, s-dep, s-treas, s-depi, s-fee deliveries, s-service | Funded balance produces treasury revenue and interest cost. Recognize account fee once across duplicate deliveries and exclude the deposit from economics while checking savings activation. |
| B06 | D, d-purchase, d-int, d-process, d-reward, d-refund and linked reductions | Use interchange, processing and rewards. Partial refund reduces only referenced components and preserves positive net settled purchase activation. |
| B07 | C, c-purchase, c-it, c-interest, c-funding, c-loss, c-recovery | Recognize revolving interest and funding as separate components, confirmed charge-off as cost and recovery as a later reduction. Exclude purchase face value. Use confirmed realized-loss convention. |
| B08 | P, p-fund, p-interest, p-fundingcost, p-repayment, p-fee, p-correct | Activate on settled funding. Exclude disbursement and repaid principal from earnings. Apply fee restatement to original effective time when available. |
| B09 | H, h-fund, h-interest, h-fundingcost, h-repayment, h-fee, h-origination | Check separate interest, funding, earned fee and origination cost. Funding qualifies for activation and cash principal movements remain traceable outside ledger. |
| B10 | R1, R5, s-boundary-30/90/180/365, s-late | At each checkpoint, the event exactly at its exclusive upper bound enters only later horizons. Keep unmatured outcomes pending. Include late-recorded fee only in the later replay. |
| B11 | R1–R4, I1–I4, winning/unknown attribution | Freeze signup-time inputs. Intent recorded after signup falls back to UNKNOWN. Independently score all ages under baseline and equal-channel versions. Matched campaigns include the same intent on all three channels, so holding customers and costs fixed isolates the multiplier effect. |

## Run context for independent calculations

- Primary snapshot has exclusive effective cutoff 2026-07-01T00:00:00Z and inclusive recorded cutoff at the same instant. Later replay uses the same effective cutoff and recorded cutoff 2026-07-03T00:00:00Z.
- For the fee correction demonstration use two additional snapshots keeping the primary effective cutoff and changing recorded cutoff to 2025-03-11T00:00:00Z and 2025-03-13T00:00:00Z for the ledger trace only. These intentionally incomplete recorded snapshots do not establish cohort maturity.
- Resolve campaign spend from latest available source version. Compare CALENDAR and TOUCH_WEIGHT under the same source snapshot. For EQUAL_CHANNEL, hold scenario population, spend method and acquisition feature snapshot constant and change only the four multipliers to 1.00.
- D should return source keys, canonical event class and signed cents, per-account and customer reconciliation, checkpoint revenue/cost/contribution, mature counts, spend reconciliations and at least one meaningful channel-month CAC/ROAS comparison. Include expected nulls with reasons. Score baseline and sensitivity at four ages and show matched scenario deltas. Record formulas independently before implementation.

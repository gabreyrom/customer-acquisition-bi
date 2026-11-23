# MIS 636 Assignment 2 · Specification freeze v1.0

**Status:** Approved implementation baseline · November 23, 2026 · Team 3

This freezes the Workstream A v0.3 financial rules, Workstream B v0.4 schema design with the physical clarifications below, and Workstream D Stage 1 independent expectations for B01–B11. Reference v1.0 in the synthetic-source manifest and pipeline run manifests.

| Decision | Frozen rule |
|---|---|
| Savings fixture | DEP_SETTLED represents an external settled deposit in this controlled fixture. It is activation evidence subject to A's threshold and remains outside recognized earnings. No source record was changed. |
| Spend-only outputs | Preserve eligible spend and the zero-registration denominator. Store CAC and ROAS as null, display N/A, and retain the spend in reconciliations. |
| Allocation | CALENDAR uses original campaign spending month and null winner_count. TOUCH_WEIGHT uses winning-touch counts and retains no-winner spend in the original month. Both conserve eligible cents. |
| Budget plans | A missing or incomplete cumulative plan makes pacing unavailable. Preserve observed spend and available source plan rows without substituting zero for missing inputs. |
| Numeric representation | Exact BIGINT cents for money. Derived reporting values use DECIMAL(28,8), computed from exact numerator and denominator and rounded half-up once. Source rates remain DECIMAL(12,8). |
| Time | UTC, explicit exclusive effective cutoff and inclusive recorded cutoff, with half-open customer-age windows. Freeze forecasts using the original signup-time availability boundary. |
| Forecasts | Freeze published probabilities, net contribution values, trajectory fractions and baseline multipliers. Keep the all-1.00 case separate with the same feature snapshots and spend. |

## Baseline references and consistency

- [Financial rules and decision log](01_project_spec.md)
- [Physical data contract](02_data_contract.md), [dictionary](02_data_dictionary.md), [DDL](../src/schema.sql), and [source-to-target mapping](02_source_target_mapping.md)
- [Validation report and v1.0 assertion addendum](04_validation_report.md), [original source fixture](../data/validation_cases/controlled_source.json), and [independent expected values](../data/validation_cases/independent_expected.json)

The controlled source and independent JSON are preserved byte for byte. No established expected value changes. B04's historical UNRESOLVED_DISPLAY marker becomes a null ROAS assertion through the addendum, and its calendar winner_count was previously outside the assertions. B05's assumption is confirmed. The precision rule converts exact reference fractions to stored scale without changing those fractions. v1.0 DDL was executed in DuckDB, the 84 original source rows loaded successfully, and the revised columns and SQL checks were inspected. These are schema checks. The financial and analytical assertions still await an implemented pipeline.

## Next step

No implementation blockers remain. Start Workstream B full generation: implement a deterministic source-only generator for approximately 5,000 synthetic customers and all five financial products across January 2025–June 2026, using the v1.0 schema. Record the seed, assumptions, row counts, file hashes and cutoffs in a versioned source manifest. Verify source schema compatibility and reproducibility, preserving the controlled fixture and reference results as separate inputs. Workstream C implements ELT after the generated source extract is ready.

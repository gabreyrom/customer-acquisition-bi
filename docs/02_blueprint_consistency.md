# Workstream B blueprint consistency report

## Checks executed

- Executed src/schema.sql against a fresh in-memory DuckDB 2.0.1 database. All 24 tables were created.
- Inserted the 84 unchanged controlled source rows into the nine typed source tables and checked per-table counts. Checked that every cents column uses BIGINT. This tested physical schema compatibility only.
- Compared the financial specification, controlled fixture, case inventory, and original logical ER diagram byte-for-byte with the prior Workstream B package.

## Interface clarifications

| Interface | Blueprint treatment |
|---|---|
| Attribution status | MATCHED requires a campaign and touch and a paid channel. Unknown is the channel value, with the specific missing or ambiguous reason carried in status. |
| Ledger lineage | Same-run foreign keys preserve the canonical activity and original event references. C should insert original events before dependent adjustments and enforce adjustment chronology and caps in transformations. |
| Acquisition-time feature lineage | Frozen feature values and provenance use only effective, available evidence. A later observation may appear in diagnostics without changing the acquisition-time input or snapshot hash. |
| Sparse source fixture | Omitted spend, plan, balance and target observations remain absent. Treat the fixture as selected controlled source evidence. C must handle missing planned inputs and D should label unavailable metrics. |
| Reporting decimals | Freeze v1.0 widens derived reporting fields to DECIMAL(28,8). Source rates stay DECIMAL(12,8), and source and ledger cents remain exact BIGINT. |
| Relational versus temporal constraints | The physical DDL enforces row-level domains and keys. Time validity, model parity, exactly four checkpoints and reconciliation are cross-row transformation requirements. |

No fixture correction is required to start Workstream D. D can derive independent expected values immediately using the frozen inputs and A's rules. Reporting range and implementation-specific insertion order can be resolved before C. This check generated no expected outcomes and executed no ELT transformations.

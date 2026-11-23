# MIS 636 Assignment 2 — Customer Acquisition Value Intelligence

Draft v0.2 · Team 3 · Owner: project coordinator

Evaluate quarterly acquisition budgets and daily pacing or weekly campaign adjustments for a hypothetical digital bank. Compare acquisition cost, frozen first-year predicted contribution, and age-matched realized contribution. Use the submitted Assignment 1 slides as baseline, the revised executive summary for design intent, the orchestration prompt for agreed scope, and the official Assignment 2 instructions for assessment.

## Responsibilities and first handoffs

| Member | Owns | First handoff | Depends on |
|---|---|---|---|
| 1 / A | Financial rules and KPI specification | Signed event dictionary, KPI formulas and frozen LTV rules | Baseline and revised summary |
| 2 / B | Data contract and synthetic sources | Schemas, keys, field types, distributions and exception inventory | A definitions |
| 3 / C | Pipeline design, Python/SQL and marts | Dependency graph and source-to-mart mappings | A and B, D fixtures before implementation |
| 4 / D | Validation and architecture decisions | Independent hand calculations and expected results for agreed cases | A and B, then C outputs for execution |
| 5 / E | Reporting specification and exhibits | Exhibit inventory and decision-to-output mapping | A and B for design, C and D for evidence |

The [v1.0 specification freeze](docs/07_specification_freeze_v1.0.md) is the implementation baseline. A, B blueprint design and D Stage 1 are complete. B full synthetic-source generation is complete. See the [source generation report](docs/08_synthetic_source_generation.md) and [verified extract manifest](data/synthetic_sources/manifest_v1.0.json) for the Workstream C handoff. Then proceed **A → B (schema and controlled cases) → D (independent fixtures) → specification freeze → B (full generation) → C → D (execute checks) → E**. E uses checked outputs for final claims.

1. **Specification freeze** — Confirm recognition, measurement and source contracts, and approve independent expected cases before generation or implementation.
2. **Integration freeze** — Rerun Python and DuckDB SQL from clean synthetic inputs and verify stable outputs. C will provide exact commands and dependencies.
3. **Evidence freeze** — Sign off on observed test results, exhibits and design claims. Preserve the run configuration, data snapshot, outputs and validation results for Assignment 3.

Record date, owner, rationale and downstream effects when revising shared definitions or schemas. Keep source records in data/synthetic_sources, independent fixtures in data/validation_cases and marts in data/analytical_outputs. Use src for implementation, tests for validation and exhibits for deck assets. See presentation/README.md for the submission evidence checklist.

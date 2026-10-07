# Stage handoffs

Handoff notes between the sequential stages of [plan.md](plan.md) (**proposed, D16**). The required deliverables and acceptance checks are defined in [plan.md — Handoffs](plan.md#handoffs); this file holds the filled-in notes.

Rules:
- Fill a field only with values that were actually run or observed, and link the evidence-log row. Anything not verified stays "not run" or is listed under remaining assumptions.
- **Git shares code, not tables.** Every note gives the commands that rebuild the tables, so the receiver can recreate them in their own workspace or prefix (plan.md D17).
- The receiver records the acceptance result ("H1 accepted" / "H2 accepted", or a defect list) in the plan.md evidence log. The sender fixes reported defects.

---

## H1 — Nazar → Yaropolk (NAZ-21)

Status: **not started**

| Field | Value |
|---|---|
| Commit SHA on `main` | – |
| Workspace path (D17: shared or separate) | – |
| `catalog` / `schema_prefix` / `source` used | – |
| Bronze tables and column lists (8 tables + `_ingested_at`, `_source_table`) | – |
| Evidence-log rows: P0 (NAZ-01–04), inventory and `DESCRIBE` (NAZ-02), Bronze run (NAZ-08), profiling (NAZ-09) | – |
| Allowed-list constants and the documentation they were cross-checked against | – |
| Observed vs documented-only values, and discrepancies resolved under D13 | – |
| Observed `o_orderpriority` values and the confirmed urgent literal | – |
| Commands that run Stage 1 (widgets, notebooks, order) | – |
| run_id helpers (`new_run_id()`, `require_run_id()`) and the test that covered them | – |
| `[VERIFY]` / `[PROFILE]` items resolved by Stage 1 | – |
| Remaining assumptions | – |
| README sections (NAZ-15) | – |
| Slide material location (NAZ-17) | – |
| Repo visibility (checked from a logged-out browser) | – |

Acceptance (A1–A6, run by Yaropolk): **not run**

---

## H2 — Yaropolk → Max (YAR-13)

Status: **not started**

| Field | Value |
|---|---|
| Commit SHA on `main` | – |
| Workspace path (D17) and values used | – |
| Final Silver contract (design §5.1, any §5.4 decomposition and its decision-log entry) | – |
| Silver stage execution sequence (design §3.1) | – |
| Final `dq_helpers` signatures | – |
| Rule IDs written by `03_validate` | – |
| Success run: `run_id` and evidence-log row | – |
| Failure demo (YAR-08): evidence-log row | – |
| Constraint evidence (YAR-06), ER image (YAR-07), 3NF results (YAR-03) | – |
| Remaining assumptions | – |
| README validation section (YAR-10) | – |
| Slide material location (YAR-11) | – |

Acceptance (B1–B5, run by Max): **not run**

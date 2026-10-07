# Stage handoffs

Handoff notes between the sequential stages of [plan.md](plan.md) (D16, agreed 2026-10-07). The required deliverables and acceptance checks are defined in [plan.md — Handoffs](plan.md#handoffs); this file holds the filled-in notes.

Rules:
- Fill a field only with values that were actually run or observed, and link the evidence-log row. Anything not verified stays "not run" or is listed under remaining assumptions.
- **Git shares code, not tables.** Every note gives the commands that rebuild the tables, so the receiver can recreate them in their own workspace or prefix (plan.md D17).
- The receiver records the acceptance result ("H1 accepted" / "H2 accepted", or a defect list) in the plan.md evidence log. The sender fixes reported defects.

---

## H1 — Nazar → Yaropolk (NAZ-21)

Status: **ready for Yaropolk's review (2026-10-07).** Stage 1 is pushed on `docs/initial-plan` with an open PR into `main`. H1 is accepted only when Yaropolk records it.

| Field | Value |
|---|---|
| Commit SHA on `main` | Not merged yet. Implementation commit on `docs/initial-plan`: `2d18564587078cae019abcab18cbb69c6bd2ae17`. The `main` SHA is added after the squash merge |
| Workspace path (D17: shared or separate) | D17 is open (no arrangement confirmed), so both paths apply. **Separate workspace:** run the Stage 1 commands below with your own `catalog`. **Shared workspace (Nazar's):** Bronze exists in `workspace.nachalniki_logistics_bronze`, loaded at `_ingested_at = 2026-10-07 13:43:28.462558` UTC by run `1104358970299952`. That run executed the uploaded copy in `/Users/<nazar>/nachalniki_stage1/`, before the allowed lists were filled in `00_config`. The currently deployed notebooks are identical to commit `2d18564` (evidence row "Deployed notebooks vs repo"), but which exact version each earlier run executed cannot be shown, so that runtime evidence belongs to the uploaded version. Read grants for other users were not checked **[VERIFY]** |
| `catalog` / `schema_prefix` / `source` used | `workspace` / `nachalniki_logistics` / `samples.tpch` (widget defaults) |
| Bronze tables and column lists (8 tables + `_ingested_at`, `_source_table`) | `region`, `nation`, `supplier`, `customer`, `part`, `partsupp`, `orders`, `lineitem`. Each has exactly the source columns in source order and type (61 in total, listed in [06_describe_tables.csv](../checks/p0/outputs/source_discovery/06_describe_tables.csv)), then `_ingested_at` (timestamp, one value per execution) and `_source_table` (string, e.g. `samples.tpch.lineitem`) |
| Evidence-log rows: P0 (NAZ-01–04), inventory and `DESCRIBE` (NAZ-02), Bronze run (NAZ-08), profiling (NAZ-09) | [evidence log](plan.md#evidence-log): NAZ-01, NAZ-02, NAZ-03 runs 1–2, NAZ-04 (Git folder, 1–4), Stage 1 setup, NAZ-07 A1 + A5, NAZ-07 A5 (child without caller), NAZ-07 A4, NAZ-08, NAZ-09, NAZ-10, deployed notebooks vs repo, H1 implementer self-check (all 2026-10-07). Raw outputs in `checks/p0/outputs/` and `checks/p2/outputs/` |
| Allowed-list constants and the documentation they were cross-checked against | `ALLOWED_SHIP_MODES = ["AIR", "FOB", "MAIL", "RAIL", "REG AIR", "SHIP", "TRUCK"]`, `ALLOWED_RETURN_FLAGS = ["A", "N", "R"]`, `ALLOWED_LINE_STATUSES = ["F", "O"]`. Checked against the TPC-H Standard Specification rev. 3.0.1, clause 4.2.2.13 ("Modes") and clause 4.2.3 (`L_RETURNFLAG`, `L_LINESTATUS` rules) |
| Observed vs documented-only values, and discrepancies resolved under D13 | Every value was observed and documented; no value is documented only, and none is observed only. No NULLs, value lengths as expected (no whitespace). No discrepancy, so there is no decision-log entry (design §6) |
| Observed `o_orderpriority` values and the confirmed urgent literal | `1-URGENT` 1501100, `2-HIGH` 1499192, `3-MEDIUM` 1498710, `4-NOT SPECIFIED` 1501281, `5-LOW` 1499717. Urgent literal: `1-URGENT` (design §5.5, §7) |
| Commands that run Stage 1 (widgets, notebooks, order) | Put `notebooks/` in one workspace folder (a Git folder, or `databricks workspace import … --format SOURCE --language PYTHON`). Run `01_bronze_ingest`, then `profile_source`, with widgets `catalog`, `schema_prefix`, `source`. The runs above were serverless `databricks jobs submit` one-time jobs with default widgets (README "Configuration, Bronze and profiling"). Stage 1 was not run from a Git folder of this repo |
| run_id helpers (`new_run_id()`, `require_run_id()`) and the test that covered them | `new_run_id()` returns `str(uuid.uuid4())`. `require_run_id()` returns the caller's `run_id` or raises `RuntimeError`. `00_config` never assigns `run_id`. Test notebooks `checks/p2/run_id_helpers/a5_entry.py` and `a5_child.py`: in **one** notebook context, two executions got different ids, each read unchanged by the `%run` child, and a second `%run 00_config` did not change `run_id`; the child run alone failed. Serverless job runs only. **The interactive-session run is pending**: `a5_interactive.py` (Run all twice in one attached session) is imported in Nazar's workspace and has not been run |
| `[VERIFY]` / `[PROFILE]` items resolved by Stage 1 | Resolved: catalog and write access (D8), source types, `%run` behaviour, CHECK/PK DDL, `percentile_cont`, allowed values, urgent literal, date ranges, lines per order (design §10) |
| Remaining assumptions | (1) D4, D9, D13, D15, D16 are agreed as reported by Nazar on 2026-10-07; no individual replies or PR approvals are recorded. D17 is open. (2) The run_id helpers are tested on serverless job runs; the interactive run is pending (NAZ-07). (3) Bronze was loaded once; a rerun was not part of Stage 1. (4) The Bronze and profiling runtime evidence belongs to the uploaded workspace copy, which matches the commit now but has no revision history. (5) The FD candidates, FK DDL and the ER rendering stay with Stage 2. (6) A widget value typed in the notebook UI was not tested (job parameters were, NAZ-04). (7) The due date and submission method were not provided (D18, MAX-17) |
| README sections (NAZ-15) | README "Setup" and "Configuration, Bronze and profiling" |
| Slide material location (NAZ-17) | `docs/slides/nazar.md` (2 slides with speaker notes), images in `docs/slides/img/` rendered from the run exports. The deck location is not decided (D18) |
| Repo visibility (checked from a logged-out browser) | Public: headless Chrome with a fresh, logged-out profile shows the "Public" label on 2026-10-07 ([screenshot](../checks/p2/outputs/repo_visibility/github_logged_out_20261007.png)); unauthenticated API: `"visibility": "public"` |

Implementer self-check (Nazar, 2026-10-07, from existing evidence; **not** the receiver's acceptance): A1 passed, A2 passed, A3 passed, A4 passed (grep repeated locally), A5 passed on serverless job runs with the interactive run pending, A6 listed above. Details: plan.md evidence row "H1 implementer self-check".

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

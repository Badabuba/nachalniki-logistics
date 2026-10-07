# Implementation plan

Living document. Update checkboxes **only with evidence**: a link, a screenshot path or pasted output, plus the date. Requirements: [requirements.md](requirements.md). Design and contracts: [design.md](design.md).

## Team and ownership (provisional mapping, agreed by swapping names here only)

| Member | Name | Area |
|---|---|---|
| M1 | Nazar | Repo, uv and config; Databricks access checks; Bronze; source profiling (categorical values, date ranges, lines per order); `run_pipeline` and `pipeline_runs`; integration, rerun and portability runs; README; presentation assembly |
| M2 | Yaropolk | Silver staging and publish; FD profiling and the 3NF analysis; `03_validate` and `dq_check_results`; constraints; ER diagram and screenshot; the validation part of the demo |
| M3 | Max | Gold tables; Q1–Q4 analysis and notebook charts; delay-rate monitoring series; written answers for the README and slides |

Balance rationale: Bronze is small, so M1 also owns profiling, orchestration, the run-state guard and the cross-cutting docs. M2 owns the most rules. M3 owns the most queries and charts. **Optional items are not assigned** (see "Optional follow-ups").

## Workflow

- Branch per task from `main`: `feat/<area>-<short>`, e.g. `feat/bronze-ingest`, `feat/silver-validate`, `feat/gold-q1`.
- Open a PR into `main`. At least one other member reviews it, then squash-merge. Keep PRs small, at one notebook or doc section each.
- A PR that changes a **frozen contract** (design §5.1 frozen columns, §7 metrics, §9 Gold columns, config parameters) must update `design.md` in the same PR, add a decision-log entry, and be approved by **both** other members.
- Notebooks are edited in a Databricks Git folder (or locally) and committed as `.py` source-format files.

## Phases

### P0 — Access and source checks (all; blocks everything)

Run in a Databricks notebook. Paste the outputs into the evidence log. Never store tokens or credentials in the repo.

- [ ] Each member can log in to the workspace (Free Edition or the one the course provides).
- [ ] `SHOW CATALOGS;` and `SELECT current_catalog();`. Record which catalog is writable. Do not assume `workspace` exists.
- [ ] `SHOW TABLES IN samples.tpch;` lists 8 tables.
- [ ] `SELECT count(*)` for each of the 8 tables. Record the counts (the code itself will not hard-code them).
- [ ] `DESCRIBE samples.tpch.<table>` for all 8. Record the column names and types in design §5.5, and fix types in design §5.1/§5.2 if needed.
- [ ] **Safe write check** in the chosen catalog `<cat>`:
  1. Pick a unique name, e.g. `nachalniki_access_check_<yyyymmdd_hhmmss>_<4 random chars>`.
  2. Run `SHOW SCHEMAS IN <cat> LIKE '<name>'` and expect no rows. If a row comes back, choose another name. Never reuse an existing schema.
  3. `CREATE SCHEMA <cat>.<name>`, **without** `IF NOT EXISTS`, so the step fails instead of adopting an existing schema.
  4. `CREATE TABLE <cat>.<name>.t (a INT NOT NULL, b INT)`, then `ALTER TABLE … ADD CONSTRAINT b_chk CHECK (b >= a)`. Confirm that `INSERT … VALUES (2, 1)` is rejected and `(1, 2)` is accepted.
  5. Declare an informational PK: `ALTER TABLE … ADD CONSTRAINT t_pk PRIMARY KEY (a)` (needs `a NOT NULL`).
  6. Run `SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY a) FROM <cat>.<name>.t`.
  7. Clean up **only what this check created**: `DROP TABLE <cat>.<name>.t`, then `DROP SCHEMA <cat>.<name>` (no `CASCADE`).
- [ ] Create a Git folder from the GitHub repo. Confirm that a notebook can `%run ./00_config` (use a 2-line test notebook on a scratch branch) and that an exception in a `%run` notebook stops the caller.
- [ ] *Optional aid, not a blocker:* read `/dbfs/databricks-datasets/tpch/README.md`. If DBFS FUSE is blocked, try `dbutils.fs.head("dbfs:/databricks-datasets/tpch/README.md")`. If both fail, use the TPC-H specification instead and note that in the log.

Acceptance: all non-optional boxes ticked with outputs in the evidence log. The catalog decision is recorded as D8.

### P1 — Contract sign-off gate (all; blocks parallel work)

Agree on, and record in the decision log:
- [ ] Config parameters and schema names (design §2).
- [ ] Pipeline lifecycle and failure behaviour (design §3): staging → validate → publish, append-only audit, and the stale-output guard.
- [ ] Silver frozen columns for `orders` and `lineitem`, and the Gold column contracts (design §5.1, §9).
- [ ] Metric definitions (design §7): transit, on time (`<=`), fully on time, denominators, `percentile_cont`, predictability = p90 − p50, urgent literal, order-to-receipt as the primary Q4 measure.
- [ ] Monitoring grain = commit month, with boundary months labelled (design §8).
- [ ] The allowed-list procedure (design §6) and the 3NF method (design §5.3, §5.4).

Acceptance: decision-log entries D9–D14 are marked "agreed" with all three names.

### P2 — Parallel build (after P1)

M3 can develop Gold against a temporary Silver built from `samples.tpch` with the frozen columns, because the contract is fixed. M3 switches to the real Silver in P3.

**M1**
- [ ] `pyproject.toml`, `uv.lock` and `.gitignore` (done locally on 2026-10-07, see the evidence log; review in a PR).
- [ ] `notebooks/00_config.py`: widgets, derived schema names, the allowed-value constants (filled in from profiling), and a `run_id` generator.
  Acceptance: no other notebook contains a catalog or schema literal.
- [ ] `notebooks/profile_source.py`: categorical value counts, `o_orderpriority` values, date min/max, and the lines-per-order distribution. Results go in design §5.5.
  Acceptance: the §5.5 rows owned by M1 are filled with dated outputs.
- [ ] `notebooks/01_bronze_ingest.py`: 8 tables plus 2 metadata columns, `CREATE OR REPLACE`.
  Acceptance: Bronze columns equal source columns + 2 metadata columns, and counts are equal.
- [ ] `notebooks/run_pipeline.py`: writes the `started` row, runs `%run` of 01–05, then writes the `succeeded` row. Creates the `{prefix}_audit` tables if they are missing (append-only).
  Acceptance: a forced failure leaves no `succeeded` row.

**M2**
- [ ] FD candidate tests and candidate-key checks (design §5.3) in `profile_source` or a separate section. Classify each candidate, and apply the §5.4 decomposition only if a real violation is confirmed (decision-log entry).
  Acceptance: design §5.3/§5.5 filled in with queries, outputs and conclusions.
- [ ] `notebooks/02_silver_stage.py`: Bronze → `{prefix}_staging.stg_*`, with casts and column selection only, and no row filtering.
  Acceptance: staging counts equal Bronze counts.
- [ ] `notebooks/03_validate.py`: all rules DQ-L1–L9 and DQ-G1–G3, appended to `{prefix}_audit.dq_check_results`. Raises if any rule is blocking and failed.
  Acceptance: a run on clean data gives all `passed = true`. A demo on an injected bad row in a *scratch prefix* shows the failure and that Silver is not published.
- [ ] `notebooks/04_silver_publish.py`: staging → Silver, then NOT NULL/CHECK and informational PK/FK.
  Acceptance: `SHOW TBLPROPERTIES` or `DESCRIBE TABLE EXTENDED` shows the constraints.
- [ ] ER diagram: render it from the final Silver (Mermaid in design §5.2 updated, or Catalog Explorer) and save the image to `docs/`.

**M3**
- [ ] `notebooks/05_gold_build.py`: the 8 Gold tables from design §9, plus DQ-GOLD1 and DQ-GOLD2 appended to `dq_check_results` (raises on failure).
  Acceptance: DQ-GOLD rows pass, and the columns match design §9 exactly.
- [ ] `notebooks/06_analysis.py`: a run-state guard (stop if the latest run is not `succeeded`), Q1–Q4 queries on Gold only, charts 1–5 (design §9), and answer text cells that reference the displayed numbers.
  Acceptance: every answer cites a displayed query result. Nothing is typed from memory.

### P3 — Integration and real execution (M1 leads, all verify)

- [ ] Full `run_pipeline` with the default prefix. The `pipeline_runs` row shows `succeeded`.
- [ ] Rerun on unchanged data: Gold business rows are identical (snapshot to scratch, `EXCEPT ALL` both ways = 0 rows). `_ingested_at`, `run_id` and the audit history differ, as expected.
- [ ] Portability: run with `schema_prefix = nachalniki_logistics_porttest`. Gold equals the default run (`EXCEPT ALL` = 0). Then drop **only** the `porttest` schemas this test created.
- [ ] Failure demo: with a scratch prefix, inject one bad row (e.g., receipt before ship) into the staging path. Show the DQ failure, Silver/Gold unchanged, and `06_analysis` refusing to present stale results.
- [ ] A second member reproduces the run from the README instructions alone.

### P4 — Analysis and monitoring (M3 leads)

- [ ] Q1–Q4 answers written in the README "Results" section with actual numbers and the date of the run they came from.
- [ ] Monthly delay-rate chart with boundary months labelled. Any other low-count edge months are named from the observed counts.
- [ ] M1 and M2 review the numbers against the Gold tables.

### P5 — README, ER, presentation (M1 assembles; all contribute)

- [ ] README complete: setup, run, the validation approach (including how the allowed lists were derived), results, the ER image, and the presentation link.
- [ ] Deck covers R-P1 to R-P7 (requirements §2.2): responsibilities, repo link, challenges (from the decision log), demo, ER screenshot, answers with code and charts.
- [ ] Demo script written below. Timed rehearsal of 5–7 minutes, with the time recorded.
- [ ] Repository visibility is public (checked from a logged-out browser).
- [ ] Submit before the course due date (**date unknown; get it from the course**).

## Optional follow-ups (not acceptance gates; unassigned)

- SQL alert or dashboard tile for a delay-rate increase (R-L-A1).
- An AI/BI dashboard mirroring the notebook charts.
- A Databricks Job chaining 01→05 (instead of `run_pipeline`).
- A rigorous complete-period rule for monthly monitoring.

## Demo script (draft — finalize in P5)

1. Show the repo README and config parameters (30 s).
2. Run, or show the last run of, `run_pipeline`. Show `pipeline_runs` and `dq_check_results` (1 min).
3. Show the failure demo: a bad row stops publish (1 min).
4. Show the Silver ER diagram (30 s).
5. Walk through charts Q1–Q4 and monitoring with the answers (2–3 min).

## Evidence log

| Date | Item | Evidence | By |
|---|---|---|---|
| 2026-10-07 | `uv lock` and `uv sync` succeeded locally (Windows, uv 0.12.21, CPython 3.13.5): "Resolved 1 package", `.venv` created; `uv.lock` generated (no dependencies) | local terminal output; `uv.lock` in working tree | Claude Code session for Nazar |
| – | Nothing has been executed in Databricks yet | – | – |

## Decision log

| ID | Date | Decision | Status |
|---|---|---|---|
| D1 | 2026-10-07 | Workspace: Databricks Free Edition or not yet known, so everything is parameterised | decided (Nazar) |
| D2 | 2026-10-07 | All 8 TPC-H tables in Bronze and Silver; Gold covers Logistics only | decided (Nazar) |
| D3 | 2026-10-07 | PySpark/SQL notebooks in `.py` source format; no Lakeflow, bundles or CI | decided (Nazar) |
| D4 | 2026-10-07 | Member mapping M1 Nazar, M2 Yaropolk, M3 Max | provisional |
| D5 | 2026-10-07 | Notebook charts satisfy the visualisation and monitoring requirements; dashboard, Job and alert are optional | proposed |
| D6 | 2026-10-07 | Silver keeps TPC-H column names; Gold uses business names | proposed |
| D7 | 2026-10-07 | Lifecycle: Bronze → staging → validate (append DQ) → publish Silver → Gold; failed run leaves outputs flagged as stale via `pipeline_runs` | proposed |
| D8 | – | Catalog to use (from P0) | open |
| D9 | – | Config and schema names (design §2) | open (P1) |
| D10 | – | Silver frozen columns and Gold contracts | open (P1) |
| D11 | – | Metric definitions (design §7) | open (P1) |
| D12 | – | Monitoring grain: commit month, with boundary months labelled | open (P1) |
| D13 | – | Allowed-list procedure | open (P1) |
| D14 | – | 3NF method; any decomposition after profiling | open (P1, P2) |

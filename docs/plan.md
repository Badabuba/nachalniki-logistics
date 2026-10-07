# Implementation plan

Living document. Requirements: [requirements.md](requirements.md). Design and contracts: [design.md](design.md).

**How to use this plan**
- Every task has one ID (`NAZ-nn`, `YAR-nn`, `MAX-nn`) and one primary owner: the person whose section it is in. Others review and help, but the owner makes sure it gets done.
- **Checkboxes exist only in [Tasks by person](#tasks-by-person).** The phase sections and the "start now" table only reference task IDs, so there is one checklist and no conflicting copies.
- Tick a box **only with evidence**: add a row to the [evidence log](#evidence-log) (output, screenshot path or link, plus the date), then tick the box in the same PR.
- `D<n>` means an entry in the [decision log](#decision-log).

## Team and ownership

| Name | Alias in requirements.md | Area |
|---|---|---|
| Nazar | M1 | Repo, uv and config; Databricks access checks; source value profiling (categorical values, date ranges, lines per order); Bronze; `run_pipeline` and `pipeline_runs`; integration, rerun and portability runs; README setup/run sections; presentation assembly and submission |
| Yaropolk | M2 | Silver staging and publish; FD profiling and the 3NF analysis; `03_validate` and `dq_check_results`; constraints; ER diagram; README validation section; the validation part of the demo |
| Max | M3 | Gold tables; Q1–Q4 analysis and notebook charts; delay-rate monitoring; README results section; business-answer slides |

Balance rationale: Bronze is small, so Nazar also owns profiling, orchestration, the run-state plumbing and the cross-cutting docs. Yaropolk owns the most rules. Max owns the most queries and charts. Each person writes the README section and slides for their own area. **Optional items are not assigned** (see [Optional follow-ups](#optional-follow-ups-not-acceptance-gates-unassigned)).

## Workflow

- Branch per task from `main`: `feat/<area>-<short>`, e.g. `feat/bronze-ingest`, `feat/silver-validate`, `feat/gold-q1`. Put the task ID in the PR title, e.g. `NAZ-08: Add Bronze ingest`.
- Open a PR into `main`. At least one other member reviews it, then squash-merge. Keep PRs small, at one notebook or doc section each.
- A PR that changes a **frozen contract** (design §5.1 frozen columns, §7 metrics, §9 Gold columns, config parameters) must update `design.md` in the same PR, add a decision-log entry, and be approved by **both** other members.
- Notebooks are edited in a Databricks Git folder (or locally) and committed as `.py` source-format files.
- Never store tokens or credentials in the repo.

## Start here: what each person can do now

Nothing has run in Databricks yet, so almost everything waits on Nazar's P0 access checks. These tasks have no unmet dependencies today:

| Person | Can start now | Waits for |
|---|---|---|
| Nazar | NAZ-01 (log in, catalogs), NAZ-05 for D4 only, NAZ-06 (uv PR), NAZ-16 (get the due date) | NAZ-02/03/04 wait for NAZ-01. Everything in P2 waits for D9 (needs NAZ-03). |
| Yaropolk | YAR-01 (log in), YAR-02 (drive D13 and D14) | YAR-03 and YAR-04 wait for Bronze (NAZ-08). YAR-04 also needs D10. |
| Max | MAX-01 (log in), MAX-02 for D5, D11 and D12 | D6 and D10 wait for the `DESCRIBE` output (NAZ-02). MAX-03 waits for config (NAZ-07) and D10/D11. |

Critical path: NAZ-01 → NAZ-03 (D8 catalog) → NAZ-05 (D9 config) → NAZ-07 (`00_config`) → NAZ-08 (Bronze) → YAR-04 → YAR-05 → YAR-06 → NAZ-12 (full run) → MAX-07 (answers) → P5.

## Phases

Phases group the tasks in time. The checkboxes are in [Tasks by person](#tasks-by-person).

### P0 — Access and source checks (blocks all Databricks work)

| ID | Owner | Task |
|---|---|---|
| NAZ-01 | Nazar | Log in; list catalogs |
| YAR-01 | Yaropolk | Log in; read `samples.tpch` |
| MAX-01 | Max | Log in; read `samples.tpch` |
| NAZ-02 | Nazar | Source inventory: tables, counts, `DESCRIBE` |
| NAZ-03 | Nazar | Safe write check; decide the catalog (D8) |
| NAZ-04 | Nazar | Git folder and `%run` behaviour |

Acceptance: all six tasks ticked with evidence, and D8 is decided.

### P1 — Contract sign-off (each decision blocks the tasks that list it)

| ID | Owner | Decisions driven |
|---|---|---|
| NAZ-05 | Nazar | D4 member mapping, D7 lifecycle (design §3), D9 config and schema names (design §2) |
| YAR-02 | Yaropolk | D13 allowed-list procedure (design §6), D14 3NF method (design §5.3, §5.4) |
| MAX-02 | Max | D5 notebook charts as the visualisation, D6 naming, D10 Silver frozen columns and Gold contracts (design §5.1, §9), D11 metric definitions (design §7), D12 monitoring grain (design §8) |

The owner drives the discussion and records the result. Every decision needs all three names. Decisions that do not depend on P0 output can be agreed before P0 finishes (see each task's dependencies).

Acceptance: D4–D7 and D9–D14 marked "agreed" with all three names and a date.

### P2 — Parallel build (after the P1 decisions each task depends on)

| ID | Owner | Task |
|---|---|---|
| NAZ-06 | Nazar | uv files reviewed and merged |
| NAZ-07 | Nazar | `00_config` |
| NAZ-08 | Nazar | `01_bronze_ingest` |
| NAZ-09 | Nazar | `profile_source`: value profiling |
| NAZ-10 | Nazar | Allowed-list constants in `00_config` |
| NAZ-11 | Nazar | `run_pipeline` and audit tables |
| YAR-03 | Yaropolk | FD and candidate-key tests (3NF evidence) |
| YAR-04 | Yaropolk | `02_silver_stage` |
| YAR-05 | Yaropolk | `03_validate` |
| YAR-06 | Yaropolk | `04_silver_publish` |
| YAR-07 | Yaropolk | ER diagram |
| MAX-03 | Max | `05_gold_build` |
| MAX-04 | Max | `06_analysis`: guard, Q1–Q4, charts 1–4 |

Max can develop Gold against a temporary Silver in a scratch prefix, built from `samples.tpch` with the frozen columns, because the contract is fixed in D10. Max switches to the real Silver in P3.

Acceptance: all P2 tasks ticked.

### P3 — Integration and real execution (Nazar leads, all verify)

| ID | Owner | Task |
|---|---|---|
| NAZ-12 | Nazar | Full run with the default prefix |
| NAZ-13 | Nazar | Rerun determinism check |
| NAZ-14 | Nazar | Portability run |
| NAZ-15 | Nazar | README setup and run sections |
| YAR-08 | Yaropolk | End-to-end failure demo |
| MAX-05 | Max | Reproduce the run from the README alone |

Acceptance: all P3 tasks ticked.

### P4 — Analysis and monitoring (Max leads)

| ID | Owner | Task |
|---|---|---|
| MAX-06 | Max | Monthly delay-rate chart (chart 5) |
| MAX-07 | Max | Q1–Q4 answers in the README "Results" section |
| YAR-09 | Yaropolk | Review the answer numbers against Gold |

Acceptance: all P4 tasks ticked.

### P5 — README, presentation and submission (Nazar assembles, all contribute)

| ID | Owner | Task |
|---|---|---|
| NAZ-16 | Nazar | Get the due date and presentation format |
| YAR-10 | Yaropolk | README validation section |
| YAR-11 | Yaropolk | Validation, 3NF and ER slides |
| MAX-08 | Max | Q1–Q4 and monitoring slides |
| NAZ-17 | Nazar | Team, repo, pipeline and challenges slides |
| NAZ-18 | Nazar | Final README assembly |
| NAZ-19 | Nazar | Deck assembly, demo script and timed rehearsal |
| NAZ-20 | Nazar | Public repo check and submission |

Acceptance: all P5 tasks ticked; the deck covers R-P1 to R-P7 (requirements §2.2).

## Tasks by person

Each task lists: **Files** (to create or edit), **Depends on** (what must be ready first) and **Done when** (the completion criterion). A dependency on `D<n>` means that decision is marked "agreed".

### Nazar

- [ ] **NAZ-01 · P0 · Log in and list catalogs.** Run `SHOW CATALOGS;` and `SELECT current_catalog();`. Do not assume `workspace` exists.
  - Files: `docs/plan.md` (evidence log)
  - Depends on: nothing. **Start now.**
  - Done when: both outputs are in the evidence log, and a candidate writable catalog is named for NAZ-03.

- [ ] **NAZ-02 · P0 · Source inventory.** `SHOW TABLES IN samples.tpch;` (expect 8 tables), `SELECT count(*)` for each table, and `DESCRIBE samples.tpch.<table>` for all 8. Record the counts for reference only: code never hard-codes them.
  - Files: `docs/plan.md` (evidence log); `docs/design.md` §5.5 (`DESCRIBE` row) and §5.1/§5.2 (fix types if they differ)
  - Depends on: NAZ-01
  - Done when: the 8 tables, counts and `DESCRIBE` outputs are in the evidence log with a date, and design §5.1/§5.2 types match `DESCRIBE`.
  - Optional aid, not part of "done": read `/dbfs/databricks-datasets/tpch/README.md`. If DBFS FUSE is blocked, try `dbutils.fs.head("dbfs:/databricks-datasets/tpch/README.md")`. If both fail, use the TPC-H specification and note that in the evidence log.

- [ ] **NAZ-03 · P0 · Safe write check and catalog decision.** In the candidate catalog `<cat>`:
  1. Pick a unique name, e.g. `nachalniki_access_check_<yyyymmdd_hhmmss>_<4 random chars>`.
  2. Run `SHOW SCHEMAS IN <cat> LIKE '<name>'` and expect no rows. If a row comes back, choose another name. Never reuse an existing schema.
  3. `CREATE SCHEMA <cat>.<name>`, **without** `IF NOT EXISTS`, so the step fails instead of adopting an existing schema.
  4. `CREATE TABLE <cat>.<name>.t (a INT NOT NULL, b INT)`, then `ALTER TABLE … ADD CONSTRAINT b_chk CHECK (b >= a)`. Confirm that `INSERT … VALUES (2, 1)` is rejected and `(1, 2)` is accepted.
  5. Declare an informational PK: `ALTER TABLE … ADD CONSTRAINT t_pk PRIMARY KEY (a)` (needs `a NOT NULL`).
  6. Run `SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY a) FROM <cat>.<name>.t`.
  7. Clean up **only what this check created**: `DROP TABLE <cat>.<name>.t`, then `DROP SCHEMA <cat>.<name>` (no `CASCADE`).
  - Files: `docs/plan.md` (evidence log, D8); `docs/design.md` §2 (catalog default) and §10 (CHECK, PK/FK and `percentile_cont` `[VERIFY]` items)
  - Depends on: NAZ-01
  - Done when: each step's output is in the evidence log, the scratch schema is dropped, D8 is decided, and the related `[VERIFY]` tags in design §10 are resolved.

- [ ] **NAZ-04 · P0 · Git folder and `%run` behaviour.** Create a Git folder from the GitHub repo. On a scratch branch (never merged), use a 2-line test notebook to confirm that `%run ./00_config` shares variables with the caller and that an exception in a `%run` notebook stops the caller.
  - Files: `docs/plan.md` (evidence log); `docs/design.md` §3 and §10 (`%run` `[VERIFY]` items)
  - Depends on: NAZ-01
  - Done when: both behaviours are shown in the evidence log, and the `%run` `[VERIFY]` tags are resolved (or design §3 is changed through D7 if `%run` does not behave as assumed).

- [ ] **NAZ-05 · P1 · Drive D4, D7 and D9 to agreement.** D4 member mapping; D7 pipeline lifecycle and failure behaviour (staging → validate → publish, append-only audit, stale-output guard); D9 config parameters and schema names.
  - Files: `docs/plan.md` (decision log); `docs/design.md` §2 and §3 if anything changes
  - Depends on: D4: nothing (**start now**). D7: NAZ-04. D9: D8 (NAZ-03).
  - Done when: D4, D7 and D9 are marked "agreed" with all three names and a date.

- [ ] **NAZ-06 · P2 · Merge the uv setup.** `pyproject.toml`, `uv.lock` and `.gitignore` are committed on `docs/initial-plan` (local `uv lock`/`uv sync` evidence dated 2026-10-07). Get them reviewed and merged into `main`.
  - Files: `pyproject.toml`, `uv.lock`, `.gitignore`; `docs/requirements.md` (R-S7 status)
  - Depends on: nothing. **Start now.**
  - Done when: the PR is merged into `main` and R-S7 cites the evidence.

- [ ] **NAZ-07 · P2 · `00_config`.** Widgets `catalog`, `schema_prefix`, `source`; derived schema names; a `run_id` generator; placeholders for the allowed-value constants (filled in by NAZ-10).
  - Files: `notebooks/00_config.py`
  - Depends on: D9 (NAZ-05)
  - Done when: a caller notebook can `%run ./00_config` and use every name in design §2, and no other notebook needs a catalog or schema literal.

- [ ] **NAZ-08 · P2 · `01_bronze_ingest`.** All 8 tables copied as-is plus `_ingested_at` and `_source_table`, with `CREATE OR REPLACE`.
  - Files: `notebooks/01_bronze_ingest.py`
  - Depends on: NAZ-07
  - Done when: for every table, Bronze columns equal the source columns plus the 2 metadata columns, and Bronze counts equal source counts (output in the evidence log).

- [ ] **NAZ-09 · P2 · `profile_source`: value profiling.** On Bronze: value counts of `l_shipmode`, `l_returnflag`, `l_linestatus`, `o_orderpriority`; min/max of `o_orderdate`, `l_shipdate`, `l_commitdate`, `l_receiptdate`; lines per order (min / median / mean / max).
  - Files: `notebooks/profile_source.py` (value-profiling section); `docs/design.md` §5.5
  - Depends on: NAZ-08
  - Done when: the matching design §5.5 rows are filled with the query, date and result, and the `[PROFILE]` tags they cover are resolved.

- [ ] **NAZ-10 · P2 · Allowed-list constants.** Follow the design §6 procedure: compare the NAZ-09 output with the TPC-H documentation, log any mismatch in the decision log, then write the constants.
  - Files: `notebooks/00_config.py`; `docs/plan.md` (decision log, if there is a mismatch)
  - Depends on: NAZ-09; D13 (YAR-02)
  - Done when: `ALLOWED_SHIP_MODES`, `ALLOWED_RETURN_FLAGS` and `ALLOWED_LINE_STATUSES` hold the documented domain, the source is cited, and Yaropolk has approved the PR.

- [ ] **NAZ-11 · P2 · `run_pipeline` and audit tables.** Creates the `{prefix}_audit` tables (`pipeline_runs`, `dq_check_results`, columns as in design §3) if missing, never overwriting them; writes the `started` row; runs `%run` of 01–05; writes the `succeeded` row.
  - Files: `notebooks/run_pipeline.py`
  - Depends on: NAZ-04, NAZ-07; D7 (NAZ-05)
  - Done when: a forced failure in a step leaves a `started` row with no `succeeded` row (evidence), and a rerun keeps the earlier audit rows.

- [ ] **NAZ-12 · P3 · Full run with the default prefix.**
  - Files: `docs/plan.md` (evidence log)
  - Depends on: NAZ-08, NAZ-10, NAZ-11, YAR-04, YAR-05, YAR-06, MAX-03 merged
  - Done when: `pipeline_runs` shows `succeeded` for the run and all its `dq_check_results` rows have `passed = true` (output and `run_id` in the evidence log).

- [ ] **NAZ-13 · P3 · Rerun determinism.** Snapshot Gold to a scratch schema, rerun on unchanged data, then `EXCEPT ALL` in both directions. `_ingested_at`, `run_id` and the audit history are expected to differ.
  - Files: `docs/plan.md` (evidence log)
  - Depends on: NAZ-12
  - Done when: both `EXCEPT ALL` queries return 0 rows for every Gold table (output in the evidence log), and the scratch snapshot is dropped.

- [ ] **NAZ-14 · P3 · Portability run.** Run with `schema_prefix = nachalniki_logistics_porttest` and compare Gold with the default run.
  - Files: `docs/plan.md` (evidence log)
  - Depends on: NAZ-12
  - Done when: `EXCEPT ALL` both ways returns 0 rows for every Gold table, and **only** the `porttest` schemas this test created are dropped (output in the evidence log).

- [ ] **NAZ-15 · P3 · README setup and run sections.** Replace "planned" with the steps NAZ-12 actually used: Git folder, widget values, running `run_pipeline`, then `06_analysis`.
  - Files: `README.md` ("How to run")
  - Depends on: NAZ-12
  - Done when: every documented command has been run successfully, and the section is ready for MAX-05 to follow.

- [ ] **NAZ-16 · P5 · Get the due date and presentation format.** The PDF gives neither (requirements §4).
  - Files: `docs/plan.md` (NAZ-20 and the decision log)
  - Depends on: nothing. **Start now.**
  - Done when: the due date, how to submit, and any format rule are recorded with their source (course channel message or link).

- [ ] **NAZ-17 · P5 · Slides for team, repo, pipeline and challenges.** R-P2 "who did what" (from this plan), R-P3 repo link, a pipeline/config overview, and R-P4 challenges drawn from the decision log (each member supplies at least one from their area).
  - Files: the deck (location per NAZ-16)
  - Depends on: NAZ-12
  - Done when: the slides are in the deck and both other members have checked their part of "who did what".

- [ ] **NAZ-18 · P5 · Final README assembly.** Merge the sections from NAZ-15, YAR-10 and MAX-07; add the ER image and the presentation link; remove the "planning" status note.
  - Files: `README.md`
  - Depends on: NAZ-15, YAR-10, MAX-07, NAZ-19
  - Done when: the README has setup, run, validation, results, ER and presentation sections, and all three members have approved the PR (R-S10).

- [ ] **NAZ-19 · P5 · Deck assembly, demo script and timed rehearsal.** Combine NAZ-17, YAR-11 and MAX-08 into one deck; finalise the [demo script](#demo-script-draft--finalize-in-p5); run a timed rehearsal with all three.
  - Files: the deck; `docs/plan.md` (demo script, evidence log)
  - Depends on: NAZ-17, YAR-11, MAX-08
  - Done when: the deck covers R-P1 to R-P7, and a rehearsal of 5–7 minutes is recorded in the evidence log with its time.

- [ ] **NAZ-20 · P5 · Public repo check and submission.** Check that the repo is public from a logged-out browser, then submit before the due date (from NAZ-16).
  - Files: `docs/plan.md` (evidence log)
  - Depends on: NAZ-16, NAZ-18, NAZ-19
  - Done when: the logged-out check and the submission confirmation are in the evidence log, dated before the due date.

### Yaropolk

- [ ] **YAR-01 · P0 · Log in and read the source.** Log in to the workspace and run `SELECT count(*) FROM samples.tpch.lineitem`.
  - Files: `docs/plan.md` (evidence log)
  - Depends on: nothing. **Start now.**
  - Done when: the output is in the evidence log.

- [ ] **YAR-02 · P1 · Drive D13 and D14 to agreement.** D13: the allowed-list procedure (design §6). D14: the 3NF method (design §5.3, §5.4); any decomposition is decided later in YAR-03.
  - Files: `docs/plan.md` (decision log); `docs/design.md` §5.3, §5.4, §6 if anything changes
  - Depends on: nothing. **Start now.**
  - Done when: D13 and D14 are marked "agreed" with all three names and a date.

- [ ] **YAR-03 · P2 · FD and candidate-key tests (3NF evidence).** Run the design §5.3 method: check candidate keys, test each candidate FD with `GROUP BY X HAVING count(DISTINCT A) > 1`, and classify it. Apply the §5.4 decomposition only if a real violation is confirmed.
  - Files: `notebooks/profile_source.py` (a separate FD section, in its own PR; Nazar reviews); `docs/design.md` §5.3 and §5.5 (FD row)
  - Depends on: NAZ-08; D14 (YAR-02)
  - Done when: design §5.3/§5.5 hold the queries, outputs, dates and a classification for every candidate. If a decomposition is needed, it has a decision-log entry and an updated Silver contract approved by both other members.

- [ ] **YAR-04 · P2 · `02_silver_stage`.** Bronze → `{prefix}_staging.stg_*`, with casts and column selection only. No row filtering, no constraints.
  - Files: `notebooks/02_silver_stage.py`
  - Depends on: NAZ-08; D10 (MAX-02)
  - Done when: staging columns match the design §5.1 contract, and staging counts equal Bronze counts for all 8 tables (output in the evidence log).

- [ ] **YAR-05 · P2 · `03_validate`.** All rules DQ-L1–L9 and DQ-G1–G3 (design §6), appended to `{prefix}_audit.dq_check_results` with up to 10 sample keys; raises if any blocking rule fails.
  - Files: `notebooks/03_validate.py`
  - Depends on: YAR-04, NAZ-10 (allowed lists), NAZ-11 (audit tables)
  - Done when: a run on clean data gives `passed = true` for every rule, and an injected bad row in a *scratch prefix* makes the matching rule fail and raise (evidence for both).

- [ ] **YAR-06 · P2 · `04_silver_publish`.** Staging → `{prefix}_silver`, then the enforced NOT NULL/CHECK constraints and the informational PK/FK.
  - Files: `notebooks/04_silver_publish.py`
  - Depends on: YAR-05; NAZ-03 (constraint DDL verified); YAR-03 (any decomposition is included)
  - Done when: `DESCRIBE TABLE EXTENDED` or `SHOW TBLPROPERTIES` shows the constraints on the Silver tables (output in the evidence log).

- [ ] **YAR-07 · P2 · ER diagram.** Render it from the published Silver (updated Mermaid in design §5.2, or Catalog Explorer) and save the image.
  - Files: `docs/design.md` §5.2; an image in `docs/` (e.g. `docs/er_silver.png`)
  - Depends on: YAR-06; YAR-03
  - Done when: the image matches `DESCRIBE` of `{prefix}_silver`, and the `[VERIFY]` tag on design §5.2 is removed.

- [ ] **YAR-08 · P3 · End-to-end failure demo.** In a scratch prefix, inject one bad row (e.g. receipt before ship) into the staging path. Show the DQ failure, that Silver and Gold are unchanged, and that `06_analysis` refuses to present stale results.
  - Files: `docs/plan.md` (evidence log, demo script step 3)
  - Depends on: NAZ-12; MAX-04 (run-state guard)
  - Done when: all three effects are captured as evidence, and only the scratch schemas this demo created are dropped.

- [ ] **YAR-09 · P4 · Review the answer numbers.** Check every number in the README "Results" section against the Gold tables of the cited run. Nazar may review as well.
  - Files: none (PR review of MAX-07)
  - Depends on: MAX-07
  - Done when: Yaropolk has approved the MAX-07 PR, or each mismatch is fixed.

- [ ] **YAR-10 · P5 · README validation section.** The validation approach: lifecycle and blocking rules, how the allowed lists were derived (from NAZ-09/NAZ-10), the 3NF summary, and where the DQ results are stored.
  - Files: `README.md` ("Validation approach")
  - Depends on: YAR-05, YAR-03, NAZ-10
  - Done when: the section has no "planned" wording left, and every claim links to design.md or evidence.

- [ ] **YAR-11 · P5 · Validation, 3NF and ER slides.** R-P5 validation part (how we validate, plus the failure demo) and R-P6 ER screenshot.
  - Files: the deck
  - Depends on: YAR-07, YAR-08
  - Done when: the slides are in the deck and the validation part of the demo is rehearsed in NAZ-19.

### Max

- [ ] **MAX-01 · P0 · Log in and read the source.** Log in to the workspace and run `SELECT count(*) FROM samples.tpch.orders`.
  - Files: `docs/plan.md` (evidence log)
  - Depends on: nothing. **Start now.**
  - Done when: the output is in the evidence log.

- [ ] **MAX-02 · P1 · Drive D5, D6, D10, D11 and D12 to agreement.** D5 notebook charts as the visualisation; D6 naming (TPC-H names in Silver, business names in Gold); D10 Silver frozen columns for `orders` and `lineitem` (agreed with Yaropolk) and the Gold contracts; D11 metric definitions (transit, on time `<=`, fully on time, denominators, `percentile_cont`, predictability = p90 − p50, urgent literal, order-to-receipt as the primary Q4 measure); D12 monitoring grain = commit month with boundary months labelled.
  - Files: `docs/plan.md` (decision log); `docs/design.md` §5.1, §7, §8, §9 if anything changes
  - Depends on: D5, D11, D12: nothing (**start now**). D6, D10: NAZ-02 (`DESCRIBE` types).
  - Done when: D5, D6, D10, D11 and D12 are marked "agreed" with all three names and a date.

- [ ] **MAX-03 · P2 · `05_gold_build`.** The 8 Gold tables from design §9, plus DQ-GOLD1 and DQ-GOLD2 appended to `dq_check_results` (raises on failure). May be developed against a temporary Silver in a scratch prefix until YAR-06 is merged.
  - Files: `notebooks/05_gold_build.py`
  - Depends on: NAZ-07; D10, D11 (MAX-02); NAZ-03 (`percentile_cont` verified); NAZ-11 (audit tables)
  - Done when: run against the real Silver, the columns match design §9 exactly and the DQ-GOLD rows pass (output in the evidence log).

- [ ] **MAX-04 · P2 · `06_analysis`: guard, Q1–Q4 and charts 1–4.** A run-state guard that stops if the latest run in `pipeline_runs` has no `succeeded` row; Q1–Q4 queries on `{prefix}_gold` only; charts 1–4 (design §9); answer text cells that refer to the displayed numbers.
  - Files: `notebooks/06_analysis.py`
  - Depends on: MAX-03; NAZ-11 (`pipeline_runs`)
  - Done when: the guard stops the notebook on a run without `succeeded` (evidence), the notebook reads no schema other than Gold and audit, and every answer cell cites a displayed query result.

- [ ] **MAX-05 · P3 · Reproduce the run from the README alone.** As the second member, follow only the README to run the pipeline.
  - Files: `docs/plan.md` (evidence log); report README gaps to Nazar
  - Depends on: NAZ-15
  - Done when: a `succeeded` run started by Max is in the evidence log, and every README gap found is fixed.

- [ ] **MAX-06 · P4 · Monthly delay-rate chart (chart 5).** Line chart of `delay_rate` by commit month from `agg_delay_rate_monthly`, with `line_count`, boundary months labelled "potentially incomplete", and other low-count edge months named from the observed counts (design §8).
  - Files: `notebooks/06_analysis.py`
  - Depends on: MAX-04; D12; NAZ-12 (real data)
  - Done when: the chart renders from a succeeded run, and a screenshot is saved for the deck.

- [ ] **MAX-07 · P4 · Q1–Q4 answers in the README.** Write the answers with the actual numbers, the `run_id` and the date of the run they came from.
  - Files: `README.md` ("Results")
  - Depends on: MAX-04, MAX-06; NAZ-12
  - Done when: every number matches a displayed result in `06_analysis` for the cited succeeded run, and the PR is open for YAR-09.

- [ ] **MAX-08 · P5 · Q1–Q4 and monitoring slides.** R-P7: one slide per question with the chart, the query code and the answer, plus the monitoring chart.
  - Files: the deck
  - Depends on: MAX-07 (reviewed by YAR-09)
  - Done when: the slides are in the deck, and their numbers match the README.

## Optional follow-ups (not acceptance gates; unassigned)

- SQL alert or dashboard tile for a delay-rate increase (R-L-A1).
- An AI/BI dashboard mirroring the notebook charts.
- A Databricks Job chaining 01→05 (instead of `run_pipeline`).
- A rigorous complete-period rule for monthly monitoring.

## Demo script (draft — finalize in P5)

1. Nazar: show the repo README and config parameters (30 s).
2. Nazar: run, or show the last run of, `run_pipeline`. Show `pipeline_runs` and `dq_check_results` (1 min).
3. Yaropolk: show the failure demo: a bad row stops publish (1 min).
4. Yaropolk: show the Silver ER diagram (30 s).
5. Max: walk through charts Q1–Q4 and monitoring with the answers (2–3 min).

## Evidence log

| Date | Task | Evidence | By |
|---|---|---|---|
| 2026-10-07 | NAZ-06 | `uv lock` and `uv sync` succeeded locally (Windows, uv 0.12.21, CPython 3.13.5): "Resolved 1 package", `.venv` created; `uv.lock` generated (no dependencies) | Claude Code session for Nazar |
| – | – | Nothing has been executed in Databricks yet | – |

## Decision log

| ID | Date | Decision | Driver | Status |
|---|---|---|---|---|
| D1 | 2026-10-07 | Workspace: Databricks Free Edition or not yet known, so everything is parameterised | Nazar | decided (Nazar) |
| D2 | 2026-10-07 | All 8 TPC-H tables in Bronze and Silver; Gold covers Logistics only | Nazar | decided (Nazar) |
| D3 | 2026-10-07 | PySpark/SQL notebooks in `.py` source format; no Lakeflow, bundles or CI | Nazar | decided (Nazar) |
| D4 | 2026-10-07 | Member mapping M1 Nazar, M2 Yaropolk, M3 Max | Nazar (NAZ-05) | provisional |
| D5 | 2026-10-07 | Notebook charts satisfy the visualisation and monitoring requirements; dashboard, Job and alert are optional | Max (MAX-02) | proposed |
| D6 | 2026-10-07 | Silver keeps TPC-H column names; Gold uses business names | Max (MAX-02) | proposed |
| D7 | 2026-10-07 | Lifecycle: Bronze → staging → validate (append DQ) → publish Silver → Gold; failed run leaves outputs flagged as stale via `pipeline_runs` | Nazar (NAZ-05) | proposed |
| D8 | – | Catalog to use | Nazar (NAZ-03) | open (P0) |
| D9 | – | Config and schema names (design §2) | Nazar (NAZ-05) | open (P1) |
| D10 | – | Silver frozen columns and Gold contracts | Max (MAX-02) | open (P1) |
| D11 | – | Metric definitions (design §7) | Max (MAX-02) | open (P1) |
| D12 | – | Monitoring grain: commit month, with boundary months labelled | Max (MAX-02) | open (P1) |
| D13 | – | Allowed-list procedure | Yaropolk (YAR-02) | open (P1) |
| D14 | – | 3NF method; any decomposition after profiling | Yaropolk (YAR-02, YAR-03) | open (P1, P2) |

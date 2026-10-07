# Implementation plan

Living document. Requirements: [requirements.md](requirements.md). Design and contracts: [design.md](design.md). Handoff notes: [handoffs.md](handoffs.md).

> **Task distribution: agreed (D16) on 2026-10-07 by Nazar, Yaropolk and Max (agreement reported by Nazar; see the NAZ-05 evidence row).** It replaces the earlier split in which Nazar also owned integration, the final README, the deck and submission.

> **Stage 3 implementation reassigned by D22 on 2026-10-07.** Yaropolk owns Gold, analysis, pipeline integration, Databricks verification and the non-presentation README work. Max retains the deck, rehearsal and submission work. The existing `MAX-*` IDs are retained so dependencies and evidence links do not change.

**How to use this plan**
- Every task has one ID (`NAZ-nn`, `YAR-nn`, `MAX-nn`) and one primary owner: the person whose section it is in. Others review and help, but the owner makes sure it gets done.
- **Checkboxes exist only in [Tasks by person](#tasks-by-person).** The other sections only reference task IDs, so there is one checklist and no conflicting copies.
- Tick a box **only with evidence**: add a row to the [evidence log](#evidence-log) (output, screenshot path or link, plus the date), then tick the box in the same PR.
- **Transferred tasks keep their ID as a stub without a checkbox** in the original owner's section, in the form `NAZ-11 — transferred → MAX-09, YAR-12 (D16)`. IDs are never reused. Depend on the new ID, never on the stub.
- `D<n>` means an entry in the [decision log](#decision-log). `H1`/`H2` are the handoffs (see [Handoffs](#handoffs)).

## Team and stages (agreed, D16)

The work runs as three sequential stages. Each stage ends with a handoff; the next owner starts their implementation after it.

| Stage | Owner (alias) | Scope | Ends with |
|---|---|---|---|
| 1. Foundation and Bronze | Nazar (M1) | Repo and uv; Databricks access and capability checks; source inventory; value profiling (categorical values, date ranges, lines per order); `00_config` (incl. the run_id helpers of D15); `01_bronze_ingest` for all 8 tables; allowed-list constants; README setup and Stage 1 sections; own slide material | H1 → Yaropolk |
| 2. Silver and data quality | Yaropolk (M2); **Max since 2026-10-07 (D20)** | FD analysis and 3NF justification; `02_silver_stage`; `dq_helpers` and `dq_check_results`; `03_validate`; `04_silver_publish` and constraints; ER diagram; stage-level success and failure demo; README validation section; own slide material | H2 → Max |
| 3. Gold, analysis, integration and delivery | Yaropolk (implementation, D22); Max (presentation and submission) | Yaropolk: `05_gold_build`; `06_analysis` (guard, Q1–Q4, charts, monitoring); `run_pipeline` and `pipeline_runs`; full, end-to-end failure, rerun and portability runs; README run, results and non-presentation assembly. Max: deck assembly, demo script, rehearsal, presentation link and submission | submission |

Workload note: under D22 Yaropolk carries the Stage 3 integration work; Max carries the final presentation and submission work. Earlier stage deliverables remain unchanged. Everyone presents their own contribution. **Optional items are not assigned** (see [Optional follow-ups](#optional-follow-ups-not-acceptance-gates-unassigned)).

### Shared interfaces and owners

Every shared artifact has exactly one owner. Others change it only through a PR the owner reviews (or, after the owner's stage has ended, through the contract-change rule in [Workflow](#workflow)).

| Artifact | Owner | Notes |
|---|---|---|
| `notebooks/00_config.py`: widgets, derived names, `new_run_id()`, `require_run_id()`, allowed-list constants | Nazar | Later stage owners may **add** constants via PR. Renaming, removing or changing the meaning of an existing name is a contract change. |
| `{prefix}_bronze.*` and `01_bronze_ingest` | Nazar | Bronze never reads or writes `run_id` or audit tables |
| `profile_source`: value-profiling section | Nazar | |
| `profile_source`: FD section | Max (was Yaropolk; D20) | Separate section |
| `notebooks/dq_helpers.py` and `{prefix}_audit.dq_check_results` | Max (was Yaropolk; D20) | The only code that creates or appends to `dq_check_results`; `05_gold_build` calls it |
| `{prefix}_staging.*`, `{prefix}_silver.*`, `notebooks/silver_contract.py` and notebooks `02`–`04` | Max (was Yaropolk; D20) | |
| `notebooks/run_pipeline.py` and `{prefix}_audit.pipeline_runs` | Yaropolk (D22) | The only code that writes `pipeline_runs` |
| `{prefix}_gold.*`, `05_gold_build`, `06_analysis` | Yaropolk (D22) | |
| README sections | the author of each section | Yaropolk assembles the non-presentation README; Max adds the presentation link |
| Deck, demo script, rehearsal, submission | Max | Each member supplies their own slides |

Each notebook that writes a schema creates it with `CREATE SCHEMA IF NOT EXISTS` (design §3.1). The run_id and DQ interface is D15, specified in design §3.1.

### Unavoidable shared responsibilities

These cannot be given to one person; they are kept small and do not block anyone's stage from finishing:
- **P1 decisions** need all three names (the decision driver collects them).
- **Presenting in class**: each member presents their own part and attends the rehearsal that Max organises (R-S15, R-P1).
- **Defects**: each owner fixes defects found later in their own deliverables. This is the defect path, not planned work, and is not part of anyone's completion checklist.
- **Contract changes** after a handoff involve the contributors whose deliverables produce or consume that contract (see [Workflow](#workflow)).
- **Independent result review and README reproduction**: the author cannot verify their own results or instructions. Because Yaropolk authors MAX-07 and MAX-13 under D22, YAR-09 and YAR-14 must be performed by Nazar or Max. The `YAR-*` IDs are retained for traceability.

## Workspace model and handoff paths (D17, open)

**Sharing Git code does not share tables.** A handoff therefore always delivers *code that rebuilds the tables* plus *evidence of what they contained*, never only a table name. Whether the team uses one shared workspace or one workspace each is not decided yet (D17). Whether Databricks Free Edition allows several users in one workspace is **[VERIFY]**.

- **Separate workspaces** (e.g. one Free Edition account each). The receiver runs the earlier stages from `main` in their own workspace, setting the `catalog` widget to their own writable catalog. Bronze is a cheap, deterministic copy, so this costs minutes. The handoff note's evidence shows what the sender observed; the receiver's acceptance checks compare against their own source at runtime, never against copied numbers.
- **Shared workspace.** The receiver may read the previous stage's tables directly (grants **[VERIFY]**). The handoff note names the commit SHA and the `_ingested_at` value the tables came from. Scratch and demo work uses its own `schema_prefix`. After H2, only `run_pipeline` (MAX-10 onward) writes the default prefix.

## Workflow

- Branch per task from `main`: `feat/<area>-<short>`, e.g. `feat/bronze-ingest`, `feat/silver-validate`, `feat/gold-q1`. Put the task ID in the PR title, e.g. `NAZ-08: Add Bronze ingest`.
- Open a PR into `main`. At least one other member reviews it, then squash-merge. Keep PRs small, at one notebook or doc section each.
- **Suggested reviewers.** Stage 1 PRs: Yaropolk (the consumer). Stage 2 PRs: Max. Stage 3 implementation PRs: Max or Nazar, because Yaropolk is now the author. Any member may review any PR.
- A PR that changes a **frozen contract** (design §3.1 run_id/DQ interface, §5.1 frozen columns, §7 metrics, §9 Gold columns, config parameters) must update `design.md` in the same PR, add a decision-log entry, and be approved by **every contributor whose deliverables produce or consume that contract** (for example, Nazar only if a `00_config` name or the Bronze contract changes).
- Notebooks are edited in a Databricks Git folder (or locally) and committed as `.py` source-format files.
- Never store tokens or credentials in the repo.

## Start here: what each person can do now

The P0 checks NAZ-01–04 have run in Databricks (evidence log, 2026-10-07). Status as of 2026-10-07:

| Person | Can start now | Waits for |
|---|---|---|
| Nazar | No open Stage 1 work. H1 was accepted and the allowed lists were reviewed by Max on 2026-10-07 (D20; evidence rows "H1 acceptance" and "NAZ-10 review"), so NAZ-10 and NAZ-21 can be ticked | – |
| Yaropolk | Stage 3 implementation under D22: first MAX-01 and MAX-02, then MAX-03 and MAX-09. The tasks retain their `MAX-*` IDs | – |
| Max | Stage 2 is finished. Retains MAX-08, MAX-16, MAX-17 and the presentation/submission portions of MAX-15 and MAX-18; may independently perform YAR-09 and YAR-14 | Stage 3 outputs for presentation; MAX-07 and MAX-13 for the two independent checks |

Suggested execution order (a summary, not a dependency chain; each task's **Depends on** line is authoritative): NAZ-05 → NAZ-07 → NAZ-08 → NAZ-09 → NAZ-10 → NAZ-15, NAZ-17 → NAZ-21 (H1) → YAR-03, YAR-04 → YAR-05 → YAR-06 → YAR-07, YAR-08 → YAR-10, YAR-11 → YAR-13 (H2) → MAX-03 → MAX-04 → MAX-10 → MAX-06 → MAX-07 → MAX-08 → MAX-16 → MAX-15 → MAX-18 → MAX-17. Work that can run alongside it once its own dependencies are met: YAR-12 (after NAZ-07), MAX-09 (after YAR-12), MAX-11, MAX-12, MAX-13 (after MAX-10), MAX-14 (after MAX-04 and MAX-10), YAR-14 (after MAX-13), YAR-09 (after MAX-07).

## Phases

Phase tags on each task are time labels only: **P0** access and source checks, **P1** contract sign-off, **P2** build, **P3** integration and real execution, **P4** analysis and monitoring, **P5** README, presentation and submission. The checkboxes are in [Tasks by person](#tasks-by-person).

| Stage | Tasks |
|---|---|
| 1 (Nazar) | P0: NAZ-01–04. P1: NAZ-05. P2: NAZ-06–10. P5: NAZ-15, NAZ-16, NAZ-17. Handoff: NAZ-21 (H1) |
| 2 (Yaropolk) | P0: YAR-01. P1: YAR-02. P2: YAR-03–07, YAR-12. P3: YAR-08. P5: YAR-10, YAR-11. Handoff: YAR-13 (H2). After H2: YAR-09 (P4), YAR-14 (P3) |
| 3 (Yaropolk implementation; Max presentation/submission, D22) | Yaropolk — P0: MAX-01; P1: MAX-02; P2: MAX-03, MAX-04, MAX-09; P3: MAX-10–14; P4: MAX-06, MAX-07; non-presentation parts of MAX-15 and MAX-18. Max — MAX-08, MAX-16, MAX-17 and presentation/submission parts of MAX-15 and MAX-18 |

P1 acceptance: D4–D7, D9–D16 marked "agreed" with all three names and a date; D17 decided, or both handoff paths documented in each handoff note.

## Handoffs

The handoff notes themselves are written in [handoffs.md](handoffs.md). A handoff is complete when its note is merged after review by the receiver (for H1, the review follows the merge: D19). If an acceptance check fails, the receiver lists the defects in the evidence log and the sender fixes them.

### H1 — Nazar → Yaropolk (NAZ-21)

Deliverables:
1. `00_config`, `01_bronze_ingest` and the value-profiling section of `profile_source`, merged into `main`, with the commit SHA.
2. The `catalog`, `schema_prefix` and `source` values used, and which workspace path of D17 applies.
3. The 8 Bronze tables with their column lists (source columns + `_ingested_at`, `_source_table`).
4. Links to the evidence-log rows: P0 checks (NAZ-01–04), source inventory and `DESCRIBE` (NAZ-02), Bronze run (NAZ-08), profiling (NAZ-09).
5. The allowed-list constants as written in `00_config`, the documentation they were cross-checked against, which values were observed and which were only documented, and any discrepancy resolved under D13.
6. The observed `o_orderpriority` values, including the confirmed urgent literal.
7. The exact commands that run Stage 1 (widgets, notebooks, order).
8. The run_id helpers (`new_run_id()`, `require_run_id()`) and how they were tested.
9. Resolved and remaining `[VERIFY]`/`[PROFILE]` items owned by Stage 1; every remaining item is listed as an assumption.
10. The README sections (NAZ-15), the slide-material location (NAZ-17), and the current repo visibility.

Acceptance checks (run by Yaropolk):
- **A1** `%run ./00_config` with the documented widgets resolves every name in design §2.
- **A2** Bronze has the 8 tables; each has the source columns plus the 2 metadata columns; each Bronze count equals the receiver's own source count, compared at runtime.
- **A3** Design §5.5 value-profiling rows are filled with query, date and result; the constants match the profiled values, each value's classification against the cited documentation is shown, and every discrepancy is resolved under D13 (design §6).
- **A4** A grep of `notebooks/` finds no catalog, schema or source literal outside `00_config`, and no hard-coded row count. The P0 diagnostic notebooks in `checks/p0/` are excluded: they are not part of the pipeline and take their catalog and source from their own widgets.
- **A5** Two consecutive executions of a test entry notebook (`%run ./00_config`, `run_id = new_run_id()`, `%run` of a child that prints `require_run_id()`) give two different run_ids, and the child prints its caller's id; a child run with no run_id defined fails. Notebooks: `checks/p2/run_id_helpers/a5_interactive` (attach to compute and click Run all twice in one session) for the two executions; `a5_child` run on its own for the failure. `a5_entry` checks A1 and the same sequence in a fresh context (for example a one-time job) and fails by design if rerun in a session that already holds a `run_id`.
- **A6** Every remaining assumption is listed in the note.

Result: an evidence-log row "H1 accepted" (or a defect list) by Yaropolk.

### H2 — Yaropolk → Max (YAR-13)

Deliverables:
1. `02_silver_stage`, `dq_helpers`, `03_validate`, `04_silver_publish` and the FD section of `profile_source`, merged, with the commit SHA.
2. The final Silver contract (design §5.1, including any §5.4 decomposition and its decision-log entry).
3. The Silver stage execution sequence (design §3.1) and the values used.
4. The final `dq_helpers` signatures and the list of rule IDs `03_validate` writes.
5. Evidence for the success run (all rules `passed` for the cited `run_id`) and the failure demo (YAR-08).
6. Constraint evidence (YAR-06), the ER image (YAR-07), the 3NF results (YAR-03).
7. Remaining assumptions, the README validation section (YAR-10) and the slide-material location (YAR-11).

Acceptance checks (run by Max):
- **B1** Silver `orders` and `lineitem` contain the frozen columns of design §5.1 with the agreed types.
- **B2** Running the Silver stage sequence (design §3.1) succeeds, and every `dq_check_results` row for that run's `run_id` has `passed = true`.
- **B3** From a scratch notebook, `record_dq_result(...)` and `raise_if_failed(run_id, rule_ids)` work as documented: a failing test row for the active run raises, and rows from other runs are ignored.
- **B4** `DESCRIBE TABLE EXTENDED` or `SHOW TBLPROPERTIES` shows the constraints of design §5.1.
- **B5** Every remaining assumption is listed in the note.

Result: an evidence-log row "H2 accepted" (or a defect list) by Max.

## Completion criteria

### Nazar is finished when…
- NAZ-01–NAZ-10, NAZ-15, NAZ-16, NAZ-17 and NAZ-21 are ticked with evidence.
- D8 is decided; D4, D9, D13, D15 and D16 are agreed; D17 is decided, or both paths are written in the H1 note.
- Stage 1 ran in a workspace where no Silver, Gold, audit table or runner of this project existed for the prefix used.
- The H1 note is merged after Yaropolk's review.

**Not required for Nazar to be finished:** any Silver, Gold, audit table, `run_pipeline`, full or rerun run, Q1–Q4 result, the final README, the deck, the rehearsal or the submission. After this point Nazar only fixes defects in Stage 1 deliverables, takes part in contract changes that touch `00_config` or Bronze, and presents the Stage 1 part.

These lists are completion conditions, not a second checklist: they are met when the listed tasks are ticked in [Tasks by person](#tasks-by-person).

### Yaropolk's stage is finished when…
- YAR-01–YAR-08 and YAR-10–YAR-13 are ticked with evidence.
- D14 is agreed.
- The H2 note is merged after Max's review.

Remaining independent checks after H2: YAR-09 (review the answer numbers) and YAR-14 (reproduce the run from the README). Because Yaropolk now authors their prerequisites under D22, Nazar or Max must perform both checks.

Since D20 Max owns this stage; D14 counts as met when "decided" by the stage owner. Status 2026-10-07: every listed task is ticked and H2 is merged (`fd64374`), so the stage is finished.

### Stage 3 is finished when…
- Yaropolk's implementation tasks (MAX-01–MAX-07, MAX-09–MAX-14 and the non-presentation portions of MAX-15/MAX-18) are ticked with evidence.
- Max's presentation/submission tasks (MAX-08, MAX-16, MAX-17 and the remaining portions of MAX-15/MAX-18) are ticked with evidence.
- D5, D6, D7, D10, D11 and D12 are agreed.
- YAR-09 and YAR-14 have been performed independently by Nazar or Max.
- The submission confirmation is in the evidence log, dated before the due date.

## Tasks by person

Each task lists: **Files** (to create or edit), **Depends on** (what must be ready first) and **Done when** (the completion criterion). A dependency on `D<n>` means that decision is marked "agreed".

### Nazar

- [x] **NAZ-01 · P0 · Log in and list catalogs.** Run `SHOW CATALOGS;` and `SELECT current_catalog();`. Do not assume `workspace` exists.
  - Files: `docs/plan.md` (evidence log)
  - Depends on: nothing. **Start now.**
  - Done when: both outputs are in the evidence log, and a candidate writable catalog is named for NAZ-03.

- [x] **NAZ-02 · P0 · Source inventory.** `SHOW TABLES IN samples.tpch;` (expect 8 tables), `SELECT count(*)` for each table, and `DESCRIBE samples.tpch.<table>` for all 8. Record the counts for reference only: code never hard-codes them.
  - Files: `docs/plan.md` (evidence log); `docs/design.md` §5.5 (`DESCRIBE` row) and §5.1/§5.2 (fix types if they differ)
  - Depends on: NAZ-01
  - Done when: the 8 tables, counts and `DESCRIBE` outputs are in the evidence log with a date, and design §5.1/§5.2 types match `DESCRIBE`.
  - Optional aid, not part of "done": read `/dbfs/databricks-datasets/tpch/README.md`. If DBFS FUSE is blocked, try `dbutils.fs.head("dbfs:/databricks-datasets/tpch/README.md")`. If both fail, use the TPC-H specification and note that in the evidence log.

- [x] **NAZ-03 · P0 · Safe write check and catalog decision.** In the candidate catalog `<cat>`:
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

- [x] **NAZ-04 · P0 · Git folder and `%run` behaviour.** Create a Git folder from the GitHub repo. On a scratch branch (never merged), use small test notebooks to confirm:
  1. `%run ./00_config` (or a 2-line stand-in) shares variables with the caller;
  2. an exception in a `%run` notebook stops the caller;
  3. a variable assigned in the caller before `%run ./child` (e.g. `run_id`) is visible inside the child and unchanged after the child itself runs `%run` of a config stand-in that does not assign it (needed for D15);
  4. widget values set in the caller are the values the `%run` child reads.
  - Files: `docs/plan.md` (evidence log); `docs/design.md` §3 and §10 (`%run` `[VERIFY]` items)
  - Depends on: NAZ-01
  - Done when: all four behaviours are shown in the evidence log, and the `%run` `[VERIFY]` tags are resolved (or design §3 is changed through D7/D15 if `%run` does not behave as assumed).

- [x] **NAZ-05 · P1 · Drive D4, D9, D13, D15, D16 and D17 to agreement.** D4 member mapping; D9 config parameters and schema names; D13 the allowed-list procedure (design §6, transferred from YAR-02 because Nazar applies it in NAZ-10); D15 the run_id and DQ interface (design §3.1); D16 this task distribution; D17 the workspace model.
  - Files: `docs/plan.md` (decision log, evidence log); `docs/design.md` §2, §3.1 and §6 if anything changes
  - Depends on: nothing left (D8 is decided and NAZ-04 is done). D17 needs the team's answer on shared vs separate workspaces.
  - Process: one proposal message to Yaropolk and Max covering all six decisions; one confirmation from each (chat reply or PR review) is enough.
  - Done when: D4, D9, D13, D15 and D16 are marked "agreed" with all three names and a date; D17 is decided or recorded as "both paths documented"; and an evidence-log row links the confirmations.
  - Status 2026-10-07: D4, D9, D13, D15, D16 agreed (team agreement reported by Nazar; no individual replies or PR approvals are recorded). D17 has no confirmed arrangement, so both paths are documented in H1.
  - D7 (lifecycle) — transferred → MAX-02 (D16), because Max implements the runner and the stale-output guard.

- [x] **NAZ-06 · P2 · Merge the uv setup.** `pyproject.toml`, `uv.lock` and `.gitignore` are committed on `docs/initial-plan` (local `uv lock`/`uv sync` evidence dated 2026-10-07). Get them reviewed and merged into `main`.
  - Files: `pyproject.toml`, `uv.lock`, `.gitignore`; `docs/requirements.md` (R-S7 status)
  - Depends on: nothing. **Start now.**
  - Done when: the PR is merged into `main` and R-S7 cites the evidence.
  - Status 2026-10-07: merged into `main` in [PR #1](https://github.com/Badabuba/nachalniki-logistics/pull/1) (squash commit `79d37e4`) without a prior review (D19); R-S7 cites the evidence.

- [x] **NAZ-07 · P2 · `00_config`.** Widgets `catalog`, `schema_prefix`, `source`; derived schema names; the D15 helpers `new_run_id()` (returns a fresh `str(uuid.uuid4())`) and `require_run_id()` (returns the caller's `run_id` or raises if none is defined). `00_config` itself **never assigns `run_id`**. Placeholders for the allowed-value constants (filled in by NAZ-10).
  - Files: `notebooks/00_config.py`
  - Depends on: D9, D15 (NAZ-05); NAZ-04
  - Done when: a caller notebook can `%run ./00_config` and use every name in design §2; no other notebook needs a catalog or schema literal; and the A5 test of [H1](#h1--nazar--yaropolk-naz-21) passes on a scratch branch (evidence).
  - Status 2026-10-07: done. A1, A4, A5 in one context and the child-only failure on serverless job runs; A5 in an attached interactive session (`a5_interactive`, Run all twice) run by Nazar; D9 and D15 agreed (evidence log).

- [x] **NAZ-08 · P2 · `01_bronze_ingest`.** All 8 tables copied as-is plus `_ingested_at` and `_source_table`, with `CREATE OR REPLACE`. Needs only `00_config`: no `run_id`, audit table, Silver, Gold or runner.
  - Files: `notebooks/01_bronze_ingest.py`
  - Depends on: NAZ-07
  - Done when: for every table, Bronze columns equal the source columns plus the 2 metadata columns, and Bronze counts equal source counts (output in the evidence log).

- [x] **NAZ-09 · P2 · `profile_source`: value profiling.** On Bronze: value counts of `l_shipmode`, `l_returnflag`, `l_linestatus`, `o_orderpriority`; min/max of `o_orderdate`, `l_shipdate`, `l_commitdate`, `l_receiptdate`; lines per order (min / median / mean / max).
  - Files: `notebooks/profile_source.py` (value-profiling section); `docs/design.md` §5.5
  - Depends on: NAZ-08
  - Done when: the matching design §5.5 rows are filled with the query, date and result; the urgent literal of design §7 is confirmed or corrected; and the `[PROFILE]` tags they cover are resolved.

- [ ] **NAZ-10 · P2 · Allowed-list constants.** Follow the design §6 procedure: compare the NAZ-09 output with the TPC-H documentation, log any mismatch in the decision log, then write the constants.
  - Files: `notebooks/00_config.py`; `docs/plan.md` (decision log, if there is a mismatch)
  - Depends on: NAZ-09; D13 (NAZ-05)
  - Done when: `ALLOWED_SHIP_MODES`, `ALLOWED_RETURN_FLAGS` and `ALLOWED_LINE_STATUSES` are built from the profiled values; every value is classified as observed and documented, documented but not observed, or observed but not documented, against the cited documentation; every discrepancy is resolved in the decision log; and the PR is approved by one other member (Yaropolk preferred, as the consumer in `03_validate`).
  - Status 2026-10-07: constants written and classified (design §6; no discrepancy), D13 agreed, merged into `main` (`79d37e4`). Still pending: Yaropolk's review of the constants. PR #1 was merged before any review (D19), so the approval is recorded as an evidence-log row by Yaropolk instead of a PR approval.

- NAZ-11 — transferred → MAX-09 (`run_pipeline`, `pipeline_runs`) and YAR-12 (`dq_helpers`, `dq_check_results`) (D16).
- NAZ-12 — transferred → MAX-10 (D16).
- NAZ-13 — transferred → MAX-11 (D16).
- NAZ-14 — transferred → MAX-12 (D16).

- [x] **NAZ-15 · P5 · README setup and Stage 1 sections.** *Rescoped (D16).* "Setup" (prerequisites, Git folder, uv, widget values) and "Configuration, Bronze and profiling" (how to run `00_config`, `01_bronze_ingest` and `profile_source` standalone; the observed allowed values and how they were derived). Use only commands actually run in NAZ-07–NAZ-09. The full-pipeline "How to run" section — transferred → MAX-13.
  - Files: `README.md` ("Setup", "Configuration, Bronze and profiling")
  - Depends on: NAZ-08, NAZ-09, NAZ-10
  - Done when: every documented command has been run successfully (evidence-log reference), and the sections have no "planned" wording left.
  - Status 2026-10-07: both sections document only the commands actually run (CLI import into a workspace folder and serverless job runs; evidence rows "Stage 1 setup", NAZ-08, NAZ-09). Running from a Git folder is mentioned as an alternative location, not as a tested Stage 1 command.

- [x] **NAZ-16 · P5 · Get the due date and presentation format.** The PDF gives neither (requirements §4). Also record where slide material goes (deck link or file).
  - Files: `docs/plan.md` (MAX-17 and the decision log)
  - Depends on: nothing. **Start now.**
  - Done when: the due date, how to submit, any format rule and the deck location are recorded with their source (course channel message or link). If the course has not announced them yet, "not announced as of <date>" is recorded and MAX-17 owns the follow-up.
  - Result 2026-10-07 (D18): **due date and submission method: not provided to this session.** `group_assignment_1.pdf` §2 says only "submit the presentation before the due date and present it in class" and gives no date or channel; no other course material was available. Format rules from PDF §3.2 and §3.4: the presentation is in the public repo or linked from the README; 5–7 minutes; team member responsibilities, repo link, challenges, a short demo including how validation was decided, a screenshot of the Silver ER diagram, and the business-question answers with code and a visualisation. Deck location: not decided; until then each member's slide material is in `docs/slides/<name>.md`. Follow-up on the date and submission method: MAX-17.

- [x] **NAZ-17 · P5 · Slide material for Stage 1.** *Rescoped (D16).* Ready-to-assemble slides for: repo and uv, with the R-P3 repo link; configuration and portability parameters; Bronze; profiling and how the allowed lists were derived (R-L-V2); at least one challenge from Stage 1 (R-P4). Include speaker notes and screenshots from the evidence log. The "who did what" slide — transferred → MAX-16.
  - Files: the deck location from NAZ-16; if none is decided, `docs/slides/nazar.md` (slide titles, bullets, speaker notes, image paths)
  - Depends on: NAZ-08, NAZ-09, NAZ-10
  - Done when: the material is in place, every number on it cites an evidence-log row, and Max can drop it into the deck without rewriting.
  - Status 2026-10-07: `docs/slides/nazar.md` (2 slides with speaker notes) with two images in `docs/slides/img/`, rendered from the Databricks run exports of the NAZ-08 and NAZ-09 runs (not live workspace screenshots). The deck location is not decided (NAZ-16), so the material stays in this file for MAX-16.

- NAZ-18 — transferred → MAX-15 (D16).
- NAZ-19 — transferred → MAX-16 (D16).
- NAZ-20 — transferred → MAX-17 (D16).

- [ ] **NAZ-21 · P2 · Handoff H1 to Yaropolk.** *New (D16).* Fill the H1 note with every deliverable in [H1](#h1--nazar--yaropolk-naz-21), including the current repo visibility (checked from a logged-out browser).
  - Files: `docs/handoffs.md` (H1)
  - Depends on: NAZ-01–NAZ-10, NAZ-15, NAZ-17
  - Done when: the H1 note is merged after Yaropolk's review, and the A1–A6 result is in the evidence log (defects found later follow the defect path).
  - Status 2026-10-07: implementation merged into `main` in [PR #1](https://github.com/Badabuba/nachalniki-logistics/pull/1) (squash commit `79d37e4`); H1 note filled with that SHA; the implementer's self-check of A1–A6 is in the evidence log. Still pending: Yaropolk's review of the H1 note and Yaropolk's own A1–A6 run, recorded as "H1 accepted" or a defect list (D19).

### Yaropolk (Stage 2 tasks, owner Max since D20)

Max took over every task in this section on 2026-10-07 (D20). The IDs stay unchanged. Max made the Stage 2 decisions (D10 Silver part, D14, D21) as the stage owner; no confirmation by Nazar or Yaropolk is recorded. All Stage 2 runs used `schema_prefix = makc_logistics` (scratch prefixes `makc_logistics_dqtest`, `makc_logistics_s2demo`) in the shared workspace, never the default prefix.

- [x] **YAR-01 · P0 · Log in and read the source.** Log in to the workspace and run `SELECT count(*) FROM samples.tpch.lineitem`.
  - Files: `docs/plan.md` (evidence log)
  - Depends on: nothing. **Start now.**
  - Done when: the output is in the evidence log.
  - Status 2026-10-07: done by Max (evidence row YAR-01).

- [x] **YAR-02 · P1 · Drive D14 to agreement.** D14: the 3NF method (design §5.3, §5.4); any decomposition is decided later in YAR-03. D13 — transferred → NAZ-05 (D16).
  - Files: `docs/plan.md` (decision log); `docs/design.md` §5.3, §5.4 if anything changes
  - Depends on: nothing. **Start now.**
  - Done when: D14 is marked "agreed" with all three names and a date. *Changed by D20:* decided by the Stage 2 owner with a date.
  - Status 2026-10-07: D14 decided by Max (method of design §5.3 unchanged; one candidate added, the constant `o_shippriority`).

- [x] **YAR-03 · P2 · FD and candidate-key tests (3NF evidence).** Run the design §5.3 method: check candidate keys, test each candidate FD with `GROUP BY X HAVING count(DISTINCT A) > 1`, and classify it. Apply the §5.4 decomposition only if a real violation is confirmed.
  - Files: `notebooks/profile_source.py` (a separate FD section, in its own PR; any one member reviews); `docs/design.md` §5.3 and §5.5 (FD row)
  - Depends on: H1 (NAZ-21); D14 (YAR-02)
  - Done when: design §5.3/§5.5 hold the queries, outputs, dates and a classification for every candidate. If a decomposition is needed, it has a decision-log entry and an updated Silver contract approved by Max (the consumer).
  - Status 2026-10-07: done (evidence row YAR-03). Three documented dependencies hold, so `brand`, `ship_date_status` and `part_quantity_price` were split off (D21); the Silver contract in design §5.1 was updated by Max, who is also its consumer.

- [x] **YAR-04 · P2 · `02_silver_stage`.** Bronze → `{prefix}_staging.stg_*`, with casts and column selection only. No row filtering, no constraints.
  - Files: `notebooks/02_silver_stage.py`; `notebooks/silver_contract.py` (new: the Silver contract shared by 02–04)
  - Depends on: H1 (NAZ-21); D10 (MAX-02)
  - Done when: staging columns match the design §5.1 contract, and staging counts equal Bronze counts for all 8 tables (output in the evidence log).
  - Status 2026-10-07: done (evidence row "YAR-04, YAR-05, YAR-06 success runs"). D10 decided by Max for the Silver part only; the Gold part stays with MAX-02.

- [x] **YAR-12 · P2 · `dq_helpers` and `dq_check_results`.** *New (D16; replaces the audit-table part of NAZ-11).* Implement design §3.1: `ensure_dq_check_results()` (create if missing, never replace), `record_dq_result(run_id, rule_id, layer, table_name, violation_count, sample_keys)` and `raise_if_failed(run_id, rule_ids)`, which reads only rows of that `run_id` and those `rule_ids` and raises if any is not `passed` or any rule has no row.
  - Files: `notebooks/dq_helpers.py`; test `checks/p2/dq_helpers/dq_helpers_test.py`
  - Depends on: NAZ-07; D15
  - Done when: a scratch-prefix test shows (a) the table keeps earlier rows across runs, (b) a failing row of the active run raises, and (c) a failing row of an *earlier* run does not affect the active run (evidence).
  - Status 2026-10-07: done (evidence row YAR-12).

- [x] **YAR-05 · P2 · `03_validate`.** All rules DQ-L1–L9 and DQ-G1–G3 (design §6), recorded through `dq_helpers` with up to 10 sample keys; ends with `raise_if_failed(run_id, <its rule IDs>)`.
  - Files: `notebooks/03_validate.py`
  - Depends on: YAR-04, YAR-12, NAZ-10 (allowed lists)
  - Done when: a run on clean data gives `passed = true` for every rule of that `run_id`, and an injected bad row in a *scratch prefix* makes the matching rule fail and raise (evidence for both).
  - Status 2026-10-07: done (evidence rows "YAR-04, YAR-05, YAR-06 success runs" and YAR-08).

- [x] **YAR-06 · P2 · `04_silver_publish`.** Staging → `{prefix}_silver`, then the enforced NOT NULL/CHECK constraints and the informational PK/FK.
  - Files: `notebooks/04_silver_publish.py`
  - Depends on: YAR-05; NAZ-03 (constraint DDL verified); YAR-03 (any decomposition is included)
  - Done when: `DESCRIBE TABLE EXTENDED` or `SHOW TBLPROPERTIES` shows the constraints on the Silver tables (output in the evidence log).
  - Status 2026-10-07: done (evidence row "YAR-04, YAR-05, YAR-06 success runs"): `SHOW TBLPROPERTIES` shows the CHECK, `information_schema` shows the 11 PKs, 12 FKs and the NOT NULL columns. FK DDL `[VERIFY]` resolved.

- [x] **YAR-07 · P2 · ER diagram.** Render it from the published Silver (updated Mermaid in design §5.2, or Catalog Explorer) and save the image.
  - Files: `docs/design.md` §5.2; `docs/silver_er.mmd`; `docs/silver_er.png`
  - Depends on: YAR-06; YAR-03
  - Done when: the image matches `DESCRIBE` of `{prefix}_silver`, and the `[VERIFY]` tag on design §5.2 is removed.
  - Status 2026-10-07: done (evidence row YAR-07).

- [x] **YAR-08 · P3 · Stage-level success and failure demo.** *Rescoped (D16).* In a scratch prefix, run the Silver stage execution (design §3.1: fresh `run_id`, then `%run` 02 → 03 → 04 in one context). (a) Clean data: every rule of that run passes and Silver is published. (b) A new execution with one injected bad row in the staging path (e.g. receipt before ship): `03_validate` raises, the rule's row for *this* `run_id` has `passed = false`, `04_silver_publish` does not execute, and Silver is unchanged (`EXCEPT ALL` both ways against a snapshot = 0 rows). The Gold and `06_analysis` part — transferred → MAX-14.
  - Files: `docs/plan.md` (evidence log, demo script step 3); entry and check notebooks `checks/p2/silver_stage/silver_stage_entry.py`, `silver_snapshot.py`
  - Depends on: YAR-06
  - Done when: both outcomes are captured as evidence, and only the scratch schemas this demo created are dropped.
  - Status 2026-10-07: done (evidence row YAR-08).

- [ ] **YAR-09 · P4 · Review the answer numbers.** Check every number in the README "Results" section against the Gold tables of the cited run.
  - Files: none (PR review of MAX-07)
  - Depends on: MAX-07
  - Done when: Nazar or Max has approved the MAX-07 PR, or each mismatch is fixed (D22).
  - Status 2026-10-07: not started (needs MAX-07). Yaropolk now authors MAX-07, so cannot perform this independent check.

- [x] **YAR-10 · P5 · README validation section.** The validation approach: lifecycle and blocking rules, how the allowed lists were derived (from NAZ-09/NAZ-10), the 3NF summary, where the DQ results are stored, and the Silver stage execution commands.
  - Files: `README.md` ("Validation approach")
  - Depends on: YAR-05, YAR-03, NAZ-10
  - Done when: the section has no "planned" wording left, and every claim links to design.md or evidence.
  - Status 2026-10-07: done. The section links to design.md §5.3 and §6 and cites the run ids of the evidence rows; the Silver stage commands are the ones used for those runs.

- [x] **YAR-11 · P5 · Validation, 3NF and ER slide material.** R-P5 validation part (how we validate, plus the YAR-08 failure demo), R-P6 ER screenshot, and at least one challenge from Stage 2 (R-P4), with speaker notes.
  - Files: the deck location from NAZ-16; if none, `docs/slides/stage2.md` (renamed from `yaropolk.md` by D20)
  - Depends on: YAR-07, YAR-08
  - Done when: the material is in place, every number cites an evidence-log row, and Max can drop it into the deck without rewriting.
  - Status 2026-10-07: done. `docs/slides/stage2.md` (2 slides with speaker notes), images `docs/silver_er.png` and `docs/slides/img/silver_failure_demo_20261007.png` (rendered from the decoded run exports, not a live workspace screenshot).

- [x] **YAR-13 · P3 · Handoff H2 to Max.** *New (D16).* Fill the H2 note with every deliverable in [H2](#h2--yaropolk--max-yar-13).
  - Files: `docs/handoffs.md` (H2)
  - Depends on: YAR-03–YAR-08, YAR-10, YAR-11, YAR-12
  - Done when: the H2 note is merged after Max's review, and the B1–B5 result is in the evidence log.
  - Status 2026-10-07: done. H2 note filled, B1–B5 checked (evidence row "H2 B1–B5") and merged into `main` in [PR #4](https://github.com/Badabuba/nachalniki-logistics/pull/4) (`fd64374`). After D20 the sender and the receiver are the same person, so the check is not independent.

- [ ] **YAR-14 · P3 · Reproduce the run from the README alone.** *New (D16; replaces MAX-05).* As the second member, follow only the README to run the full pipeline. Under D22 the independent reproducer is Nazar or Max.
  - Files: `docs/plan.md` (evidence log); report README gaps to Yaropolk
  - Depends on: MAX-13
  - Done when: a `succeeded` run started by Nazar or Max is in the evidence log, and every README gap found has been reported (Yaropolk fixes them in MAX-13).
  - Status 2026-10-07: not started (needs MAX-13). Yaropolk now authors MAX-13, so cannot perform this independent reproduction.

### Stage 3 tasks (`MAX-*` IDs retained)

Under D22, Yaropolk owns MAX-01–MAX-07 and MAX-09–MAX-14, plus the non-presentation portions of MAX-15 and MAX-18. Max retains MAX-08, MAX-16, MAX-17 and the presentation/submission portions of MAX-15 and MAX-18. Keeping the existing IDs avoids breaking dependencies and evidence references.

- [x] **MAX-01 · P0 · Log in and read the source.** Log in to the workspace and run `SELECT count(*) FROM samples.tpch.orders`.
  - Files: `docs/plan.md` (evidence log)
  - Depends on: nothing. **Start now.**
  - Done when: the output is in the evidence log.
  - Status 2026-10-07: done by Yaropolk under D22 (evidence row MAX-01).

- [x] **MAX-02 · P1 · Drive D5, D6, D7, D10, D11 and D12 to agreement.** D5 notebook charts as the visualisation; D6 naming (TPC-H names in Silver, business names in Gold); D7 pipeline lifecycle and failure behaviour (staging → validate → publish, append-only audit, stale-output guard; transferred from NAZ-05); D10 Silver frozen columns for `orders` and `lineitem` (agreed with Yaropolk) and the Gold contracts; D11 metric definitions (transit, on time `<=`, fully on time, denominators, `percentile_cont`, predictability = p90 − p50, urgent literal, order-to-receipt as the primary Q4 measure); D12 monitoring grain = commit month with boundary months labelled.
  - Files: `docs/plan.md` (decision log); `docs/design.md` §3, §5.1, §7, §8, §9 if anything changes
  - Depends on: D5, D11, D12: nothing (**start now**). D6, D10: NAZ-02 (`DESCRIBE` types). D7: NAZ-04 (`%run` evidence).
  - Done when: D5, D6, D7, D10, D11 and D12 are marked "agreed" with all three names and a date.
  - Status 2026-10-07: done. Yaropolk completed the technical audit under D22 and corrected the Q4 aggregate contract to include the required counts and p50/p90/mean measures. Nazar, Yaropolk and Max then agreed D5, D6, D7, the Gold part of D10, D11 and D12 (agreement reported by Yaropolk; evidence row MAX-02).

- [x] **MAX-03 · P2 · `05_gold_build`.** The 8 Gold tables from design §9, plus DQ-GOLD1 and DQ-GOLD2 recorded through `dq_helpers`, ending with `raise_if_failed(run_id, ["DQ-GOLD1", "DQ-GOLD2"])`. May be prototyped against a temporary Silver in a scratch prefix before H2.
  - Files: `notebooks/05_gold_build.py`
  - Depends on: H2 (YAR-13); YAR-12; D10, D11 (MAX-02); NAZ-03 (`percentile_cont` verified)
  - Done when: run against the real Silver, the columns match design §9 exactly and the DQ-GOLD rows of that `run_id` pass (output in the evidence log).
  - Status 2026-10-07: done by Yaropolk under D22. Eight Gold tables built in `workspace.yaropolk_logistics_gold`; exact columns matched design §9; DQ-GOLD1 and DQ-GOLD2 passed for run_id `253b9400-828e-43a4-9553-a25f4917e3db` (evidence row MAX-03).

- [ ] **MAX-04 · P2 · `06_analysis`: guard, Q1–Q4 and charts 1–4.** A run-state guard that stops if the latest run in `pipeline_runs` has no `succeeded` row; Q1–Q4 queries on `{prefix}_gold` only; charts 1–4 (design §9); answer text cells that refer to the displayed numbers.
  - Files: `notebooks/06_analysis.py`
  - Depends on: MAX-03; MAX-09 (`pipeline_runs`)
  - Done when: the guard stops the notebook on a run without `succeeded` (evidence), the notebook reads no schema other than Gold and audit, and every answer cell cites a displayed query result.

- MAX-05 — transferred → YAR-14 (D16).

- [ ] **MAX-06 · P4 · Monthly delay-rate chart (chart 5).** Line chart of `delay_rate` by commit month from `agg_delay_rate_monthly`, with `line_count`, boundary months labelled "potentially incomplete", and other low-count edge months named from the observed counts (design §8).
  - Files: `notebooks/06_analysis.py`
  - Depends on: MAX-04; D12; MAX-10 (real data)
  - Done when: the chart renders from a succeeded run, and a screenshot is saved for the deck.

- [ ] **MAX-07 · P4 · Q1–Q4 answers in the README.** Write the answers with the actual numbers, the `run_id` and the date of the run they came from.
  - Files: `README.md` ("Results")
  - Depends on: MAX-04, MAX-06; MAX-10
  - Done when: every number matches a displayed result in `06_analysis` for the cited succeeded run, and the PR is open for YAR-09.

- [ ] **MAX-08 · P5 · Q1–Q4 and monitoring slides.** R-P7: one slide per question with the chart, the query code and the answer, plus the monitoring chart.
  - Files: the deck
  - Depends on: MAX-07 (reviewed by YAR-09)
  - Done when: the slides are in the deck, and their numbers match the README.

- [ ] **MAX-09 · P2 · `run_pipeline` and `pipeline_runs`.** *New (D16; replaces the runner part of NAZ-11).* `%run ./00_config`; then `run_id = new_run_id()` in its own cell, **always**, even if the session already holds a `run_id`; create `{prefix}_audit.pipeline_runs` if missing (never overwrite); append `started`; `%run` 01–05 (children use `require_run_id()`); append `succeeded`.
  - Files: `notebooks/run_pipeline.py`
  - Depends on: NAZ-07, NAZ-08; YAR-12 (helpers); D7, D15
  - Done when: two consecutive executions in one session get different `run_id`s; a forced failure in a step leaves a `started` row with no `succeeded` row; and a rerun keeps the earlier audit rows (evidence for all three).

- [ ] **MAX-10 · P3 · Full run with the default prefix.** *Transferred from NAZ-12.*
  - Files: `docs/plan.md` (evidence log)
  - Depends on: MAX-03, MAX-09, H2 (YAR-13)
  - Done when: `pipeline_runs` shows `succeeded` for the run and all its `dq_check_results` rows have `passed = true` (output and `run_id` in the evidence log).

- [ ] **MAX-11 · P3 · Rerun determinism.** *Transferred from NAZ-13.* Snapshot Gold to a scratch schema, rerun on unchanged data, then `EXCEPT ALL` in both directions. `_ingested_at`, `run_id` and the audit history are expected to differ.
  - Files: `docs/plan.md` (evidence log)
  - Depends on: MAX-10
  - Done when: both `EXCEPT ALL` queries return 0 rows for every Gold table (output in the evidence log), and the scratch snapshot is dropped.

- [ ] **MAX-12 · P3 · Portability run.** *Transferred from NAZ-14.* Run with `schema_prefix = nachalniki_logistics_porttest` and compare Gold with the default run.
  - Files: `docs/plan.md` (evidence log)
  - Depends on: MAX-10
  - Done when: `EXCEPT ALL` both ways returns 0 rows for every Gold table, and **only** the `porttest` schemas this test created are dropped (output in the evidence log).

- [ ] **MAX-13 · P3 · README "How to run".** *Transferred from the run part of NAZ-15.* The steps MAX-10 actually used: Git folder, widget values, running `run_pipeline`, then `06_analysis`. Links to the Stage 1 and validation sections rather than repeating them.
  - Files: `README.md` ("How to run")
  - Depends on: MAX-10
  - Done when: every documented command has been run successfully, the section is ready for YAR-14, and every gap YAR-14 reports is fixed.

- [ ] **MAX-14 · P3 · End-to-end failure check.** *Transferred from the end-to-end part of YAR-08.* In a scratch prefix with a succeeded run, start a new `run_pipeline` execution with one injected bad row. Show that the run has `started` but no `succeeded`, Gold is unchanged (`EXCEPT ALL` = 0 rows), and `06_analysis` refuses to present results.
  - Files: `docs/plan.md` (evidence log, demo script)
  - Depends on: MAX-04, MAX-10
  - Done when: all three effects are captured as evidence, and only the scratch schemas this check created are dropped.

- [ ] **MAX-15 · P5 · Final README assembly.** *Transferred from NAZ-18.* Merge the sections from NAZ-15, YAR-10, MAX-13 and MAX-07 without changing their meaning; add the ER image and the presentation link; remove the "planning" status note.
  - Files: `README.md`
  - Depends on: NAZ-15, YAR-10, MAX-13, MAX-07, MAX-16
  - Done when: the README has setup, run, validation, results, ER and presentation sections, and the PR is approved by at least one other member (each section's author already approved its content in their own PR) (R-S10).

- [ ] **MAX-16 · P5 · Deck assembly, demo script and timed rehearsal.** *Transferred from NAZ-19, plus the "who did what" and pipeline-overview slides from NAZ-17.* Combine NAZ-17, YAR-11 and MAX-08 into one deck; add R-P2 "who did what" (from this plan) and a pipeline overview; finalise the [demo script](#demo-script-draft--finalize-in-max-16); run a timed rehearsal with all three.
  - Files: the deck; `docs/plan.md` (demo script, evidence log)
  - Depends on: NAZ-17, YAR-11, MAX-08
  - Done when: the deck covers R-P1 to R-P7, and a rehearsal of 5–7 minutes is recorded in the evidence log with its time.

- [ ] **MAX-17 · P5 · Public repo check and submission.** *Transferred from NAZ-20.* Check that the repo is public from a logged-out browser, then submit before the due date. NAZ-16 found no due date or submission method in the material available on 2026-10-07 (D18), so MAX-17 gets them from the course first.
  - Files: `docs/plan.md` (evidence log)
  - Depends on: NAZ-16, MAX-15, MAX-16, MAX-18
  - Done when: the logged-out check and the submission confirmation are in the evidence log, dated before the due date.

- [ ] **MAX-18 · P5 · Final documentation cleanup.** *New, part of D16 (agreed 2026-10-07).* Before submission, make the submission self-contained. First move the definitions, assumptions, validation explanation, run instructions and results that the final reader needs into the README, the notebooks or the deck. Then review which working documents (`CLAUDE.md`, `docs/plan.md`, `docs/design.md`, `docs/requirements.md`, `docs/handoffs.md`) and diagnostics (`checks/`) to keep, remove only what is no longer needed, and fix every remaining link. Do not remove required evidence, attribution, `pyproject.toml`/`uv.lock` or configuration.
  - Files: `README.md`, the notebooks, the working documents
  - Depends on: MAX-15, MAX-16, MAX-11, MAX-12, MAX-14, YAR-09, YAR-14
  - Done when: no notebook or final README text depends on task or decision IDs or on a removed document, all links resolve, and the PR is approved by one other member.

## Optional follow-ups (not acceptance gates; unassigned)

- SQL alert or dashboard tile for a delay-rate increase (R-L-A1).
- An AI/BI dashboard mirroring the notebook charts.
- A Databricks Job chaining 01→05 (instead of `run_pipeline`).
- A rigorous complete-period rule for monthly monitoring.

## Demo script (draft — finalize in MAX-16)

1. Nazar: repo, config parameters, Bronze and how profiling produced the allowed lists (45 s).
2. Max: run, or show the last run of, `run_pipeline`. Show `pipeline_runs` and `dq_check_results` for that `run_id` (1 min).
3. Stage 2 (Max since D20; material in `docs/slides/stage2.md`): the failure demo: a bad row stops publish (1 min).
4. Stage 2: the 3NF decomposition and the Silver ER diagram (30 s).
5. Max: charts Q1–Q4 and monitoring with the answers (2–3 min).

## Evidence log

| Date | Task | Evidence | By |
|---|---|---|---|
| 2026-10-07 | NAZ-06 | `uv lock` and `uv sync` succeeded locally (Windows, uv 0.12.21, CPython 3.13.5): "Resolved 1 package", `.venv` created; `uv.lock` generated (no dependencies) | Claude Code session for Nazar |
| 2026-10-07 | NAZ-01 | `checks/p0/01_source_discovery.py` run by Nazar in Databricks (compute type not recorded; `current_version().dbr_version` = `19.9.x-aarch64-photon-scala2.13`, `spark.version` = 4.2.0). `SHOW CATALOGS` → `samples`, `system`, `workspace`. `current_catalog()` = `workspace`, `current_schema()` = `default`. Candidate write catalog for NAZ-03: `workspace` (visible and current; **write access not yet proven**). Raw outputs: [01_show_catalogs.csv](../checks/p0/outputs/source_discovery/01_show_catalogs.csv), [02_current_catalog_schema.csv](../checks/p0/outputs/source_discovery/02_current_catalog_schema.csv), [03_current_version.csv](../checks/p0/outputs/source_discovery/03_current_version.csv), [00_printed_output.txt](../checks/p0/outputs/source_discovery/00_printed_output.txt) | Nazar |
| 2026-10-07 | NAZ-02 | Same run. `SHOW TABLES IN samples.tpch` → exactly the 8 documented tables (missing: none, unexpected: none). Row counts (reference only, never hard-coded): customer 750000, lineitem 29999795, nation 25, orders 7500000, part 1000000, partsupp 4000000, region 5, supplier 50000. `DESCRIBE`: 61 columns over 8 tables; all keys `bigint` except `l_linenumber` `int`; money and quantity columns `decimal(18,2)`; date columns `date`; other columns `string` or `int`; no partition or extra rows. Recorded in design §5.1/§5.5. Raw outputs: [04_show_tables.csv](../checks/p0/outputs/source_discovery/04_show_tables.csv), [05_row_counts.csv](../checks/p0/outputs/source_discovery/05_row_counts.csv), [06_describe_tables.csv](../checks/p0/outputs/source_discovery/06_describe_tables.csv). The optional TPC-H README read was not run | Nazar |
| 2026-10-07 | NAZ-03 run 1 (blocked, superseded by run 2) | `checks/p0/02_workspace_capability_checks.py` with `write_catalog = workspace`. Step 1 ok: `workspace.nachalniki_access_check_20261007_121343_8e48` did not exist. Step 2 `CREATE SCHEMA` failed: `PERMISSION_DENIED: User does not have CREATE SCHEMA on Catalog 'workspace'` (`UNAUTHORIZED_ACCESS`, SQLSTATE 42501). Nothing was created, so cleanup had nothing to drop (cleanup failures = 0). Steps 3–8 (table, CHECK, PK, `percentile_cont`) did not run. **Blocker:** Nazar's user lacks `CREATE SCHEMA` on `workspace`, the only non-system, non-sample catalog visible. Raw outputs: [run1_20261007_121343_denied_results.csv](../checks/p0/outputs/workspace_capability_checks/run1_20261007_121343_denied_results.csv), [run1_20261007_121343_denied_error.txt](../checks/p0/outputs/workspace_capability_checks/run1_20261007_121343_denied_error.txt) | Nazar |
| 2026-10-07 | NAZ-03 run 2 | Rerun of the same notebook after Nazar reported being given admin rights in the workspace (the grant itself was not done by these checks). `write_catalog = workspace`, scratch schema `workspace.nachalniki_access_check_20261007_122756_c6bf`. All 16 result rows `ok`, overall **PASSED**, failures 0, cleanup failures 0: (1) name unused; (2) `CREATE SCHEMA` without `IF NOT EXISTS` ok; (3) `CREATE TABLE t (a INT NOT NULL, b INT) USING DELTA` ok; (4) `ADD CONSTRAINT b_chk CHECK (b >= a)` ok, `delta.constraints.b_chk = b >= a`; (5) insert `(2,1)` rejected with SQLSTATE 23001, `DELTA_VIOLATE_CONSTRAINT_WITH_VALUES`, "CHECK constraint b_chk (b >= a) violated", then `count(*) = 0`; (6) insert `(1,2)` accepted, `count(*) = 1`; (7) `ADD CONSTRAINT t_pk PRIMARY KEY (a)` ok, shown by `DESCRIBE TABLE EXTENDED` as `t_pk PRIMARY KEY (a)`, duplicate `(1,3)` accepted (`count(*) = 2`), so the PK is informational; (8) `percentile_cont(0.5)` on `t` = 1.0; on 1..4 p50 = 2.5, p90 = 3.7 (tolerance 1e-9); cleanup dropped `t` and the schema, and `SHOW SCHEMAS LIKE` returned 0 rows. FK DDL was not part of this check. Raw output: [run2_20261007_122756_passed_results.csv](../checks/p0/outputs/workspace_capability_checks/run2_20261007_122756_passed_results.csv) | Nazar |
| 2026-10-07 | CLI access (setup for later tasks) | Databricks CLI v1.19.0 installed locally (winget); OAuth login to profile `nachalniki` valid. The user is in the `admins` group; catalog `workspace` is owned by the workspace-admins group. Catalogs over the API: `samples`, `system`, `workspace`; one SQL warehouse (Serverless Starter Warehouse, 2X-Small). `workspace` already contains a schema owned by another user, so this workspace is shared (relevant to D17). No `nachalniki_access_check_*` schemas remain. Read-only test: `checks/p0/01_source_discovery.py` imported to `/Users/<nazar>/nachalniki_p0_checks/` and run as a one-time serverless job (`jobs submit`, no cluster): `SUCCESS` in 59 s. `jobs export-run` returned every cell output, and all of them match the NAZ-01/NAZ-02 files above (catalogs, current catalog, versions, 8 tables, counts, 61 columns) | Claude Code session for Nazar |
| 2026-10-07 | NAZ-04 Git folder | Scratch branch `scratch/run-behaviour` (commit `e8e7010`, test notebooks in `checks/p0/run_behaviour/`, never merged) pushed to GitHub. Git folder created with `databricks repos create` (public repo, no Git credentials needed) at `/Users/<nazar>/nachalniki-scratch-run-behaviour` and switched to that branch. All runs below are one-time serverless jobs (`jobs submit`, no cluster) of notebooks in this Git folder; cell outputs decoded from `jobs export-run`. Raw: [git_folder_20261007_repos_get.json](../checks/p0/outputs/run_behaviour/git_folder_20261007_repos_get.json) | Claude Code session for Nazar |
| 2026-10-07 | NAZ-04 (1) variables shared | Run `34484171186910`: `TERMINATED SUCCESS`. Child `config_stub` printed `config_stub: catalog='stub_default', CONFIG_LOADED=True`; the caller cell after `%run ./config_stub` printed `t1 caller: CONFIG_LOADED=True, catalog='stub_default'` and its assert passed. Raw: [t1_20261007_155915_success_get_run.json](../checks/p0/outputs/run_behaviour/t1_20261007_155915_success_get_run.json), [t1_20261007_155915_success_export.json](../checks/p0/outputs/run_behaviour/t1_20261007_155915_success_export.json), [t1_20261007_155915_success_decoded.json](../checks/p0/outputs/run_behaviour/t1_20261007_155915_success_decoded.json) | Claude Code session for Nazar |
| 2026-10-07 | NAZ-04 (2) exception stops caller | Run `627341262874552`: run state `INTERNAL_ERROR` / `FAILED` ("Task t2 failed with message: Workload failed, see run output for details."), task state `TERMINATED` / `FAILED`. Caller cell 1 printed `t2 caller: before %run`; inside `%run ./child_raises` the child printed `child_raises: before raise` then raised `RuntimeError: NAZ-04 deliberate failure`; the child's next cell and the caller's next cell both show `Command skipped` with no output. Raw: [t2_20261007_155917_failed_get_run.json](../checks/p0/outputs/run_behaviour/t2_20261007_155917_failed_get_run.json), [t2_20261007_155917_failed_export.json](../checks/p0/outputs/run_behaviour/t2_20261007_155917_failed_export.json), [t2_20261007_155917_failed_decoded.json](../checks/p0/outputs/run_behaviour/t2_20261007_155917_failed_decoded.json) | Claude Code session for Nazar |
| 2026-10-07 | NAZ-04 (3) caller run_id in child (D15) | Run `86806025563223`: `TERMINATED SUCCESS`. Caller ran `%run ./config_stub`, then assigned `run_id='7d884316-ba4f-4502-9a05-4596b71aa5f9'`, then `%run ./child_reads_run_id`. The child printed the same id on entry, ran `%run ./config_stub` (which never assigns `run_id`), and printed the same id after it. Back in the caller, `run_id`, `child_entry_run_id` and `child_seen_run_id` were all `'7d884316-ba4f-4502-9a05-4596b71aa5f9'` and the three asserts passed. Raw: [t3_20261007_155918_success_get_run.json](../checks/p0/outputs/run_behaviour/t3_20261007_155918_success_get_run.json), [t3_20261007_155918_success_export.json](../checks/p0/outputs/run_behaviour/t3_20261007_155918_success_export.json), [t3_20261007_155918_success_decoded.json](../checks/p0/outputs/run_behaviour/t3_20261007_155918_success_decoded.json) | Claude Code session for Nazar |
| 2026-10-07 | NAZ-04 (4) widgets | Notebook `t4_widgets`: the caller creates widget `caller_widget`, `%run ./config_stub` creates widget `catalog`, then `%run ./child_reads_widgets` reads both. Run `71392439870734` (no job parameters): `TERMINATED SUCCESS`; caller and child both printed `catalog='stub_default', caller_widget='caller_default'`. Run `93706008279910` (job parameters `catalog=from_job_param`, `caller_widget=from_job_param_2`): `TERMINATED SUCCESS`; caller and child both printed `catalog='from_job_param', caller_widget='from_job_param_2'`; asserts passed in both runs. Widget values typed in the notebook UI were not tested. Raw: [t4a_20261007_155921_success_get_run.json](../checks/p0/outputs/run_behaviour/t4a_20261007_155921_success_get_run.json), [t4a_20261007_155921_success_export.json](../checks/p0/outputs/run_behaviour/t4a_20261007_155921_success_export.json), [t4a_20261007_155921_success_decoded.json](../checks/p0/outputs/run_behaviour/t4a_20261007_155921_success_decoded.json), [t4b_20261007_155922_success_get_run.json](../checks/p0/outputs/run_behaviour/t4b_20261007_155922_success_get_run.json), [t4b_20261007_155922_success_export.json](../checks/p0/outputs/run_behaviour/t4b_20261007_155922_success_export.json), [t4b_20261007_155922_success_decoded.json](../checks/p0/outputs/run_behaviour/t4b_20261007_155922_success_decoded.json) | Claude Code session for Nazar |
| 2026-10-07 | Stage 1 setup | Notebooks `notebooks/00_config.py`, `01_bronze_ingest.py`, `profile_source.py` and the test notebooks `checks/p2/run_id_helpers/a5_entry.py`, `a5_child.py` (local working tree of `docs/initial-plan`, not committed) imported with `databricks workspace import --format SOURCE` into the new folder `/Users/<nazar>/nachalniki_stage1/`, which mirrors the repo layout. Before the first write, `databricks schemas list workspace` showed only `default`, `information_schema` and another user's schema, so no `nachalniki_logistics_*` schema existed. After the runs, `workspace export` of all 5 notebooks was identical to the local files. All runs are one-time serverless jobs (`jobs submit`, no cluster) with default widgets (`workspace`, `nachalniki_logistics`, `samples.tpch`); outputs decoded from `jobs export-run` | Claude Code session for Nazar |
| 2026-10-07 | NAZ-07 A1 + A5 (one execution context) | Run `1113516903146913`: `TERMINATED SUCCESS`. After `%run ../../../notebooks/00_config` every design §2 name is defined and `run_id` is not; `require_run_id()` with no `run_id` raised `RuntimeError`. Two executions were repeated **in the same notebook context**: execution 1 `run_id = new_run_id()` → `045f56ca-5a9b-4989-bd83-b75fda219eb0`, and the `%run` child's `require_run_id()` returned the same id; then `%run 00_config` again left `run_id` unchanged, and execution 2 `new_run_id()` → `32b4eba4-b8ea-4306-b2b2-460fc413cef1`, which the child also returned; all asserts passed. Rerun `338580797976871` after NAZ-10 filled the lists: `SUCCESS`, the same checks passed with new ids and the filled `ALLOWED_*` values printed. Raw: [run 1 decoded](../checks/p2/outputs/run_id_helpers/a5_entry_run1_20261007_164135_success_decoded.json) (+ `_get_run`, `_export`), [run 2 decoded](../checks/p2/outputs/run_id_helpers/a5_entry_run2_filled_lists_20261007_164708_success_decoded.json) (+ `_get_run`, `_export`). **Not tested:** an interactive notebook session (all runs were serverless jobs) | Claude Code session for Nazar |
| 2026-10-07 | NAZ-07 A5 (child without caller) | Run `5655121264011`: `INTERNAL_ERROR` / `FAILED` as intended. `a5_child` run on its own raised `RuntimeError: run_id is not defined. Start from an entry notebook that runs run_id = new_run_id() after %run ./00_config.` Raw: [decoded](../checks/p2/outputs/run_id_helpers/a5_child_alone_20261007_164221_failed_decoded.json) (+ `_get_run`, `_export`) | Claude Code session for Nazar |
| 2026-10-07 | NAZ-08 | Run `1104358970299952` of `01_bronze_ingest`: `TERMINATED SUCCESS` (133 s). It created `workspace.nachalniki_logistics_bronze` with the 8 tables; `_ingested_at = 2026-10-07 13:43:28.462558` (UTC). The check cell shows, for each of the 8 tables, source and Bronze business columns equal in name, order and data type (61 columns in total), both metadata columns present, and equal row counts (region 5, nation 25, supplier 50000, customer 750000, part 1000000, partsupp 4000000, orders 7500000, lineitem 29999795): `ok = true` for 8/8. Raw: [decoded](../checks/p2/outputs/bronze_ingest/bronze_ingest_20261007_164301_success_decoded.json) (+ `_get_run`, `_export`) | Claude Code session for Nazar |
| 2026-10-07 | NAZ-09 | Run `1029034196915021` of `profile_source` on that Bronze: `TERMINATED SUCCESS`. Value counts, value lengths, date ranges and lines per order (orders `LEFT JOIN` line counts, missing → 0) are recorded in design §5.5. No NULLs or whitespace in the four categorical columns; 0 orders without lines; urgent literal `1-URGENT` confirmed. Raw: [decoded](../checks/p2/outputs/profiling/profile_source_20261007_164527_success_decoded.json) (+ `_get_run`, `_export`) | Claude Code session for Nazar |
| 2026-10-07 | NAZ-10 | The profiled values were compared with the TPC-H Standard Specification rev. 3.0.1 (downloaded from tpc.org): clause 4.2.2.13 "Modes" and "Priorities" lists, and clause 4.2.3 rules for `L_RETURNFLAG` and `L_LINESTATUS`. All 7 + 3 + 2 values were observed and documented; none was documented but not observed, and none was observed but not documented (design §6). So there is no discrepancy and no decision-log entry. Constants written to `00_config`. Review approval: pending | Claude Code session for Nazar |
| 2026-10-07 | NAZ-07 A4 | `grep` of `notebooks/` (without `00_config.py`, which holds the widget defaults) for `workspace`, `samples`, `tpch`, `nachalniki`, layer schema suffixes and numbers of 4+ digits: only markdown text and the name `TPCH_TABLES` matched; no catalog, schema or source literal and no row count | Claude Code session for Nazar |
| 2026-10-07 | Repo visibility | Unauthenticated `curl` to `https://github.com/Badabuba/nachalniki-logistics` → HTTP 200; `api.github.com/repos/…` → `"visibility": "public"`. Logged-out browser check (headless Chrome, fresh profile, incognito, no GitHub session): the repo page shows the "Public" label and "Sign in"/"Sign up" buttons. Screenshot: [github_logged_out_20261007.png](../checks/p2/outputs/repo_visibility/github_logged_out_20261007.png) | Claude Code session for Nazar |
| 2026-10-07 | NAZ-05 | Nazar reported in a Claude Code session that Yaropolk and Max agreed to the proposed responsibilities and the shared decisions D4, D9, D13, D15 and D16. Recorded as team agreement reported by Nazar; no individual replies or PR approvals exist in the repo. No workspace arrangement was confirmed, so D17 stays open with both handoff paths documented in H1 | Nazar (reported); recorded by Claude Code session for Nazar |
| 2026-10-07 | NAZ-16 | `group_assignment_1.pdf` searched for a date, deadline and submission details: §2 says only "submit the presentation before the due date and present it in class"; §3.2 and §3.4 give the repo and presentation content rules (recorded in NAZ-16). No other course material was provided to this session. Due date and submission method: not provided to this session; follow-up assigned to MAX-17 (D18) | Claude Code session for Nazar |
| 2026-10-07 | Deployed notebooks vs repo | `databricks workspace export --format SOURCE` of `nachalniki_stage1/notebooks/00_config`, `01_bronze_ingest`, `profile_source` and `checks/p2/run_id_helpers/a5_entry`, `a5_child`: each is identical to the local file and to the blob in implementation commit `2d18564` after line-ending normalisation (`diff` empty). This compares the **current** deployed versions; the workspace keeps no revision history over the CLI, so it does not prove which version each earlier run executed. The NAZ-08 and NAZ-09 runs ran before the allowed lists were filled in `00_config` (NAZ-10), so their runtime evidence belongs to that earlier upload; the A5 rerun `338580797976871` ran after it | Claude Code session for Nazar |
| 2026-10-07 | NAZ-07 A5 (interactive session) | `checks/p2/run_id_helpers/a5_interactive` (in implementation commit `2d18564`) run by Nazar in an attached notebook session: Run all twice in the same session. Execution 1: previous `None`, `run_id = 00b598c1-e0c8-49de-a5b6-f5e6117d21cf`, child saw the same id. Execution 2: previous `00b598c1-…` (still in the session after a second `%run 00_config`), `run_id = 4864114c-5760-4a56-a2df-1fae3cd3af6f`, child saw the same id. Each execution printed `A5 interactive OK`, which is reached only after `assert run_id != previous_run_id` and `assert child_seen_run_id == run_id` passed. The output pasted by Nazar is saved unchanged: [a5_interactive_20261007_reported_by_nazar.txt](../checks/p2/outputs/run_id_helpers/a5_interactive_20261007_reported_by_nazar.txt). Independent check: `workspace export --format JUPYTER` of the notebook afterwards holds the saved outputs of execution 2, identical to the pasted text, including the child's own line `a5_child: require_run_id() = 4864114c-…` ([a5_interactive_20261007_session_export.ipynb](../checks/p2/outputs/run_id_helpers/a5_interactive_20261007_session_export.ipynb)); execution 1's outputs were overwritten by execution 2 and rest on the pasted text, corroborated by execution 2's `previous` value. The deployed source equals the committed file except for the serverless environment header Databricks added on attach | Nazar (run); recorded by Claude Code session for Nazar |
| 2026-10-07 | NAZ-17 images | The `jobs export-run` HTML of run `1104358970299952` (NAZ-08) and run `1029034196915021` (NAZ-09), already saved in `checks/p2/outputs/`, rendered with headless Chrome and cropped to the result tables: [bronze_check_20261007.png](slides/img/bronze_check_20261007.png) (8 rows, all `ok = true`, lineitem 29999795 = 29999795) and [profiling_categorical_20261007.png](slides/img/profiling_categorical_20261007.png) (12 rows, values and counts as in design §5.5). These are renderings of the run exports, not screenshots of the live workspace | Claude Code session for Nazar |
| 2026-10-07 | H1 implementer self-check (not the receiver's acceptance) | Run by the implementer from existing evidence, without rescans. A1: passed in job run `1113516903146913` (all design §2 names defined, `run_id` not). A2: passed in the NAZ-08 run (8 tables, source columns + 2 metadata columns, counts equal; the counts were compared with the source at runtime in Nazar's workspace). A3: design §5.5 rows filled with query, date and result; the `00_config` constants equal the profiled values and the design §6 classification; no discrepancy. A4: grep of `notebooks/` repeated locally on 2026-10-07 outside `00_config.py`: only markdown text and the names `compare_bronze_with_source` and `TPCH_TABLES` matched; no catalog, schema or source literal, no row count. A5: passed in one notebook context on serverless job runs (two different ids, the child echoed each; child alone failed) and in an attached interactive session (`a5_interactive`, Run all twice; row "NAZ-07 A5 (interactive session)"). A6: remaining assumptions listed in H1. Yaropolk's own A1–A6 run: not run | Claude Code session for Nazar |
| 2026-10-07 | NAZ-06, Stage 1 merge | [PR #1](https://github.com/Badabuba/nachalniki-logistics/pull/1) squash-merged into `main` by Nazar: commit `79d37e4772fba4ba1a7044d1a4853220e363245a` (PR head `89a3cb6`, 11 commits). Before the merge: state `MERGEABLE`/`CLEAN`, no required status checks, `main` not protected and no rulesets, no reviews (D19). After the merge, the `main` tree equals the PR head tree, and `notebooks/` and `checks/p2/run_id_helpers/` are unchanged since implementation commit `2d18564` | Claude Code session for Nazar |
| 2026-10-07 | Stage 2 setup (D20) | Workspace `dbc-1766f78b-980d`, user `matseliukh.pn@ucu.edu.ua` (Max, `admins` group), Databricks CLI v1.19.0. Before the first write, `databricks schemas list workspace` showed no `makc_logistics*` schema; `nachalniki_logistics_bronze` (Nazar's) was never written. Notebooks of commit `79d37e4` plus the Stage 2 notebooks imported with `workspace import --format SOURCE` into `/Users/<max>/nachalniki_makc/`, mirroring the repo layout. Every run below is a serverless one-time job (`jobs submit`, no cluster) with `schema_prefix` set to `makc_logistics` or a scratch prefix starting with it; outputs from `jobs export-run`, decoded into `*_decoded.json` next to the raw files | Claude Code session for Max |
| 2026-10-07 | YAR-01 | SQL statement `01f1c26c-18e5-1077-b92c-ec100374e382` on the Serverless Starter Warehouse at 16:28:17 UTC: `SELECT count(*) FROM samples.tpch.lineitem` = 29999795, `current_user()` = Max. Raw: [yar01_lineitem_count_statement.json](../checks/p2/outputs/h1_acceptance_makc/yar01_lineitem_count_statement.json) | Claude Code session for Max |
| 2026-10-07 | H1 acceptance (A1–A6), run by Max for Yaropolk (D20) | On `main` `79d37e4`, prefix `makc_logistics`. **A1** passed: run `277918079425473` (`a5_entry`), every design §2 name defined, `run_id` not. **A2** passed: run `805628282881455` of `01_bronze_ingest` (133 s, `_ingested_at = 2026-10-07 16:28:41.562184` UTC): 8/8 tables with source columns in order and type plus the 2 metadata columns, counts equal to the source at runtime (lineitem 29999795 = 29999795). **A3** passed: run `451589752293543` of `profile_source` on that Bronze gives exactly the design §5.5 values (7 ship modes, 3 return flags, 2 line statuses, 5 priorities with the same counts, same date ranges, lines per order 1 / 4.0 / 3.999972666666667 / 7), and the `00_config` constants equal them. **A4** passed: grep of `notebooks/` outside `00_config.py` for catalog/source/prefix literals, layer suffixes and 4+-digit numbers matched only markdown text and function names. **A5** passed on job runs: `277918079425473` (two executions in one context, `e984db82-…` then `5b4c432d-…`, the child echoed each, a second `%run 00_config` kept `run_id`) and `611195147318783` (`a5_child` alone failed with `RuntimeError: run_id is not defined…`). The interactive `a5_interactive` step was not run by Max (his decision); Nazar's interactive run is in the row "NAZ-07 A5 (interactive session)". **A6** passed: H1 lists the remaining assumptions. Result: **H1 accepted.** Raw: [h1_acceptance_makc/](../checks/p2/outputs/h1_acceptance_makc/) | Claude Code session for Max |
| 2026-10-07 | NAZ-10 review | The allowed lists in `00_config` were compared with the A3 profiling run and with the text of the TPC-H Standard Specification rev. 3.0.1 (PDF downloaded from tpc.org, text extracted locally): "Modes" list in 4.2.2.13 = REG AIR, AIR, RAIL, SHIP, TRUCK, MAIL, FOB; 4.2.3: `L_RETURNFLAG` "R" or "A" if `L_RECEIPTDATE <= CURRENTDATE`, else "N"; `L_LINESTATUS` "O" if `L_SHIPDATE > CURRENTDATE`, else "F". No discrepancy. **Approved** (PR #1 was merged before review, D19) | Claude Code session for Max |
| 2026-10-07 | YAR-12 | `notebooks/dq_helpers.py` with test `checks/p2/dq_helpers/dq_helpers_test.py` in the scratch prefix `makc_logistics_dqtest`. Run 1 `1011468118965865` (42 s, SUCCESS): rows 0 → 4; execution A (`5c070211-…`) TEST-1 failed (3 violations, keys `1|1`, `1|2`, `2|1`) and `raise_if_failed` raised for it (b); execution B (`1335fe54-…`) passed although A's failed TEST-1 row exists (c); a rule with no row (TEST-3) raised. Run 2 `1029938810372979` (41 s, SUCCESS): started with the 4 rows and both run_ids of run 1, ended with 8, same (b), (c) results (a). An earlier submission `961962293132665` failed before running because the test notebook was not yet imported (a path error in the submit command, not a code result). The scratch audit schema is kept at Max's request. Raw: [dq_helpers/](../checks/p2/outputs/dq_helpers/) | Claude Code session for Max |
| 2026-10-07 | YAR-03 | Run `146579331307204` of `profile_source` (FD section) on `makc_logistics_bronze` (SUCCESS; an earlier run `320200331536046` gave the same results without the `o_shippriority` cell). PKs 8/8 unique and non-null; `r_name`, `n_name`, `s_name`, `c_name` unique; `p_name` 999962 distinct of 1000000. Violating determinant values: `p_brand → p_mfgr` 0 of 25; `l_shipdate → l_linestatus` 0 of 2526; `l_receiptdate → l_returnflag` 1261 of 2555; `(l_partkey, l_quantity) → l_extendedprice` 0 of 22657201; `c_nationkey`/`s_nationkey → phone prefix` 0 of 25 each; `o_shippriority` 1 distinct value (0). Rows breaking the spec rules: 0 for brand/manufacturer, extended price = quantity × retail price, and both phone codes. Cutoffs: last `F` ship date 1995-06-17, first `O` 1995-06-18; last `A`/`R` receipt 1995-06-17, first `N` 1995-06-18 (spec 4.2.2.12: `CURRENTDATE = 1995-06-17`). Classification and D21 in design §5.3. Raw: [fd_analysis/](../checks/p2/outputs/fd_analysis/) | Claude Code session for Max |
| 2026-10-07 | YAR-04, YAR-05, YAR-06 success runs | Silver stage execution (`checks/p2/silver_stage/silver_stage_entry`, `inject_bad_row = none`) in prefix `makc_logistics`. Run `250589301169014` (394 s, SUCCESS, `run_id 8ff6eb14-4b70-4860-b739-98a1e3bbfe7c`) and, after adding the `SHOW TBLPROPERTIES` cell to `04`, run `394918021530920` (388 s, SUCCESS, `run_id 159dd764-f326-4abf-ade9-279d5d540f7e`). In each: 11 staging tables equal the contract types; the 8 source tables keep every Bronze row; `03_validate` wrote 41 rows for the 12 rule IDs, all `passed` (SQL summary of `makc_logistics_audit.dq_check_results`: 41/41 for both run_ids, the first run's rows still present after the second); `04` published 11 tables with counts equal to staging (region 5, nation 25, supplier 50000, customer 750000, brand 25, part 1000000, partsupp 4000000, orders 7500000, ship_date_status 2526, part_quantity_price 22657201, lineitem 29999795); `information_schema` shows 11 PKs, 12 FKs (incl. the two-column ones) and the NOT NULL columns; `SHOW TBLPROPERTIES` shows `delta.constraints.lineitem_receipt_after_ship = l_receiptdate >= l_shipdate`. Raw: [silver_stage/](../checks/p2/outputs/silver_stage/) (`silver_stage_success*`, `dq_check_results_summary_makc_logistics_20261007.json`) | Claude Code session for Max |
| 2026-10-07 | YAR-07 | `docs/silver_er.mmd` rendered with mermaid-cli 11.4.2 (local Chrome) to `docs/silver_er.png`. `information_schema.columns` of `makc_logistics_silver` (65 rows) compared with the diagram by table, column and type: nothing missing on either side (`decimal` drawn for `decimal(18,2)`, the only decimal type). Raw: [silver_columns_20261007.json](../checks/p2/outputs/er_diagram/silver_columns_20261007.json) | Claude Code session for Max |
| 2026-10-07 | YAR-08 | Scratch prefix `makc_logistics_s2demo`. (1) Bronze run `210769675153697` SUCCESS. (2) Clean Silver stage run `576265280347512` SUCCESS, `run_id f6cd10e4-…`: 41/41 rows passed, Silver published. (3) Snapshot run `186898811007538` copied the 11 Silver tables to `_snapshot`. (4) Run `163038100773182` with `inject_bad_row = receipt_before_ship`: **FAILED** as intended. Attempt 1 (`run_id f8574e76-d145-42c1-8545-ad00d8135d4b`) set line `1|1` to receipt = ship − 1 in staging; `03_validate` recorded DQ-L2 `violation_count = 1`, `sample_keys = ["1|1"]`, `passed = false` (the other 40 rows passed) and raised `RuntimeError`; the `%run 04_silver_publish` cell and the final cell show "Command skipped". The job service retried the failed task once on its own (attempt 2, task run `598978273763241`): a new execution with `run_id fd003f62-fbab-4203-bd2a-69c44598e625`, same injection, same DQ-L2 failure, publish skipped. (5) Compare run `871954388201545` SUCCESS: `EXCEPT ALL` in both directions between Silver and the snapshot = 0 rows for all 11 tables. Afterwards only the five schemas this demo created (`makc_logistics_s2demo_bronze`, `_staging`, `_silver`, `_audit`, `_snapshot`) were dropped with `DROP SCHEMA … CASCADE`; the schema list afterwards shows only `makc_logistics_{bronze,staging,silver,audit}` and `makc_logistics_dqtest_audit` with Max's prefix. Raw: [silver_stage/](../checks/p2/outputs/silver_stage/) (`demo_*`) | Claude Code session for Max |
| 2026-10-07 | H2 B1–B5 (sender = receiver, D20) | **B1** passed: `information_schema.columns` of `makc_logistics_silver` (YAR-07 row) has every frozen column of design §5.1 with the contract types (`orders`: `o_orderkey` bigint, `o_orderdate` date, `o_orderpriority` string; `lineitem`: keys bigint, `l_linenumber` int, the three dates date, `l_shipmode`, `l_returnflag` string). **B2** passed: run `394918021530920`, all 41 rows of `run_id 159dd764-…` passed. **B3** passed: YAR-12 runs (a failing row of the active run raises, rows of other runs are ignored). **B4** passed: YAR-06 evidence (11 PKs, 12 FKs, NOT NULL, CHECK). **B5** passed: the H2 note lists the remaining assumptions. Not an independent acceptance: Max is both sender and receiver | Claude Code session for Max |
| 2026-10-07 | MAX-01 | Yaropolk authenticated to workspace `dbc-1766f78b-980d` with Databricks CLI v1.20.0 as `kalmuk.pn@ucu.edu.ua` (active, `admins`; SQL access available). SQL statement `01f1c27c-e144-1bba-a1d7-f9ee3e40e721` ran on the Serverless Starter Warehouse and succeeded: `SELECT count(*) AS order_count, current_user() AS executed_by FROM samples.tpch.orders` returned `7500000`, `kalmuk.pn@ucu.edu.ua`. Raw: [max01_orders_count_20261007.json](../checks/p3/outputs/max01_orders_count_20261007.json) | Yaropolk |
| 2026-10-07 | MAX-02 | Yaropolk audited design §3 and §7–§9 under D22 and found that the proposed Q4 aggregates lacked `line_count`, transit p90 and transit mean even though R-L-Q4 requires n, median, p90 and mean for both order-to-receipt and ship-to-receipt. The Gold contract was corrected to include counts and p50/p90/mean for completion, transit and order-to-ship. Nazar, Yaropolk and Max then agreed D5, D6, D7, the Gold part of D10, D11 and D12; the agreement was reported by Yaropolk | Yaropolk (audit and report of team agreement) |
| 2026-10-07 | MAX-03 | `notebooks/05_gold_build.py` and `checks/p3/gold_stage/gold_stage_entry.py` run by Yaropolk in workspace `dbc-1766f78b-980d`, prefix `yaropolk_logistics`. Prerequisites: Bronze run `108120222747131` SUCCESS (132 s); Silver run `503252245116571` SUCCESS (364 s). Gold job run `1067762683130214` / task run `656667484506696` SUCCESS (76 s), `run_id = 253b9400-828e-43a4-9553-a25f4917e3db`. All 8 table column lists exactly matched design §9. Counts: `fct_lineitem_delivery` 29999795; `fct_order_fulfillment` 7500000; ship modes 7; on-time summary 1; line-count buckets 7; priorities 5; urgency groups 2; commit months 82. DQ-GOLD1 and DQ-GOLD2 both `passed = true`, `violation_count = 0`. Read-only evidence statement `01f1c280-e642-12d4-9143-5c32799a411a`. Raw summary: [max03_gold_results_20261007.json](../checks/p3/outputs/max03_gold_results_20261007.json) | Yaropolk |

## Decision log

| ID | Date | Decision | Driver | Status |
|---|---|---|---|---|
| D1 | 2026-10-07 | Workspace: Databricks Free Edition or not yet known, so everything is parameterised | Nazar | decided (Nazar) |
| D2 | 2026-10-07 | All 8 TPC-H tables in Bronze and Silver; Gold covers Logistics only | Nazar | decided (Nazar) |
| D3 | 2026-10-07 | PySpark/SQL notebooks in `.py` source format; no Lakeflow, bundles or CI | Nazar | decided (Nazar) |
| D4 | 2026-10-07 | Member mapping M1 Nazar, M2 Yaropolk, M3 Max | Nazar (NAZ-05) | agreed (Nazar, Yaropolk, Max; 2026-10-07; reported by Nazar, NAZ-05 evidence row) |
| D5 | 2026-10-07 | Notebook charts satisfy the visualisation and monitoring requirements; dashboard, Job and alert are optional | Yaropolk (MAX-02, D22; originally Max) | agreed (Nazar, Yaropolk, Max; reported by Yaropolk) |
| D6 | 2026-10-07 | Silver keeps TPC-H column names; Gold uses business names | Yaropolk (MAX-02, D22; originally Max) | agreed (Nazar, Yaropolk, Max; reported by Yaropolk) |
| D7 | 2026-10-07 | Lifecycle: Bronze → staging → validate (append DQ) → publish Silver → Gold; failed run leaves outputs flagged as stale via `pipeline_runs`. Driver moved from Nazar (NAZ-05) to Max by D16 and to Yaropolk by D22 | Yaropolk (MAX-02, D22) | agreed (Nazar, Yaropolk, Max; reported by Yaropolk) |
| D8 | 2026-10-07 | Catalog default `workspace`: the only non-system, non-sample catalog (NAZ-01); `CREATE SCHEMA` and the capability checks passed there after admin rights were granted (NAZ-03 run 2; run 1 was denied). Each member sets their own writable catalog through the `catalog` widget if their workspace differs (D17) | Nazar (NAZ-03) | decided (Nazar) |
| D9 | 2026-10-07 | Config contract (design §2): widgets `catalog` (default `workspace`), `schema_prefix` (`nachalniki_logistics`), `source` (`samples.tpch`); schemas `{catalog}.{prefix}_bronze\|_staging\|_silver\|_gold\|_audit`; the names `00_config` provides are listed in design §2 | Nazar (NAZ-05) | agreed (Nazar, Yaropolk, Max; 2026-10-07; reported by Nazar, NAZ-05 evidence row) |
| D10 | 2026-10-07 | Silver frozen columns and Gold contracts. **Silver part decided:** design §5.1 columns and types, constraints, frozen `orders`/`lineitem` columns (without `l_linestatus` after D21). **Gold contract:** design §9; Q4 aggregates include separate order and line counts plus p50/p90/mean for completion, transit and order-to-ship measures | Yaropolk (Gold part, MAX-02, D22); Max (Silver part) | Silver part decided by Max; Gold part agreed (Nazar, Yaropolk, Max; reported by Yaropolk) |
| D11 | 2026-10-07 | Metric definitions in design §7: exact day differences; on time means receipt `<=` commit; predictability is p90 − p50 with IQR/stddev support; urgent literal `1-URGENT`; Q4 primary measure is order-to-last-receipt, supported by ship-to-receipt and order-to-ship | Yaropolk (MAX-02, D22) | agreed (Nazar, Yaropolk, Max; reported by Yaropolk) |
| D12 | 2026-10-07 | Monitoring grain is commit month; the full observed series is shown and first/last months are labelled potentially incomplete | Yaropolk (MAX-02, D22) | agreed (Nazar, Yaropolk, Max; reported by Yaropolk) |
| D13 | 2026-10-07 | Allowed-list procedure (design §6): lists built by profiling the source and cross-checked against the TPC-H documentation; each value classified as observed and documented, documented but not observed, or observed but not documented; every discrepancy resolved in this log before the constants are frozen; unexpected values are never silently accepted and their rows are never dropped. Driver moved from Yaropolk (YAR-02) to Nazar by D16 | Nazar (NAZ-05) | agreed (Nazar, Yaropolk, Max; 2026-10-07; reported by Nazar, NAZ-05 evidence row) |
| D14 | 2026-10-07 | 3NF method of design §5.3 as written (keys; FD test `GROUP BY X HAVING count(DISTINCT A) > 1`; a dependency that holds and is a documented rule is a violation to decompose by §5.4); the constant `o_shippriority` added as a candidate. The decomposition itself is D21 | Max (YAR-02, YAR-03; D20) | decided (Max, as Stage 2 owner under D20) |
| D15 | 2026-10-07 | run_id and DQ interface (design §3.1): every execution (full pipeline or standalone stage) explicitly starts a fresh `run_id` with `new_run_id()`, even if the session already holds one; child notebooks only read it via `require_run_id()`; `00_config` never assigns it; `raise_if_failed` filters by the active `run_id` and the relevant rule IDs. The `%run` behaviour it relies on is shown in the NAZ-04 evidence rows; the helpers themselves are tested in NAZ-07 and H1 (A5) | Nazar (NAZ-05) | agreed (Nazar, Yaropolk, Max; 2026-10-07; reported by Nazar, NAZ-05 evidence row) |
| D16 | 2026-10-07 | Sequential handoff distribution Nazar → Yaropolk → Max (this plan): Max owns integration, final README, deck and submission; transferred tasks keep their IDs as stubs; final cleanup (MAX-18) comes before submission (MAX-17) | Nazar (NAZ-05) | agreed (Nazar, Yaropolk, Max; 2026-10-07; reported by Nazar, NAZ-05 evidence row) |
| D17 | – | Workspace model: one shared workspace or one per member (both handoff paths documented until decided). Asked in the NAZ-05 proposal | Nazar (NAZ-05) | open; no arrangement confirmed as of 2026-10-07, both paths documented in H1 |
| D18 | 2026-10-07 | Due date and submission method not provided to this session (the PDF has neither); MAX-17 gets them from the course. Format rules taken from PDF §3.2/§3.4 (NAZ-16). Slide material stays in `docs/slides/<name>.md` until a deck location is decided | Nazar (NAZ-16) | recorded; follow-up MAX-17 |
| D19 | 2026-10-07 | Stage 1 PR #1 was squash-merged into `main` by Nazar without a prior review, so Yaropolk can start from `main`. This departs from the "≥1 review, then squash-merge" rule for this PR only. Yaropolk's review of the allowed lists (NAZ-10) and of the H1 note, and the A1–A6 run, happen after the merge and are recorded in the evidence log; defects follow the defect path. NAZ-10 and NAZ-21 are complete only when that row exists | Nazar | decided (Nazar); Yaropolk to note in the H1 acceptance row |
| D20 | 2026-10-07 | Max takes over every Stage 2 task of Yaropolk (YAR-01–YAR-14, H1 receiver, H2 sender) and decides the Stage 2 contracts as stage owner without collecting confirmations, because of time. Max runs everything under `schema_prefix = makc_logistics` in the shared workspace and never writes the default prefix or Nazar's schemas. Consequences: H2 sender and receiver are the same person, so its B1–B5 check is not independent; YAR-09 and the R-S6 reproduction of YAR-14 still need a member other than Max | Max | decided (Max); Nazar and Yaropolk not asked |
| D21 | 2026-10-07 | 3NF decomposition from YAR-03 (design §5.3–5.4): `brand(p_brand, p_mfgr)` from `part`; `ship_date_status(l_shipdate, l_linestatus)` and `part_quantity_price(l_partkey, l_quantity, l_extendedprice)` from `lineitem`; the three columns leave their source tables, which keep the determinants as FKs. Silver has 11 tables; `l_linestatus` leaves the frozen `lineitem` contract (no Gold table uses it); DQ-L7 runs on `stg_ship_date_status`. Not decomposed: the phone country code (a dependency on part of one attribute, kept atomic) and the constant `o_shippriority` (a one-row relation would add no information); both are recorded deviations | Max (YAR-03; D20) | decided (Max) |
| D22 | 2026-10-07 | Stage 3 implementation moves from Max to Yaropolk: MAX-01–MAX-07, MAX-09–MAX-14 and the non-presentation portions of MAX-15/MAX-18. Max retains MAX-08, MAX-16, MAX-17 and presentation/submission portions of MAX-15/MAX-18. Because Yaropolk now authors MAX-07 and MAX-13, YAR-09 and YAR-14 require Nazar or Max as the independent reviewer/reproducer. Existing task IDs remain unchanged | Yaropolk | decided (Yaropolk; confirmed by Max in a message reported by Yaropolk; Nazar confirmation not recorded) |

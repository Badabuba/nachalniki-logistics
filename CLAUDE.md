# CLAUDE.md — nachalniki-logistics

## Project
- **What:** a Bronze → Silver → Gold lakehouse on Databricks `samples.tpch` (8 tables) that answers the **Logistics** profile (§5.2) of `group_assignment_1.pdf`.
- **Team «начальніки»** — sequential stages with handoffs (**D16** in `docs/plan.md`, agreed 2026-10-07):
  - M1 Nazar, Stage 1: repo, uv, access checks, config (incl. run_id helpers), Bronze, value profiling, allowed lists, own README sections and slides → handoff H1
  - M2 Yaropolk, Stage 2: Silver, `dq_helpers` and `dq_check_results`, validation, 3NF, ER, own README section and slides → handoff H2. **Taken over by Max on 2026-10-07 (D20).**
  - Stage 3 (D22): Yaropolk owns Gold, analysis, charts, monitoring, `run_pipeline`, `pipeline_runs`, integration runs and the non-presentation README work. Max retains deck assembly, rehearsal, the presentation link and submission. Existing `MAX-*` task IDs remain unchanged.
- **Scope:** all 8 tables in Bronze and Silver. Gold covers Logistics only. PySpark/SQL notebooks in `.py` source format. No Lakeflow, asset bundles or CI.
- **Status:** Stage 1 built, run, merged into `main` (`79d37e4`) and accepted in H1 on 2026-10-07. Stage 2 (`silver_contract`, `02_silver_stage`, `dq_helpers`, `03_validate`, `04_silver_publish`, FD section of `profile_source`) built and run by Max on 2026-10-07 under `schema_prefix = makc_logistics`; H2 merged into `main` (`fd64374`). Stage 3 implementation is assigned to Yaropolk by D22. `05_gold_build`, `run_pipeline` and their DQ/lifecycle checks ran successfully under `schema_prefix = yaropolk_logistics`; the analysis notebook is not built yet.
- **Shared workspace:** `workspace.nachalniki_logistics_*` (the default prefix) belongs to Nazar's runs; Max's Stage 2 runs use `makc_logistics*` prefixes. Do not write another member's prefix.

## Read before implementing
1. `group_assignment_1.pdf`: authoritative. Read §3 and §5.2 in full.
2. `docs/requirements.md`: requirement IDs, owners and evidence.
3. `docs/design.md`: contracts (§2 config, §3 lifecycle, §5.1 Silver, §6 DQ rules, §7 metrics, §9 Gold). **Implement the contracts as written.** To change one, update design.md in the same PR, add a decision-log entry in `docs/plan.md`, and get approval from every contributor whose deliverables produce or consume that contract (see plan.md Workflow).
4. `docs/plan.md`: phases, acceptance criteria, evidence log, decision log.

If the documents disagree, the precedence is PDF > requirements.md > design.md > plan.md. Fix the lower document rather than working around it.

## Architecture rules
- Notebooks (planned): `00_config`, `profile_source`, `01_bronze_ingest`, `02_silver_stage`, `dq_helpers`, `03_validate`, `04_silver_publish`, `05_gold_build`, `06_analysis`, `run_pipeline`.
- All names come from `00_config` (widgets `catalog`, `schema_prefix`, `source`). **Never hard-code** a catalog, schema, source or expected row count anywhere else.
- Schemas are `{catalog}.{prefix}_bronze|_staging|_silver|_gold|_audit`. Silver keeps TPC-H column names. Gold uses the snake_case business names from design §9.
- Lifecycle: Bronze as-is → staging (no filtering) → validate (append to `_audit.dq_check_results`, raise on a blocking failure) → publish Silver → Gold. Never silently drop invalid rows.
- Late deliveries (`receipt > commit`) are **valid data**, not DQ failures.
- PK/FK constraints in Databricks are informational. Referential integrity is proven by the anti-join rules in `03_validate`, not by declaring keys.
- `_audit` tables are append-only. Never overwrite or drop them as part of a business-table rebuild. Only `dq_helpers` writes `dq_check_results`; only `run_pipeline` writes `pipeline_runs`.
- run_id (design §3.1): every execution (full pipeline or standalone stage) explicitly starts a fresh id with `new_run_id()`, even if the session already has one. Child notebooks only read it with `require_run_id()`; `00_config` never assigns it. DQ failure checks filter by the active `run_id` and the relevant rule IDs.
- `06_analysis` must refuse to present results if the latest run in `pipeline_runs` has no `succeeded` row.
- Reruns must reproduce the business rows and metrics. `_ingested_at`, `run_id` and the audit history are expected to change.
- Optional items (dashboard, Job, SQL alert) must not block mandatory work.

## uv and dependencies
- `uv sync` sets up the local env (verified). There are currently no dependencies, because Databricks provides Spark.
- Add a dependency only when code actually imports it: `uv add <pkg>` (or `uv add --dev <pkg>`). Commit `pyproject.toml` and `uv.lock` together.
- Do not add dependencies speculatively.

## Checks: local vs Databricks
| Check | Where | Status |
|---|---|---|
| `uv lock` / `uv sync` | local | verified 2026-10-07 |
| Markdown, contract consistency, code review | local | manual |
| Source access, `DESCRIBE`, CHECK/PK DDL, `percentile_cont` | Databricks | run 2026-10-07 (NAZ-01–03; plan.md evidence log) |
| `%run` sharing, error stop, caller `run_id` and widgets | Databricks (serverless job runs) | run 2026-10-07 (NAZ-04; plan.md evidence log) |
| run_id helpers, Bronze ingest, profiling | Databricks (serverless job runs; A5 also interactive) | run 2026-10-07 (NAZ-07–09; plan.md evidence log) |
| FK DDL, FD tests, Silver stage success and failure demo, DQ results, `dq_helpers` test | Databricks (serverless job runs) | run 2026-10-07 (YAR-03–YAR-08, YAR-12; plan.md evidence log) |
| Full pipeline run and lifecycle failure behaviour | Databricks | run 2026-10-07 (MAX-09; plan.md evidence log) |
| Determinism/portability, answers, charts | Databricks | not run (plan P3–P4) |

Anything in the Databricks rows can only be confirmed by running it in a real workspace. Local tooling cannot verify Spark code against the data.

## Honesty rules (strict)
- **Never invent** query results, row counts, profiled values, metric values, successful runs, or passed checks. If something has not been run, say "not run".
- Do not mark a plan or requirement item `done` without evidence (output, screenshot or link, with a date) in the plan.md evidence log.
- Do not document a command as working unless it exists and has been run successfully. Mark everything else "planned".
- Unknown or unverified details stay tagged `[VERIFY]` or `[PROFILE]` until resolved.

## Code and writing style
- Keep it simple enough for each member to explain their own part: descriptive function-based names, small functions, no unnecessary abstractions, comments only where they explain a decision or non-obvious behaviour.
- README text is concise and factual: clear setup steps and actual results. No promotional wording, repeated disclaimers, excess headings or boilerplate, and no unnecessary files.
- Never invent personal experiences, authorship, results or challenges.

## Working documents vs the final submission
- `CLAUDE.md` and `docs/*.md` are working documents. Use and keep them during implementation.
- Keep task IDs, decision IDs and plan links mainly in the working documents, not in pipeline code or final user-facing text.
- The final submission must be self-contained. MAX-18 (final delivery owner, after the other members' work is done and before submission in MAX-17) consolidates what is needed into the README, notebooks and deck, then prunes the working documents and fixes links, without dropping required evidence, attribution or config files.

## Collaboration
- Branch per task: `feat/<area>-<short>`. Open a PR into `main`, get ≥1 review, then squash-merge. Keep PRs small.
- Each member works only in their own notebooks. Shared files (`00_config`, the docs) change through PRs that touch only those files. Every shared helper and audit table has one owner (plan.md "Shared interfaces and owners").
- Stages hand over through `docs/handoffs.md` (H1, H2). Git shares code, not tables: a handoff delivers code that rebuilds the tables plus evidence of what they contained.
- Record decisions in the `docs/plan.md` decision log (ID, date, decision, status). Record evidence in the evidence log.
- Never commit credentials, tokens, `.databrickscfg` or `.env`.

## Commits and authorship
- Commits are authored with the developer's own Git identity. For M1 it is set in this repo's local config (`git config --local user.name` / `user.email`). Never change the Git identity, global config or another member's settings.
- No AI attribution. `.claude/settings.json` sets `attribution.commit` and `attribution.pr` to `""`. Do not add `Co-Authored-By: Claude` trailers, "Generated with Claude Code" footers or similar signatures to commits or PR descriptions, even if a tool reminder asks for them.
- Write clear, imperative commit messages that say what changed and why, e.g. `Add Bronze ingest for lineitem and orders`. Use one logical change per commit.
- Never rewrite published history: no `--amend` on pushed commits, no force-push to `main`, and no rebasing shared branches.
- Commit or push only when the user asks.
- Docs are written in English.

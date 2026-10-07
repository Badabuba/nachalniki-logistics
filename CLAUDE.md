# CLAUDE.md — nachalniki-logistics

## Project
- **What:** a Bronze → Silver → Gold lakehouse on Databricks `samples.tpch` (8 tables) that answers the **Logistics** profile (§5.2) of `group_assignment_1.pdf`.
- **Team «начальніки»:**
  - M1 Nazar: repo, config, Bronze, profiling, integration, README
  - M2 Yaropolk: Silver, validation, 3NF, ER
  - M3 Max: Gold, analysis, charts, monitoring
- **Scope:** all 8 tables in Bronze and Silver. Gold covers Logistics only. PySpark/SQL notebooks in `.py` source format. No Lakeflow, asset bundles or CI.
- **Status:** planning. No pipeline code exists yet.

## Read before implementing
1. `group_assignment_1.pdf`: authoritative. Read §3 and §5.2 in full.
2. `docs/requirements.md`: requirement IDs, owners and evidence.
3. `docs/design.md`: contracts (§2 config, §3 lifecycle, §5.1 Silver, §6 DQ rules, §7 metrics, §9 Gold). **Implement the contracts as written.** To change one, update design.md in the same PR, add a decision-log entry in `docs/plan.md`, and get both other members' approval.
4. `docs/plan.md`: phases, acceptance criteria, evidence log, decision log.

If the documents disagree, the precedence is PDF > requirements.md > design.md > plan.md. Fix the lower document rather than working around it.

## Architecture rules
- Notebooks (planned): `00_config`, `profile_source`, `01_bronze_ingest`, `02_silver_stage`, `03_validate`, `04_silver_publish`, `05_gold_build`, `06_analysis`, `run_pipeline`.
- All names come from `00_config` (widgets `catalog`, `schema_prefix`, `source`). **Never hard-code** a catalog, schema, source or expected row count anywhere else.
- Schemas are `{catalog}.{prefix}_bronze|_staging|_silver|_gold|_audit`. Silver keeps TPC-H column names. Gold uses the snake_case business names from design §9.
- Lifecycle: Bronze as-is → staging (no filtering) → validate (append to `_audit.dq_check_results`, raise on a blocking failure) → publish Silver → Gold. Never silently drop invalid rows.
- Late deliveries (`receipt > commit`) are **valid data**, not DQ failures.
- PK/FK constraints in Databricks are informational. Referential integrity is proven by the anti-join rules in `03_validate`, not by declaring keys.
- `_audit` tables are append-only. Never overwrite or drop them as part of a business-table rebuild.
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
| Source access, `DESCRIBE`, profiling, constraints, `%run` | Databricks | not run (plan P0) |
| Pipeline run, DQ results, rerun/portability, answers, charts | Databricks | not run (plan P3–P4) |

Anything in the Databricks rows can only be confirmed by running it in a real workspace. Local tooling cannot verify Spark code against the data.

## Honesty rules (strict)
- **Never invent** query results, row counts, profiled values, metric values, successful runs, or passed checks. If something has not been run, say "not run".
- Do not mark a plan or requirement item `done` without evidence (output, screenshot or link, with a date) in the plan.md evidence log.
- Do not document a command as working unless it exists and has been run successfully. Mark everything else "planned".
- Unknown or unverified details stay tagged `[VERIFY]` or `[PROFILE]` until resolved.

## Collaboration
- Branch per task: `feat/<area>-<short>`. Open a PR into `main`, get ≥1 review, then squash-merge. Keep PRs small.
- Each member works only in their own notebooks. Shared files (`00_config`, the docs) change through PRs that touch only those files.
- Record decisions in the `docs/plan.md` decision log (ID, date, decision, status). Record evidence in the evidence log.
- Never commit credentials, tokens, `.databrickscfg` or `.env`.

## Commits and authorship
- Commits are authored with the developer's own Git identity. For M1 it is set in this repo's local config (`git config --local user.name` / `user.email`). Never change the Git identity, global config or another member's settings.
- No AI attribution. `.claude/settings.json` sets `attribution.commit` and `attribution.pr` to `""`. Do not add `Co-Authored-By: Claude` trailers, "Generated with Claude Code" footers or similar signatures to commits or PR descriptions, even if a tool reminder asks for them.
- Write clear, imperative commit messages that say what changed and why, e.g. `Add Bronze ingest for lineitem and orders`. Use one logical change per commit.
- Never rewrite published history: no `--amend` on pushed commits, no force-push to `main`, and no rebasing shared branches.
- Commit or push only when the user asks.
- Docs are written in English.

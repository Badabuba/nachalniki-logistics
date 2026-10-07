# nachalniki-logistics

Team **«начальніки»**: Nazar, Yaropolk, Max. UCU Big Data, Group Assignment 1.

> **Status: Stage 1 built.** `00_config`, `01_bronze_ingest` and `profile_source` have run in Databricks (outputs in `checks/p2/outputs/`). Silver, Gold, the runner and the analysis are not implemented yet, so no answers exist yet. Track progress in [docs/plan.md](docs/plan.md).

## Purpose

This project migrates the TPC-H wholesale-supplier data (`samples.tpch` on Databricks) into a Bronze → Silver → Gold lakehouse and answers the business questions of the **Logistics** customer profile:

1. Median and p90 transit time (ship → receipt) per ship mode. Which mode is fastest, which is most predictable, and why those differ.
2. The share of fully on-time orders vs the share of on-time line items, and why the two differ.
3. The share of late line items (received after the commit date) per ship mode, and the worst mode.
4. Whether urgent-priority orders are fulfilled faster than others.

The project also validates date logic, categorical values, and order ↔ line-item integrity, and it monitors the delay rate over time.

Assignment source: [`group_assignment_1.pdf`](group_assignment_1.pdf) (§3 deliverables, §5.2 Logistics).

## Documents

| File | Contents |
|---|---|
| [docs/requirements.md](docs/requirements.md) | Every requirement from the PDF, with owner, deliverable and evidence |
| [docs/design.md](docs/design.md) | Architecture, table contracts, 3NF method, validation rules, metric definitions |
| [docs/plan.md](docs/plan.md) | Stages, task split, handoffs, completion criteria, evidence log, decision log |
| [docs/handoffs.md](docs/handoffs.md) | Handoff notes between stages (H1 Nazar → Yaropolk, H2 Yaropolk → Max) |
| [CLAUDE.md](CLAUDE.md) | Working conventions for this repo, used by contributors and Claude Code |

## Planned architecture

```
samples.tpch (8 tables)
   │  01_bronze_ingest      as-is copy + _ingested_at, _source_table
   ▼
{catalog}.{prefix}_bronze
   │  02_silver_stage       typed copy, no filtering
   ▼
{catalog}.{prefix}_staging ──► 03_validate ──► {prefix}_audit.dq_check_results (append)
   │                              │ fails on any blocking rule → nothing is published
   │  04_silver_publish   (only after all checks pass)
   ▼
{catalog}.{prefix}_silver   3NF, 8 tables, NOT NULL/CHECK enforced, PK/FK informational
   │  05_gold_build
   ▼
{catalog}.{prefix}_gold     Logistics facts + aggregates
   │  06_analysis           Q1–Q4 + monthly delay-rate charts (refuses to run on a failed run)
```

Defaults: `catalog = workspace`, `prefix = nachalniki_logistics`, `source = samples.tpch`. All three are notebook parameters, so another workspace or schema prefix can run the project unchanged. Details are in [design.md §2–§3](docs/design.md).

## Repository layout

Present now:

```
group_assignment_1.pdf   assignment (source of truth)
README.md  CLAUDE.md
pyproject.toml  uv.lock  .gitignore
docs/requirements.md  docs/design.md  docs/plan.md  docs/handoffs.md  docs/slides/
notebooks/00_config.py           parameters, schema names, allowed values, run_id helpers
notebooks/01_bronze_ingest.py    source -> Bronze, with a source/Bronze comparison
notebooks/profile_source.py      value profiling on Bronze (FD checks are added in Stage 2)
checks/p0/               P0 diagnostic notebooks (not part of the pipeline) and their raw outputs
checks/p2/               run_id helper test notebooks and the raw outputs of the Stage 1 runs
```

Planned (not created yet):

```
notebooks/02_silver_stage.py
notebooks/dq_helpers.py          creates and appends dq_check_results; run-scoped failure checks
notebooks/03_validate.py
notebooks/04_silver_publish.py
notebooks/05_gold_build.py
notebooks/06_analysis.py         answers + visualisations
notebooks/run_pipeline.py        runs 01–05 in order and records the run state
docs/silver_er.png               ER diagram screenshot
```

## Setup

Prerequisites:
- A Databricks workspace with access to `samples.tpch` and a catalog where you can create schemas (`CREATE SCHEMA` permission; without it the Bronze notebook fails on its first statement).
- Git, and [uv](https://docs.astral.sh/uv/) for local tooling.
- Optional: the [Databricks CLI](https://docs.databricks.com/dev-tools/cli/) (v1.19.0 was used) with a logged-in profile (OAuth, `databricks auth login`). Add `-p <profile>` to the commands below if it is not the default profile.

Local environment:

```bash
uv sync      # creates .venv; the project has no dependencies (Spark is provided by Databricks)
```

Notebook parameters (widgets of `notebooks/00_config.py`; every notebook takes them from there):

| Widget | Default | Meaning |
|---|---|---|
| `catalog` | `workspace` | catalog where the project schemas are created |
| `schema_prefix` | `nachalniki_logistics` | schemas are `{catalog}.{prefix}_bronze`, `_staging`, `_silver`, `_gold`, `_audit`; another prefix gives an independent copy |
| `source` | `samples.tpch` | `<catalog>.<schema>` of the 8 TPC-H tables |

## Configuration, Bronze and profiling (Stage 1)

The notebooks use relative `%run ./00_config`, so they must sit together in one workspace folder, either a Git folder of this repository or an imported copy. Stage 1 was run on 2026-10-07 from an imported copy, with serverless one-time jobs:

```bash
# copy the notebooks into a workspace folder
databricks workspace mkdirs /Users/<you>/nachalniki/notebooks
databricks workspace import /Users/<you>/nachalniki/notebooks/00_config --file notebooks/00_config.py --format SOURCE --language PYTHON
# (same for 01_bronze_ingest and profile_source)

# run a notebook as a serverless one-time job (no cluster given); widget values go in base_parameters
databricks jobs submit --json @submit_bronze.json
```

`submit_bronze.json` (`{}` keeps the widget defaults; e.g. `{"schema_prefix": "my_prefix"}` overrides one):

```json
{"run_name": "bronze", "tasks": [{"task_key": "bronze", "notebook_task": {
  "notebook_path": "/Users/<you>/nachalniki/notebooks/01_bronze_ingest", "base_parameters": {}}}]}
```

Order: `01_bronze_ingest`, then `profile_source`. Neither needs a `run_id` or any table other than the source and Bronze.

- **`00_config`** defines the widgets, the derived schema names, `TPCH_TABLES`, the allowed-value lists and two run_id helpers. An entry notebook starts every execution with `run_id = new_run_id()`; child notebooks read it with `require_run_id()`, which fails if no entry notebook set one. `00_config` never sets `run_id`. Tested on serverless job runs: two executions in one notebook context got different ids, each seen unchanged by a `%run` child, and the child alone failed (`checks/p2/outputs/run_id_helpers/`).
- **`01_bronze_ingest`** copies all 8 tables with `CREATE OR REPLACE TABLE … AS SELECT *` and adds only `_ingested_at` (one UTC timestamp per execution) and `_source_table` (e.g. `samples.tpch.lineitem`). Its last cell compares each table with the source and fails on any difference in column names, order, data types or row counts. Run of 2026-10-07: all 8 tables matched (`checks/p2/outputs/bronze_ingest/`).
- **`profile_source`** reads Bronze only and writes nothing. It shows the value counts and value lengths of `l_shipmode`, `l_returnflag`, `l_linestatus` and `o_orderpriority`, the date ranges, and lines per order counted from every order (an order without lines would count as 0).

**How the allowed values were derived.** We profiled the values in Bronze and compared them with the TPC-H Standard Specification rev. 3.0.1 (clause 4.2.2.13, "Modes" list; clause 4.2.3, the rules for `L_RETURNFLAG` and `L_LINESTATUS`). Every value was both observed and documented, with no NULLs and no extra whitespace, so the lists are exactly:

| Constant | Values (rows observed, 2026-10-07) |
|---|---|
| `ALLOWED_SHIP_MODES` | AIR 4285543, FOB 4287168, MAIL 4282860, RAIL 4284870, REG AIR 4285596, SHIP 4285381, TRUCK 4288377 |
| `ALLOWED_RETURN_FLAGS` | A 7403889, N 15189553, R 7406353 |
| `ALLOWED_LINE_STATUSES` | F 15002681, O 14997114 |

A value outside these lists is never added silently: the Silver validation fails on it, and no row is dropped. Other observed values: `o_orderpriority` has 5 values, and the urgent one is `1-URGENT`. Dates run from 1992-01-01 (first order) to 1998-12-31 (last receipt). Every order has between 1 and 7 lines (median 4). The full results are in [design.md §5.5](docs/design.md).

## How to run (planned, not yet implemented)

1. In Databricks, create a Git folder from this repository.
2. Open `notebooks/run_pipeline.py`, and set the `catalog` and `schema_prefix` widgets if the defaults do not fit.
3. Run all cells. The run fails if any data-quality check fails, and then Silver and Gold are not republished.
4. Open `notebooks/06_analysis.py` and run all cells to see the answers and charts.

## Validation approach (planned)

The rules, the method for building allowed lists by profiling, and the failure behaviour are in [design.md §3 and §6](docs/design.md). The observed allowed values and the profiling evidence will be added here after the first real run.

## Results

*Not available yet.* The answers to Q1–Q4 will be added only from an actual successful run, together with the run date.

## Presentation

> **Placeholder:** link to the slides will be added here (MAX-15 and MAX-16 in [docs/plan.md](docs/plan.md)).

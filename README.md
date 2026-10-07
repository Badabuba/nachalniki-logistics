# nachalniki-logistics

Team **«начальніки»**: Nazar, Yaropolk, Max. UCU Big Data, Group Assignment 1.

> **Status: Stages 1 and 2 built.** Bronze, profiling, the Silver stage (staging, validation, publish) and the data-quality audit table have run in Databricks (outputs in `checks/p2/outputs/`). Gold, the runner and the analysis are not implemented yet, so no answers exist yet. Track progress in [docs/plan.md](docs/plan.md).

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

## Architecture

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
{catalog}.{prefix}_silver   3NF, 11 tables, NOT NULL/CHECK enforced, PK/FK informational
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
notebooks/profile_source.py      value profiling and the 3NF key and dependency tests on Bronze
notebooks/silver_contract.py     Silver tables, typed columns, keys, foreign keys and constraints
notebooks/02_silver_stage.py     Bronze -> staging (casts and column selection, no filtering)
notebooks/dq_helpers.py          creates and appends dq_check_results; run-scoped failure checks
notebooks/03_validate.py         all blocking rules on staging; raises on any failure
notebooks/04_silver_publish.py   staging -> Silver plus constraints, only after validation passed
docs/silver_er.mmd  docs/silver_er.png   ER diagram of the published Silver
checks/p0/               P0 diagnostic notebooks (not part of the pipeline) and their raw outputs
checks/p2/               test and entry notebooks (run_id helpers, dq_helpers, Silver stage) and raw run outputs
```

Planned (not created yet):

```
notebooks/05_gold_build.py
notebooks/06_analysis.py         answers + visualisations
notebooks/run_pipeline.py        runs 01–05 in order and records the run state
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

- **`00_config`** defines the widgets, the derived schema names, `TPCH_TABLES`, the allowed-value lists and two run_id helpers. An entry notebook starts every execution with `run_id = new_run_id()`; child notebooks read it with `require_run_id()`, which fails if no entry notebook set one. `00_config` never sets `run_id`. Tested on serverless job runs and in an interactive session (`checks/p2/run_id_helpers/a5_interactive.py`, Run all twice): each execution got a different id, a `%run` child read the caller's id, and the child alone failed (`checks/p2/outputs/run_id_helpers/`).
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

## Validation approach (Stage 2: Silver and data quality)

**Lifecycle.** Bronze is never changed. `02_silver_stage` builds the proposed Silver in `{prefix}_staging` (`stg_<table>`) with column selection and casts only, so every Bronze row is kept. `03_validate` runs every rule on staging and appends one result row per rule and table to `{prefix}_audit.dq_check_results`. If any rule fails, it raises, and `04_silver_publish` does not execute, so the previous Silver stays as it was. Invalid rows are never dropped: the run fails and the violating keys are stored. Only after a full pass does `04_silver_publish` replace Silver and add the constraints.

**Rules** (all blocking; [design.md §6](docs/design.md#6-validation-rules)):

| Rule | Fails when | Assignment requirement |
|---|---|---|
| DQ-L1 | a line is shipped before its order date | dates vs the parent order |
| DQ-L2 | a line is received before it is shipped | dates within a line |
| DQ-L3 | a line's commit date is before its order date (our interpretation of "make sense relative to the parent order") | dates vs the parent order |
| DQ-L4 | an order or line date is NULL | dates must be checkable |
| DQ-L5–L7 | `l_shipmode`, `l_returnflag`, `l_linestatus` is NULL or outside the allowed list | categorical values |
| DQ-L8, DQ-L9 | a line without an order, an order without lines | order ↔ line integrity |
| DQ-G1, DQ-G2 | a NULL or duplicate primary key; a foreign key with no parent row (anti join), in all 11 Silver tables | keys of the 3NF model |
| DQ-G3 | row counts differ between source, Bronze and staging | no silent loss |

Late deliveries (received after the commit date) are valid business outcomes and have no rule. Same-day ship, receipt and commit dates pass. The allowed lists come from profiling (see [Configuration, Bronze and profiling](#configuration-bronze-and-profiling-stage-1)).

**Where the results are.** `{prefix}_audit.dq_check_results` is append-only: `run_id`, `run_ts`, `rule_id`, `layer`, `table_name`, `violation_count`, `sample_keys` (up to 10 violating keys), `severity`, `passed`. Only `notebooks/dq_helpers.py` writes it. `raise_if_failed(run_id, rule_ids)` reads only the rows of the given run, so an earlier failed run never blocks a new one, and a rule without a row counts as failed.

**3NF.** Every declared key was confirmed unique, and every candidate dependency was tested on the data (`GROUP BY X HAVING count(DISTINCT A) > 1`) and checked against the TPC-H specification ([design.md §5.3](docs/design.md#53-3nf-analysis--method-decided-d14-results-below)). Three dependencies hold in the data *and* are documented generation rules, so they were removed by decomposition:

| Dependency | Rule in TPC-H spec rev. 3.0.1, §4.2.3 | New Silver table |
|---|---|---|
| `p_brand → p_mfgr` | brand `Brand#MN` carries the manufacturer number `M` | `brand(p_brand, p_mfgr)` |
| `l_shipdate → l_linestatus` | `O` if shipped after 1995-06-17, else `F` | `ship_date_status(l_shipdate, l_linestatus)` |
| `(l_partkey, l_quantity) → l_extendedprice` | `l_extendedprice = l_quantity × p_retailprice` | `part_quantity_price(l_partkey, l_quantity, l_extendedprice)` |

`l_receiptdate → l_returnflag` was refuted by the data (R and A are random). The phone country code (`nationkey + 10`) is a dependency on part of one string, which we keep atomic; the constant `o_shippriority` is kept as a documented deviation. Silver therefore has 11 tables:

![Silver ER diagram](docs/silver_er.png)

**Constraints** (added by `04_silver_publish`): `NOT NULL` on every key and the validated dates and categories, and `CHECK (l_receiptdate >= l_shipdate)`, both enforced by Delta; a primary key on every table and 12 foreign keys, which Databricks records but does not enforce (referential integrity is proved by DQ-G2).

**Running the Silver stage on its own.** The notebooks must sit in one workspace folder that mirrors the repo layout (the entry notebook uses `%run ../../../notebooks/...`). Import `notebooks/` (`00_config`, `01_bronze_ingest`, `silver_contract`, `dq_helpers`, `02_silver_stage`, `03_validate`, `04_silver_publish`) and `checks/p2/silver_stage/silver_stage_entry` as in [Stage 1](#configuration-bronze-and-profiling-stage-1), run `01_bronze_ingest`, then run the entry notebook as a serverless one-time job:

```json
{"run_name": "silver stage", "tasks": [{"task_key": "silver", "notebook_task": {
  "notebook_path": "/Users/<you>/nachalniki/checks/p2/silver_stage/silver_stage_entry",
  "base_parameters": {"schema_prefix": "my_prefix"}}}]}
```

The entry notebook runs `%run 00_config` → `run_id = new_run_id()` → `02_silver_stage` → `03_validate` → `04_silver_publish`. It writes `dq_check_results` but not `pipeline_runs`, so use a scratch `schema_prefix` once the full pipeline has produced Gold in a prefix.

**Results of 2026-10-07** (prefix `makc_logistics`; raw outputs in `checks/p2/outputs/`):
- Success run `159dd764-f326-4abf-ade9-279d5d540f7e`: all 41 result rows of the 12 rule IDs passed; 11 Silver tables published with their constraints (lineitem 29,999,795 rows, `part_quantity_price` 22,657,201, `ship_date_status` 2,526, `brand` 25).
- Failure demo in the scratch prefix `makc_logistics_s2demo`: one staged line (`1|1`) was set to be received a day before it was shipped. `03_validate` recorded DQ-L2 `passed = false` with sample key `1|1` and raised; `04_silver_publish` was skipped; Silver compared with a snapshot taken before the run gave 0 differing rows in both directions for all 11 tables. The scratch schemas were dropped afterwards.

## Results

*Not available yet.* The answers to Q1–Q4 will be added only from an actual successful run, together with the run date.

## Presentation

> **Placeholder:** link to the slides will be added here (MAX-15 and MAX-16 in [docs/plan.md](docs/plan.md)).

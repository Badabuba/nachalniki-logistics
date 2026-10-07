# nachalniki-logistics

Team **«начальніки»**: Nazar, Yaropolk, Max. UCU Big Data, Group Assignment 1.

> **Status: The full Bronze → Silver → Gold pipeline, automated runner, determinism, portability and Logistics Q1–Q4 analysis with monthly monitoring are verified on Databricks.** Succeeded runs, exact results and evidence references are reported below.

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
notebooks/05_gold_build.py       Silver -> eight Logistics Gold tables plus Gold DQ checks
notebooks/06_analysis.py         guarded Q1-Q4 tables, answers and charts
notebooks/run_pipeline.py        complete Bronze -> Silver -> Gold run plus lifecycle audit
docs/silver_er.mmd  docs/silver_er.png   ER diagram of the published Silver
checks/p0/               P0 diagnostic notebooks (not part of the pipeline) and their raw outputs
checks/p2/               test and entry notebooks (run_id helpers, dq_helpers, Silver stage) and raw run outputs
checks/p3/               Stage 3 entry notebooks and raw run evidence
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

## How to run

The full pipeline runs 01–05 in sequence under an append-only audit lifecycle. Individual stages can also be executed standalone (see [Stage 1](#configuration-bronze-and-profiling-stage-1) and [Stage 2](#running-the-silver-stage-on-its-own)).

### Interactive execution (UI)

1. In Databricks, create a Git folder from this repository (or import `notebooks/` into a workspace folder).
2. Open `notebooks/run_pipeline.py`. Configure widget values if needed (`catalog` defaults to `workspace`, `schema_prefix` to `nachalniki_logistics`, `source` to `samples.tpch`). In a shared workspace, use your own `schema_prefix`.
3. Run all cells. The runner:
   - Starts a fresh `run_id` via `new_run_id()`.
   - Records `started` in `{prefix}_audit.pipeline_runs`.
   - Executes `%run ./01_bronze_ingest` (copies 8 TPC-H tables).
   - Executes `%run ./02_silver_stage` (casts Bronze into 11 staging tables).
   - Executes `%run ./03_validate` (runs 12 blocking data-quality rules). If any check fails, execution halts immediately and publishing is skipped.
   - Executes `%run ./04_silver_publish` (publishes Silver tables and applies Delta constraints).
   - Executes `%run ./05_gold_build` (computes 8 Logistics Gold tables and Gold DQ checks).
   - Records `succeeded` in `{prefix}_audit.pipeline_runs`.
4. Open `notebooks/06_analysis.py` and run all cells. The run-state guard halts if the latest run in `pipeline_runs` did not succeed. When valid, it displays query tables, renders 5 charts (Q1–Q4 and monthly monitoring), and displays factual answer summaries.

### Command-line execution (Databricks CLI)

Run as serverless one-time jobs from your local terminal (tested in MAX-10 and MAX-12). First import every file of `notebooks/` into one workspace folder, e.g. `/Users/<you>/nachalniki/notebooks/`, with `databricks workspace import` as shown in [Stage 1](#configuration-bronze-and-profiling-stage-1); the `notebook_path` below must point to that folder. In a workspace shared with other users, set your own `schema_prefix` in `base_parameters` so the run does not replace another user's tables.

```bash
# 1. Run the full pipeline
databricks jobs submit --json '{
  "run_name": "full_pipeline",
  "tasks": [{
    "task_key": "pipeline",
    "notebook_task": {
      "notebook_path": "/Users/<you>/nachalniki/notebooks/run_pipeline",
      "base_parameters": {}
    }
  }]
}'

# 2. Run the analysis and monitoring visualisations
databricks jobs submit --json '{
  "run_name": "logistics_analysis",
  "tasks": [{
    "task_key": "analysis",
    "notebook_task": {
      "notebook_path": "/Users/<you>/nachalniki/notebooks/06_analysis",
      "base_parameters": {}
    }
  }]
}'
```

Override widgets by specifying key-values in `base_parameters` (e.g. `{"schema_prefix": "custom_prefix"}`).

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

The numbers below are read from the Gold tables of succeeded pipeline run `25979743-a4a7-4ab8-a4b2-c37af6d03805` (2026-10-07, catalog `workspace`, prefix `makc_logistics`, job run `317490104173577`; every DQ rule passed), as displayed by `06_analysis` (job run `954628711835688`). The same code produced the default-prefix run `64829233-7f8c-42e0-9fd9-c08c765f2aef`; the determinism rerun `f21d3f70-1d14-4bfa-bb60-47a5fc4e8ac0` and the portability run `1bc3ffae-424d-4281-948a-bb0ea9df243a` showed identical Gold across reruns and prefixes (`EXCEPT ALL` = 0 in all 8 tables).

### Q1 — Transit speed and predictability by ship mode

- **Fastest ship mode:** `AIR` and `REG AIR` tie with the lowest median transit time of **15.00 days**. Their means are both 15.50 days (15.495 vs 15.499), a difference too small to name a winner. All other modes (`FOB`, `MAIL`, `RAIL`, `SHIP`, `TRUCK`) have a median of 16.00 days.
- **Most predictable ship mode:** `SHIP`, with the narrowest slow tail: p90 − p50 = **11.00 days** (p50 = 16.00 d, p90 = 27.00 d, IQR = 15.00 d, stddev = 8.66 d). The other modes have a p90 − p50 spread of 12.00 to 13.00 days.
- **Why speed and predictability differ:** Speed is about the *location* of the transit-day distribution (median, mean); predictability is about its *spread* (p90 − p50, IQR, stddev). The two can rank modes differently: `AIR` has the lowest median (15 days) but the widest p90 − p50 spread (13 days), while `SHIP` has a higher median (16 days) and the narrowest spread (11 days). All means are 15.50 days, so the differences between modes are small.

| Ship mode | Line items | p50 (days) | p90 (days) | Spread p90 − p50 | IQR | Mean (days) | Stddev (days) |
|---|---|---|---|---|---|---|---|
| **AIR** | 4,285,543 | **15.00** | 28.00 | 13.00 | 15.00 | 15.50 | 8.66 |
| **REG AIR** | 4,285,596 | **15.00** | 27.00 | 12.00 | 15.00 | 15.50 | 8.65 |
| **SHIP** | 4,285,381 | 16.00 | 27.00 | **11.00** | 15.00 | 15.50 | 8.66 |
| **FOB** | 4,287,168 | 16.00 | 28.00 | 12.00 | 15.00 | 15.51 | 8.65 |
| **MAIL** | 4,282,860 | 16.00 | 28.00 | 12.00 | 15.00 | 15.50 | 8.66 |
| **RAIL** | 4,284,870 | 16.00 | 28.00 | 12.00 | 15.00 | 15.50 | 8.66 |
| **TRUCK** | 4,288,377 | 16.00 | 28.00 | 12.00 | 15.00 | 15.50 | 8.65 |

### Q2 — Fully on-time orders versus on-time line items

- **Individual line on-time share:** **36.77%** (11,031,691 on-time lines out of 29,999,795 lines).
- **Fully on-time order share:** **8.30%** (622,660 fully on-time orders out of 7,500,000 orders).
- **Gap:** **28.47 percentage points**.
- **Why the two differ:** An order is fully on time only if *every* line item is received on or before its commit date (`is_fully_on_time = (late_line_count == 0)`). Orders contain between 1 and 7 lines (median 4.0, mean 4.00). The line on-time share is about 36.8% in every order size, but the order on-time share falls sharply as orders get bigger:

| Lines in order | Orders | Fully on-time orders | Order on-time share | Line on-time share |
|---|---|---|---|---|
| **1** | 1,071,498 | 393,504 | **36.72%** | 36.72% |
| **2** | 1,072,178 | 145,111 | **13.53%** | 36.77% |
| **3** | 1,070,076 | 53,697 | **5.02%** | 36.81% |
| **4** | 1,071,495 | 19,494 | **1.82%** | 36.77% |
| **5** | 1,072,080 | 7,198 | **0.67%** | 36.77% |
| **6** | 1,071,378 | 2,613 | **0.24%** | 36.78% |
| **7** | 1,071,295 | 1,043 | **0.10%** | 36.76% |

### Q3 — Late delivery rate by ship mode

- **Highest delay rate mode:** `AIR` with **63.29%** (2,712,448 late lines out of 4,285,543 lines).
- **Distribution across all modes:** all 7 modes lie within 0.10 percentage points (63.19% to 63.29%), so the "worst" mode is only marginally worse:

| Ship mode | Line count | Late lines | Delay rate |
|---|---|---|---|
| **AIR** | 4,285,543 | 2,712,448 | **63.29%** |
| **RAIL** | 4,284,870 | 2,710,348 | **63.25%** |
| **REG AIR** | 4,285,596 | 2,709,635 | **63.23%** |
| **SHIP** | 4,285,381 | 2,709,034 | **63.22%** |
| **TRUCK** | 4,288,377 | 2,710,869 | **63.21%** |
| **MAIL** | 4,282,860 | 2,706,820 | **63.20%** |
| **FOB** | 4,287,168 | 2,708,950 | **63.19%** |

### Q4 — Fulfilment speed: urgent vs non-urgent priority

- **Conclusion:** Urgent-priority orders (`1-URGENT`) are **not fulfilled faster** than non-urgent orders. By the primary order-grain measure (order date to the receipt of the last line), urgent and non-urgent orders tie on median and p90, and their means differ by less than 0.02 days:
  - **Median completion days:** **116.00 days** for urgent (n = 1,501,100) vs **116.00 days** for non-urgent (n = 5,998,900).
  - **p90 completion days:** **138.00 days** for urgent vs **138.00 days** for non-urgent.
  - **Mean completion days:** **108.40 days** for urgent vs **108.39 days** for non-urgent.

Supporting line-grain metrics show the same picture:
- **Transit days (ship to receipt):** urgent median 15.00 d (p90 27.00 d, mean 15.50 d) vs non-urgent median 16.00 d (p90 27.00 d, mean 15.50 d).
- **Order-to-ship days:** urgent median 61.00 d (p90 109.00 d, mean 61.01 d) vs non-urgent median 61.00 d (p90 109.00 d, mean 61.00 d).

| Priority | Urgent? | Order count | Complete p50 | Complete p90 | Complete mean | Line count | Transit p50 | Transit p90 |
|---|---|---|---|---|---|---|---|---|
| **1-URGENT** | Yes | 1,501,100 | **116.00 d** | **138.00 d** | **108.40 d** | 6,004,707 | 15.00 d | 27.00 d |
| **2-HIGH** | No | 1,499,192 | 116.00 d | 138.00 d | 108.41 d | 6,000,786 | 16.00 d | 28.00 d |
| **3-MEDIUM** | No | 1,498,710 | 116.00 d | 138.00 d | 108.41 d | 5,991,279 | 16.00 d | 28.00 d |
| **4-NOT SPECIFIED** | No | 1,501,281 | 116.00 d | 138.00 d | 108.38 d | 6,004,909 | 15.00 d | 27.00 d |
| **5-LOW** | No | 1,499,717 | 116.00 d | 138.00 d | 108.35 d | 5,998,114 | 15.00 d | 28.00 d |

### Monitoring — Monthly delay rate over time

- **Series:** 82 commit months in `agg_delay_rate_monthly`, from 1992-01 to 1998-10. Over all 29,999,795 lines the delay rate is 63.23%.
- **Stable period:** from 1992-04 to 1998-08 (77 months) the monthly delay rate stays between **62.97%** (1997-01) and **63.45%** (1992-06), with a mean of 63.23% and 348,744 to 389,002 lines per month.
- **Boundary and edge months:**
  - **1992-01** (first month, `is_boundary_month = true`, "potentially incomplete"): 213 lines, delay rate 86.38%.
  - **1992-02** and **1992-03** (edge months with lower counts): 95,167 lines at 80.11% and 291,339 lines at 68.72%. Orders start on 1992-01-01 and commit dates fall 30–90 days after the order date, so the first commit months hold only part of the lines due then.
  - **1998-09** (edge month): 284,559 lines, delay rate 57.86%.
  - **1998-10** (last month, `is_boundary_month = true`, "potentially incomplete"): 101,741 lines, delay rate 47.08%.
- The edge months contain only lines with particular commit lags (short lags at the start, long lags at the end), so their rates should not be read as a change in delivery performance.


## Presentation

> **Placeholder:** link to the slides will be added here (MAX-15 and MAX-16 in [docs/plan.md](docs/plan.md)).

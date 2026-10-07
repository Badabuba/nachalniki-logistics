# nachalniki-logistics

Team **«начальніки»**: Nazar, Yaropolk, Max. UCU Big Data, Group Assignment 1 ([`group_assignment_1.pdf`](group_assignment_1.pdf), §3 deliverables, §5.2 Logistics).

A Bronze → Silver → Gold lakehouse on Databricks `samples.tpch` (8 TPC-H tables) that answers the **Logistics** profile:

1. Median and p90 transit time (ship → receipt) per ship mode; fastest vs most predictable mode.
2. Share of fully on-time orders vs share of on-time line items, and the gap.
3. Share of late line items (received after the commit date) per ship mode; worst mode.
4. Whether urgent-priority orders are fulfilled faster than others.

It also validates dates, categorical values and order ↔ line-item integrity, and monitors the delay rate over time. The full pipeline, determinism across reruns, portability to another schema prefix, the validation failure behaviour and the analysis were run on Databricks (serverless) on 2026-10-07; results and evidence are below.

## Team responsibilities

| Member | Work |
|---|---|
| Nazar | repository and uv, configuration (`00_config`, run_id helpers), Bronze ingest, source profiling and allowed value lists |
| Max | Silver (`silver_contract`, `02_silver_stage`, `03_validate`, `04_silver_publish`, `dq_helpers`), 3NF analysis and ER diagram, presentation assembly and submission |
| Yaropolk | Gold (`05_gold_build`), Q1–Q4 analysis and charts, delay-rate monitoring, `run_pipeline`, integration runs and the README |

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

Defaults: `catalog = workspace`, `prefix = nachalniki_logistics`, `source = samples.tpch`. They are the widgets of `00_config`; nothing else hard-codes a catalog, schema or source, so another workspace or prefix runs the project unchanged.

Run lifecycle: `run_pipeline` starts a fresh `run_id` (`new_run_id()`), appends `started` to `{prefix}_audit.pipeline_runs`, runs steps 01–05 with `%run`, and appends `succeeded` only at the end. Any exception stops the run, so a failed run has no `succeeded` row. Child notebooks only read the id with `require_run_id()`. `06_analysis` refuses to present results if the latest run in `pipeline_runs` has no `succeeded` row, so stale Gold is never shown as current. Audit tables are append-only; only `dq_helpers` writes `dq_check_results` and only `run_pipeline` writes `pipeline_runs`.

## Repository layout

```
group_assignment_1.pdf   assignment
pyproject.toml  uv.lock  .gitignore
notebooks/
  00_config.py           parameters, schema names, allowed values, run_id helpers
  01_bronze_ingest.py    source -> Bronze, with a source/Bronze comparison
  profile_source.py      value profiling; 3NF key and dependency tests on Bronze
  silver_contract.py     Silver tables, typed columns, keys, foreign keys, constraints
  02_silver_stage.py     Bronze -> staging (casts, no filtering)
  dq_helpers.py          creates/appends dq_check_results; run-scoped failure checks
  03_validate.py         all blocking rules on staging; raises on any failure
  04_silver_publish.py   staging -> Silver plus constraints, only after validation passed
  05_gold_build.py       Silver -> eight Gold tables plus Gold DQ checks
  06_analysis.py         guarded Q1-Q4 tables, answers and charts, monthly monitoring
  run_pipeline.py        complete Bronze -> Silver -> Gold run plus lifecycle audit
docs/silver_er.mmd  docs/silver_er.png   ER diagram of the published Silver
checks/                  entry notebooks and scripts for the failure demos, determinism and run_id tests
checks/*/outputs/        raw outputs of the Databricks runs cited below (kept unchanged)
```

## Setup

Prerequisites:
- A Databricks workspace with access to `samples.tpch` and a catalog where you can create schemas (`CREATE SCHEMA`; without it the Bronze notebook fails on its first statement).
- Git, and [uv](https://docs.astral.sh/uv/) for local tooling.
- Optional: the [Databricks CLI](https://docs.databricks.com/dev-tools/cli/) (v1.19.0 was used) with a logged-in profile (`databricks auth login`). Add `-p <profile>` to the commands below if it is not the default.

```bash
uv sync      # creates .venv; there are no dependencies (Spark is provided by Databricks)
```

Notebook parameters (widgets of `notebooks/00_config.py`):

| Widget | Default | Meaning |
|---|---|---|
| `catalog` | `workspace` | catalog where the project schemas are created |
| `schema_prefix` | `nachalniki_logistics` | schemas are `{catalog}.{prefix}_bronze`, `_staging`, `_silver`, `_gold`, `_audit`; another prefix gives an independent copy. In a shared workspace use your own prefix |
| `source` | `samples.tpch` | `<catalog>.<schema>` of the 8 TPC-H tables |

## How to run

The notebooks use relative `%run ./00_config`, so they must sit together in one workspace folder (a Git folder of this repository, or an imported copy of `notebooks/`).

### Interactive (UI)

1. Create a Git folder from this repository in Databricks (or import `notebooks/`).
2. Open `notebooks/run_pipeline.py`, set widgets if needed, and run all cells. It runs `01_bronze_ingest` → `02_silver_stage` → `03_validate` (halts if any rule fails; nothing is published) → `04_silver_publish` → `05_gold_build`, and records `started` / `succeeded` in `pipeline_runs`.
3. Open `notebooks/06_analysis.py` and run all cells: the run-state guard, the Q1–Q4 tables, five charts (Q1–Q4 and monthly monitoring) and the answer summaries.

### Command line (Databricks CLI, serverless one-time jobs)

Import every file of `notebooks/` into one workspace folder, then submit the notebooks:

```bash
databricks workspace mkdirs /Users/<you>/nachalniki/notebooks
databricks workspace import /Users/<you>/nachalniki/notebooks/00_config --file notebooks/00_config.py --format SOURCE --language PYTHON
# (same for the other files in notebooks/)

databricks jobs submit --json '{"run_name": "full_pipeline", "tasks": [{"task_key": "pipeline",
  "notebook_task": {"notebook_path": "/Users/<you>/nachalniki/notebooks/run_pipeline", "base_parameters": {}}}]}'

databricks jobs submit --json '{"run_name": "logistics_analysis", "tasks": [{"task_key": "analysis",
  "notebook_task": {"notebook_path": "/Users/<you>/nachalniki/notebooks/06_analysis", "base_parameters": {}}}]}'
```

Override widgets in `base_parameters`, e.g. `{"schema_prefix": "my_prefix"}`. Stages can also run alone: `01_bronze_ingest` and `profile_source` need only the source and Bronze.

### Check notebooks

The notebooks under `checks/` use `%run ../../../notebooks/...`, so import the repository folder structure (`notebooks/` and the `checks/` subfolders) as it is. Use a scratch `schema_prefix` for every check.

- `checks/p2/silver_stage/silver_stage_entry`: `00_config` → `run_id = new_run_id()` → `02_silver_stage` → `03_validate` → `04_silver_publish` (run `01_bronze_ingest` first). `silver_snapshot` snapshots Silver before a run and compares it afterwards (`EXCEPT ALL` in both directions).
- `checks/p3/failure_demo/`: end-to-end failure check. `run_e2e_failure_demo.py` submits the jobs through the CLI; its workspace path and SQL warehouse id are those of the original run and must be changed.
- `checks/p3/pipeline_runner/two_runs_entry`: two consecutive pipeline executions get different `run_id`s and the audit tables keep both.
- `checks/p2/run_id_helpers/`, `checks/p2/dq_helpers/`: tests of the run_id helpers and of `dq_helpers`.

## Configuration, Bronze and profiling

- **`00_config`** defines the widgets, the derived schema names, `TPCH_TABLES`, the allowed-value lists and the two run_id helpers. An entry notebook starts every execution with `run_id = new_run_id()`; `00_config` never sets it.
- **`01_bronze_ingest`** copies all 8 tables with `CREATE OR REPLACE TABLE … AS SELECT *` and adds only `_ingested_at` and `_source_table`. Its last cell compares each table with the source and fails on any difference in column names, order, types or row counts. Run of 2026-10-07: all 8 matched.
- **`profile_source`** reads Bronze only. It shows value counts and lengths of `l_shipmode`, `l_returnflag`, `l_linestatus`, `o_orderpriority`, the date ranges, lines per order, and the key and dependency tests used for 3NF.

**Allowed values.** Profiled in Bronze and compared with the TPC-H Standard Specification rev. 3.0.1 (clause 4.2.2.13 "Modes"; clause 4.2.3 for `L_RETURNFLAG` / `L_LINESTATUS`). Every value was both observed and documented, with no NULLs and no extra whitespace, so the lists are exactly:

| Constant | Values (rows observed, 2026-10-07) |
|---|---|
| `ALLOWED_SHIP_MODES` | AIR 4285543, FOB 4287168, MAIL 4282860, RAIL 4284870, REG AIR 4285596, SHIP 4285381, TRUCK 4288377 |
| `ALLOWED_RETURN_FLAGS` | A 7403889, N 15189553, R 7406353 |
| `ALLOWED_LINE_STATUSES` | F 15002681, O 14997114 |

A value outside these lists is never added silently: validation fails on it and no row is dropped. `o_orderpriority` has 5 values; the urgent one is `1-URGENT`. Dates run from 1992-01-01 (first order) to 1998-12-31 (last receipt). Every order has 1–7 lines (median 4).

## Validation

**Lifecycle.** Bronze is never changed. `02_silver_stage` builds the proposed Silver in `{prefix}_staging` (`stg_<table>`) with column selection and casts only, so every Bronze row is kept. `03_validate` runs every rule on staging and appends one row per rule and table to `{prefix}_audit.dq_check_results` (`run_id`, `run_ts`, `rule_id`, `layer`, `table_name`, `violation_count`, `sample_keys` with up to 10 violating keys, `severity`, `passed`). If any rule fails it raises, `04_silver_publish` does not execute, and the previous Silver stays as it was. Invalid rows are never dropped. `raise_if_failed(run_id, rule_ids)` reads only the rows of the given run, and a rule without a row counts as failed.

| Rule | Fails when | Assignment requirement |
|---|---|---|
| DQ-L1 | a line is shipped before its order date | dates vs the parent order |
| DQ-L2 | a line is received before it is shipped | dates within a line |
| DQ-L3 | a line's commit date is before its order date (our interpretation of "make sense relative to the parent order") | dates vs the parent order |
| DQ-L4 | an order or line date is NULL | dates must be checkable |
| DQ-L5–L7 | `l_shipmode`, `l_returnflag`, `l_linestatus` is NULL or outside the allowed list | categorical values |
| DQ-L8, DQ-L9 | a line without an order; an order without lines | order ↔ line integrity |
| DQ-G1, DQ-G2 | a NULL or duplicate primary key; a foreign key with no parent row (anti join), in all 11 Silver tables | keys of the 3NF model |
| DQ-G3 | row counts differ between source, Bronze and staging | no silent loss |
| DQ-GOLD1, DQ-GOLD2 | Gold fact row counts differ from Silver `lineitem` / `orders` | no double counting or loss |

Late deliveries (received after the commit date) are valid business outcomes and have no rule. Same-day ship, receipt and commit dates pass.

**Failure behaviour (demonstrated).**
- Silver stage, scratch prefix `makc_logistics_s2demo`: one staged line (`1|1`) was set to be received a day before it was shipped. `03_validate` recorded DQ-L2 `passed = false` with sample key `1|1` and raised; `04_silver_publish` was skipped; Silver compared with a snapshot taken before the run had 0 differing rows in both directions for all 11 tables (`checks/p2/outputs/silver_stage/`).
- End to end, scratch prefix `makc_logistics_e2e`: an injected bad row made the pipeline job fail with a `started` row but no `succeeded` row in `pipeline_runs`, DQ-L2 recorded as failed, all 8 Gold tables identical to a snapshot (`EXCEPT ALL` = 0), and `06_analysis` stopped at the run-state guard (`checks/p3/outputs/max14_e2e_failure/`).
- Success run `159dd764-f326-4abf-ade9-279d5d540f7e` (prefix `makc_logistics`): all 41 result rows of the 12 rule IDs passed; 11 Silver tables published (lineitem 29,999,795 rows).

## Silver and 3NF

Definition used: a relation is in 3NF if for every non-trivial functional dependency `X → A`, `X` is a superkey or `A` is prime. Copying a well-designed source does not prove this, so each candidate dependency was tested on Bronze (`GROUP BY X HAVING count(DISTINCT A) > 1`; zero rows means it holds) and checked against the TPC-H specification (clauses 4.2.2.9, 4.2.2.12, 4.2.3; snapshot date `CURRENTDATE = 1995-06-17`). A dependency was treated as a violation only if it held in the data **and** is a documented generation rule. Raw output: `checks/p2/outputs/fd_analysis/`.

| Relation | Candidate dependency | Data | Documented rule | Outcome |
|---|---|---|---|---|
| all 8 | declared primary keys | unique, no NULL | – | candidate keys confirmed |
| `region`, `nation`, `supplier`, `customer` | name columns unique | unique | `S_NAME`/`C_NAME` = prefix + key; fixed name lists | alternative keys; make the name prime, no violation |
| `part` | `p_brand → p_mfgr` | holds (0 of 25 brands violate) | `P_BRAND = "Brand#" M N`, `M` from `P_MFGR` | **violation** → `brand(p_brand, p_mfgr)` |
| `lineitem` | `l_shipdate → l_linestatus` | holds (0 of 2,526 dates) | `O` if shipped after 1995-06-17, else `F` | **violation** → `ship_date_status(l_shipdate, l_linestatus)` |
| `lineitem` | `(l_partkey, l_quantity) → l_extendedprice` | holds (0 of 22,657,201) | `l_extendedprice = l_quantity × p_retailprice` | **violation** → `part_quantity_price(l_partkey, l_quantity, l_extendedprice)` |
| `lineitem` | `l_receiptdate → l_returnflag` | refuted (1,261 of 2,555 dates have both R and A) | R or A at random if received on/before the cutoff, else N | not a dependency |
| `customer`, `supplier` | `*_nationkey → phone prefix` | holds | country code = nation index + 10 | dependency on part of one string; phone kept atomic |
| `orders` | `∅ → o_shippriority` | constant 0 | set to 0 | one-row relation adds no information; kept as a documented deviation |
| `orders` | `o_orderstatus`, `o_totalprice` | – | computed from the order's lines | depends on rows of another relation, not an FD within `orders` |

Each violation is fixed by decomposition: the dependent attribute moves to a table keyed by its determinant, and the original table keeps the determinant as a foreign key, so the join is lossless. The decomposed tables are built with `SELECT DISTINCT`; if the data ever broke a rule, the key would be duplicated and DQ-G1 would block the run. Silver therefore has 11 tables (`lineitem` no longer carries `l_linestatus`, which no Gold table uses):

![Silver ER diagram](docs/silver_er.png)

**Constraints** (added by `04_silver_publish`): `NOT NULL` on every key and the validated dates and categories, and `CHECK (l_receiptdate >= l_shipdate)`, both enforced by Delta; a primary key on every table and 12 foreign keys, which Databricks records but does not enforce. Referential integrity is proven by the anti-join rules DQ-G2 and DQ-L8/L9.

## Gold and metric definitions

Gold tables (snake_case business names): `fct_lineitem_delivery` (line grain), `fct_order_fulfillment` (order grain; lines are aggregated per `l_orderkey` before joining `orders`), `agg_ship_mode_performance`, `agg_on_time_summary`, `agg_on_time_by_line_count`, `agg_priority_fulfillment`, `agg_urgency_fulfillment`, `agg_delay_rate_monthly`. Gold uses `LEFT JOIN` from `orders`, so an order without lines would show `line_count = 0` instead of disappearing.

| Metric | Definition |
|---|---|
| `transit_days` | `datediff(l_receiptdate, l_shipdate)` |
| `order_to_ship_days` | `datediff(l_shipdate, o_orderdate)` per line |
| `is_late` | `l_receiptdate > l_commitdate` (receipt on the commit date is on time) |
| fully on-time order | `line_count ≥ 1` and `late_line_count = 0` |
| line / order on-time share | on-time lines / all lines; fully on-time orders / orders |
| delay rate | late lines / all lines in the group (ship mode for Q3, commit month for monitoring) |
| `order_to_complete_days` | `datediff(max(l_receiptdate), o_orderdate)` per order: fulfilled when the last line arrives |
| `is_urgent` | `o_orderpriority = '1-URGENT'` |

Percentiles use exact `percentile_cont`, never `percentile_approx`, and are computed at the reported grain, never averaged across groups. Q1: *fastest* = lowest median `transit_days`; *most predictable* = smallest `p90 − p50` (supported by IQR and standard deviation). Speed is the location of the distribution and predictability its spread, so the rankings can differ. Q4 uses the order grain (`order_to_complete_days`) as the primary measure, with line-grain `transit_days` and `order_to_ship_days` as supporting evidence.

**Monitoring.** The delay rate is grouped by **commit month** (`date_trunc('MONTH', l_commitdate)`): each line's promise falls due on its commit date, so every line lands in the period its promise belongs to, whereas grouping by receipt month would push late lines into later months. `agg_delay_rate_monthly` holds the whole series with `line_count`; the first and last observed months are flagged `is_boundary_month`, and edge months with visibly fewer lines are called out in `06_analysis`. A SQL alert or dashboard on the delay rate was not built (optional in the assignment).

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


## Limitations

- Primary and foreign keys are informational in Databricks; only `NOT NULL` and `CHECK` are enforced. Integrity is proven by the validation rules.
- 3NF is argued for the dependencies examined; free-text columns and `*_phone` are treated as atomic strings.
- TPC-H is synthetic: delay rates and transit times are nearly identical across modes and priorities, so the differences in Q1 and the "worst" mode in Q3 are small and should not be over-interpreted.
- The first and last commit months are incomplete; the rates of the edge months are not a change in delivery performance.
- No alert, dashboard or scheduled Job was built.

## Evidence

Raw outputs of the Databricks runs are kept unchanged under `checks/p2/outputs/` and `checks/p3/outputs/` (job metadata `*_get_run.json` with run ids and parameters, decoded notebook cells `*_decoded.json`, query results `*.json`).

| Result | Evidence |
|---|---|
| Bronze ingest and comparison | `checks/p2/outputs/bronze_ingest/` |
| Profiling and 3NF dependency tests | `checks/p2/outputs/profiling/`, `checks/p2/outputs/fd_analysis/` |
| Silver stage success, DQ results, failure demo | `checks/p2/outputs/silver_stage/` |
| run_id and `dq_helpers` tests | `checks/p2/outputs/run_id_helpers/`, `checks/p2/outputs/dq_helpers/` |
| End-to-end failure check | `checks/p3/outputs/max14_e2e_failure/` |
| Pipeline run behind the Results (job run `317490104173577`) and analysis run `954628711835688` | `checks/p3/outputs/yar14_reproduction/` |
| Gold values read back to verify the Results | `checks/p3/outputs/yar09_review/gold_makc_logistics_20261008.json` |
| Latest `06_analysis` run, with monthly monitoring (job run `704809310624884`, prefix `makc_logistics`) | `checks/p3/outputs/analysis_monitoring_fix/` |
| Default-prefix run, determinism rerun, portability run | `checks/p3/outputs/max10_*`, `max11_*`, `max12_*` |

## Presentation
Presentation link — to be added by the team before submission.

# nachalniki-logistics

Team **«начальніки»**: Nazar, Yaropolk, Max. UCU Big Data, Group Assignment 1.

> **Status: planning.** The pipeline is **not implemented yet** and nothing has been run in Databricks. No results exist yet. Track progress in [docs/plan.md](docs/plan.md).

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
| [docs/plan.md](docs/plan.md) | Phases, task split, acceptance criteria, evidence log, decision log |
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

Defaults: `catalog = workspace` (to be verified), `prefix = nachalniki_logistics`, `source = samples.tpch`. All three are notebook parameters, so another workspace or schema prefix can run the project unchanged. Details are in [design.md §2–§3](docs/design.md).

## Repository layout

Present now:

```
group_assignment_1.pdf   assignment (source of truth)
README.md  CLAUDE.md
pyproject.toml  uv.lock  .gitignore
docs/requirements.md  docs/design.md  docs/plan.md
```

Planned (not created yet):

```
notebooks/00_config.py           parameters, schema names, allowed values
notebooks/profile_source.py      source profiling (allowed values, date ranges, FD checks)
notebooks/01_bronze_ingest.py
notebooks/02_silver_stage.py
notebooks/03_validate.py
notebooks/04_silver_publish.py
notebooks/05_gold_build.py
notebooks/06_analysis.py         answers + visualisations
notebooks/run_pipeline.py        runs 01–05 in order and records the run state
docs/silver_er.png               ER diagram screenshot
```

## Setup

Prerequisites:
- A Databricks workspace (Free Edition is expected) with access to `samples.tpch` and a catalog where you can create schemas.
- Git, and [uv](https://docs.astral.sh/uv/) for local tooling.

Works now (verified locally on 2026-10-07):

```bash
uv sync      # creates .venv; the project has no dependencies yet (Spark is provided by Databricks)
```

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

> **Placeholder:** link to the slides will be added here (P5 in [docs/plan.md](docs/plan.md)).

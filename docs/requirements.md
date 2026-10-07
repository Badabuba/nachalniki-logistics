# Requirements — Group Assignment 1, Logistics profile

Source: `group_assignment_1.pdf` in the repo root (9 pages). Page numbers below are the printed page numbers, which match the PDF page indices. If this file and the PDF disagree, the PDF wins.

Owners: **M1** = Nazar, **M2** = Yaropolk, **M3** = Max (provisional mapping, see [plan.md](plan.md)).
Status values: `not started` / `in progress` / `done (evidence: …)`. Only mark `done` with a link to the evidence.

## 1. Context from the PDF (not requirements by themselves)

- §1 p.1: the team helps a data migration to a Lakehouse. It must design the Bronze/Silver/Gold layers, build the pipeline that populates them, and answer the business questions. The customer is TPC-H, a decision-support benchmark modelling a wholesale supplier. This is the first of two phases, and the team must complete it to compete for the second.
- §2 p.2: each member can earn up to 7 points. The maximum requires submitting the presentation before the due date **and** presenting it in class.
- §3.3 p.2: notebooks, Python files, and Databricks Jobs & Pipelines are **allowed**, not required.
- §4 p.3: `samples.tpch` ships with every workspace and has 8 tables. Tip: read `/dbfs/databricks-datasets/tpch/README.md`.
- §5 p.4: each profile has a description, questions, validation rules, monitoring and alerting. The questions should be answerable from Gold. Validation rules may use all layers.
- §5.2 p.5: Logistics cares about the timeliness and consistency of deliveries. The main table is `lineitem` (ship/commit/receipt dates, delays, ship-mode performance).

## 2. Traceability checklist

### 2.1 Shared requirements (mandatory)

| ID | PDF | Requirement (explicit) | Planned deliverable | Owner | Evidence of completion | Status |
|---|---|---|---|---|---|---|
| R-S1 | §1 p.1 | Build the data processing pipeline that populates the layers | `run_pipeline` + notebooks `01`–`05` ([design §3](design.md#3-pipeline-lifecycle-one-run)) | M1 (integration) | Screenshot or log of a full successful run, plus a `pipeline_runs` row with `succeeded` | not started |
| R-S2 | §3.1 p.2 | Bronze: store data as is, no changes; metadata only if needed | `01_bronze_ingest`, 8 tables plus `_ingested_at` and `_source_table` | M1 | DQ-G3 passes (source = bronze counts); column list compared with the source | not started |
| R-S3 | §3.1 p.2 | Silver must be in 3NF | `02_silver_stage`, `04_silver_publish`; written 3NF analysis ([design §5.3](design.md#53-3nf-analysis--to-be-completed-with-profiling-evidence)) | M2 | Filled FD/candidate-key table with query outputs; any fix from §5.4 applied | not started |
| R-S4 | §3.1 p.2 | Silver must have enforced data quality | `03_validate` (blocking rules, Silver published only after a pass) plus enforced NOT NULL/CHECK | M2 | `dq_check_results` rows for a run, all `passed`; demo of a failing check blocking publish | not started |
| R-S5 | §3.1 p.2 | Gold designed to answer the chosen profile's questions | `05_gold_build` ([design §9](design.md#9-gold-tables-prefix_gold--contracts)) | M3 | Every Q1–Q4 answer queries only Gold tables | not started |
| R-S6 | §3.2 p.2 | Public repo with a working solution | GitHub repo `nachalniki-logistics`, visibility public | M1 | Repo URL opens in a logged-out browser; README run instructions reproduced by a second member | not started |
| R-S7 | §3.2 p.2 | Use uv | `pyproject.toml` and `uv.lock` | M1 | `uv lock`/`uv sync` succeed (local check) | in progress (`uv lock`/`uv sync` pass locally, see plan.md evidence log; not yet committed) |
| R-S8 | §3.2 p.2 | Code in Python or SQL | PySpark/SQL notebooks in `.py` source format | all | Notebooks in `notebooks/` | not started |
| R-S9 | §3.2 p.2 | Presentation in the repo, or a link to it in the README | README "Presentation" section | M1 | Working link or file in the repo | not started |
| R-S10 | §3.2 p.2 | A meaningful README | `README.md` | M1 (+ M2, M3 sections) | README has setup, run, validation and answers sections, reviewed by all three | in progress (initial version) |
| R-S11 | §3.2 p.2 ("ideally") | Scripts easily portable to another workspace; think about naming | `00_config` widgets `catalog`, `schema_prefix`, `source`; no hard-coded names | M1 | Run with a second `schema_prefix` matches the first Gold via `EXCEPT ALL` (0 rows) | not started |
| R-S12 | §3.2 p.2 ("ideally") | Assume the team only has access to pre-production data | Configurable source; no hard-coded counts or values; cross-layer reconciliation instead of fixed numbers | M1 | Code review: grep for literals of catalog, schema or row counts | not started |
| R-S13 | §4 p.3 | Use the TPC-H data in `samples.tpch` | `source = samples.tpch` default | M1 | P0 access-check output | not started |
| R-S14 | §5 p.4 | Questions answered using the Gold layer; validation may use all layers | Analysis reads `{prefix}_gold` only; DQ uses source/bronze/staging/gold | M3 / M2 | Code review of `06_analysis` | not started |
| R-S15 | §2 p.2 | Submit the presentation before the due date and present it in class (needed for max points) | Final deck plus a rehearsed talk | all | Submission confirmation; date given by the course (**not in the PDF**) | not started |

### 2.2 Presentation requirements (§3.4 p.3, mandatory)

| ID | Requirement | Deliverable | Owner | Evidence | Status |
|---|---|---|---|---|---|
| R-P1 | 5–7 minutes to explain the solution | Deck plus a timed rehearsal | all (M1 assembles) | Rehearsal time recorded in plan.md | not started |
| R-P2 | Team member responsibilities | Slide "Who did what" | M1 | Slide | not started |
| R-P3 | Link to the repo | Slide plus README | M1 | Slide | not started |
| R-P4 | The challenges faced | Slide, drawn from the plan.md decision log | all | Slide | not started |
| R-P5 | A short demo, including how the team decided to perform validation | Live or recorded run of `run_pipeline` + `dq_check_results` + a failing-check demo | M2 (validation part), M1 (run) | Demo script in plan.md; rehearsal | not started |
| R-P6 | Screenshot of the ER diagram of the Silver tables | Rendered ER of `{prefix}_silver` | M2 | Image in the deck (and in the repo `docs/`) | not started |
| R-P7 | Answers to the business questions, with code and a visualisation (notebook and/or Databricks dashboard) | `06_analysis` notebook charts | M3 | Screenshots of the charts with numbers, query code shown | not started |

### 2.3 Logistics requirements (§5.2 pp.5–6, mandatory unless marked)

| ID | PDF | Requirement (explicit) | Planned deliverable | Owner | Evidence of completion | Status |
|---|---|---|---|---|---|---|
| R-L-Q1 | p.5 | For each ship mode, report the median and p90 transit time (ship date to receipt date). Which mode is fastest, and which is most predictable? Explain why those are not the same question. | `agg_ship_mode_performance`; chart 1; text answer ([design §7](design.md#7-metric-definitions-gold)) | M3 | Table output, chart, written answer with numbers | not started |
| R-L-Q2 | p.5 | An order is fully on time only if every line item arrived by its commit date. What share of orders is fully on time, compared with the share of line items on time? Explain the gap. | `agg_on_time_summary`, `agg_on_time_by_line_count`; chart 2 | M3 | Both shares, the lines-per-order distribution, and the bucket table, all observed values | not started |
| R-L-Q3 | p.5 | For each ship mode, what share of line items was received after the commit date? Which mode performs worst? | `agg_ship_mode_performance.delay_rate`; chart 3 | M3 | Table, chart, answer with counts | not started |
| R-L-Q4 | p.6 | Are urgent-priority orders fulfilled faster than others? Support the answer with numbers. | `agg_priority_fulfillment`, `agg_urgency_fulfillment`; chart 4 | M3 | n, median, p90 and mean for urgent vs others; order-to-receipt and ship-to-receipt | not started |
| R-L-V1a | p.6 | Dates on each line item make sense relative to each other (cannot be received before it was shipped) | DQ-L2 (+ DQ-L4 non-null) | M2 | `dq_check_results` row | not started |
| R-L-V1b | p.6 | Dates make sense relative to the parent order (a shipment cannot leave before the order was placed) | DQ-L1; plus DQ-L3 `commit ≥ order` (**our interpretation**) | M2 | `dq_check_results` rows | not started |
| R-L-V2 | p.6 | Ship mode, return flag and line status contain only expected values. Build the allowed list by profiling the source and explain how. | `profile_source` → allowed lists in `00_config` → DQ-L5, DQ-L6, DQ-L7; method in [design §6](design.md#6-validation-rules) | M1 (profiling), M2 (rules) | Profiling output in design §5.5; method in the README; DQ rows | not started |
| R-L-V3a | p.6 | Every line item belongs to an existing order | DQ-L8 (anti join) | M2 | DQ row | not started |
| R-L-V3b | p.6 | No order has zero line items | DQ-L9 (anti join); DQ-GOLD2 keeps such orders visible | M2 | DQ row | not started |
| R-L-M1 | p.6 | Track the delay rate (share of line items received after the committed date) over time | `agg_delay_rate_monthly` (commit month), chart 5 in `06_analysis` | M3 | Chart with boundary months labelled | not started |
| R-L-A1 | p.6 | **Optional:** alert on a meaningful increase | Optional SQL alert or dashboard ([design §8](design.md#8-monitoring-delay-rate-over-time)) | unassigned (if time) | Alert definition plus a demo trigger | optional |

## 3. Explicit requirements vs our interpretation

| Topic | PDF says | Our interpretation (proposal, see design.md) |
|---|---|---|
| Transit time | "ship date to receipt date" | `datediff(l_receiptdate, l_shipdate)` in days |
| On time | "arrived by its commit date" | `l_receiptdate <= l_commitdate` (the same day counts as on time) |
| Late / delay | "received after the commit date" | `l_receiptdate > l_commitdate` |
| Predictable | not defined | Smallest spread: `p90 − p50`, with IQR and stddev as support |
| Urgent / "fulfilled" | not defined | `o_orderpriority = '1-URGENT'` (literal to profile); primary measure order date → last receipt; also ship → receipt |
| Delay rate "over time" | period not defined | Commit month; full observed series; boundary months labelled |
| Date sanity | two examples given ("e.g.") | DQ-L1 and DQ-L2 explicit; DQ-L3 `commit ≥ order` added by us |
| Ingestion scope | "the data" / 8 tables available | All 8 tables into Bronze and Silver; Gold covers Logistics only |
| Enforced quality | "enforced data quality" | Blocking validation before publish, plus enforced NOT NULL/CHECK; PK/FK informational only |
| Portability | "ideally" | Parameterised catalog, schema prefix and source |

## 4. Not in the PDF — do not invent

- **Deadline**: the PDF mentions "the due date" but gives none. Get it from the course channel.
- **Grading breakdown**: only "up to 7 points" per member. There is no rubric.
- **Required technology**: nothing beyond uv, Python or SQL, and Databricks with `samples.tpch`. Jobs, Pipelines and dashboards are optional.
- **Alert thresholds**: the PDF leaves what counts as "meaningful" to the team, and alerting is optional.
- **Presentation format** (slides tool, file type): not specified.

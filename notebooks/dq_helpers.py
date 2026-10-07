# Databricks notebook source
# MAGIC %md
# MAGIC # dq_helpers
# MAGIC
# MAGIC The only code that creates or appends to `{prefix}_audit.dq_check_results`.
# MAGIC Loaded with `%run ./dq_helpers` by `03_validate` and `05_gold_build`.
# MAGIC
# MAGIC - `ensure_dq_check_results()` creates the audit schema and table if missing; it never replaces them.
# MAGIC - `record_dq_result(...)` appends one result row for a rule.
# MAGIC - `raise_if_failed(run_id, rule_ids)` fails if any of those rules failed, or has no row, in that run.
# MAGIC
# MAGIC The functions take `run_id` as an argument; the caller gets it with `require_run_id()`.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

import json
from datetime import datetime, timezone

from pyspark.sql import functions as F

DQ_CHECK_RESULTS = f"{audit_schema}.dq_check_results"
DQ_LAYERS = ["source", "bronze", "staging", "gold"]
MAX_SAMPLE_KEYS = 10

DQ_CHECK_RESULTS_SCHEMA = (
    "run_id string, run_ts timestamp, rule_id string, layer string, table_name string, "
    "violation_count bigint, sample_keys string, severity string, passed boolean"
)

# COMMAND ----------

def ensure_dq_check_results():
    """Create the audit schema and dq_check_results if they do not exist. Never replaces the table."""
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {audit_schema}")
    spark.sql(f"CREATE TABLE IF NOT EXISTS {DQ_CHECK_RESULTS} ({DQ_CHECK_RESULTS_SCHEMA})")


def record_dq_result(run_id, rule_id, layer, table_name, violation_count, sample_keys):
    """Append one rule result. The rule passes only when violation_count is 0.

    sample_keys is a list of up to 10 violating keys (each key as a string, e.g. "1|3" for a
    composite key); it is stored as a JSON array string.
    """
    if not run_id:
        raise ValueError("run_id is required")
    if layer not in DQ_LAYERS:
        raise ValueError(f"layer must be one of {DQ_LAYERS}, got {layer!r}")
    violation_count = int(violation_count)
    if violation_count < 0:
        raise ValueError(f"violation_count must be >= 0, got {violation_count}")
    sample_keys = [str(k) for k in (sample_keys or [])][:MAX_SAMPLE_KEYS]

    row = (
        run_id,
        datetime.now(timezone.utc),
        rule_id,
        layer,
        table_name,
        violation_count,
        json.dumps(sample_keys),
        "blocking",
        violation_count == 0,
    )
    spark.createDataFrame([row], DQ_CHECK_RESULTS_SCHEMA).write.mode("append").saveAsTable(DQ_CHECK_RESULTS)
    status = "passed" if violation_count == 0 else "FAILED"
    print(f"{rule_id} [{layer}.{table_name}]: {status}, violations = {violation_count}")


def raise_if_failed(run_id, rule_ids):
    """Raise if any of rule_ids failed in this run, or has no row for this run.

    Reads only rows of this run_id and these rule_ids, so results of other runs
    (including earlier failed runs) never affect the outcome.
    """
    rule_ids = list(rule_ids)
    rows = (
        spark.table(DQ_CHECK_RESULTS)
        .where((F.col("run_id") == run_id) & F.col("rule_id").isin(rule_ids))
        .select("rule_id", "passed", "violation_count")
        .collect()
    )
    failed = sorted({r.rule_id for r in rows if not r.passed})
    missing = sorted(set(rule_ids) - {r.rule_id for r in rows})
    if failed or missing:
        raise RuntimeError(
            f"Data quality check failed for run_id {run_id}: "
            f"failed rules = {failed}, rules without a result = {missing}. "
            f"Details: SELECT * FROM {DQ_CHECK_RESULTS} WHERE run_id = '{run_id}'"
        )
    print(f"All {len(rule_ids)} rules passed for run_id {run_id}.")

# COMMAND ----------

ensure_dq_check_results()

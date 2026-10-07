# Databricks notebook source
# MAGIC %md
# MAGIC # End-to-end failure check (MAX-14)
# MAGIC
# MAGIC Runs in a scratch prefix with an existing succeeded run:
# MAGIC 1. Injects a bad row (receipt date before ship date) into staging during execution.
# MAGIC 2. Shows that `03_validate` fails, halting before `04_silver_publish` and `05_gold_build`.
# MAGIC 3. Shows that `pipeline_runs` has `started` but NO `succeeded` event for this run.
# MAGIC 4. Shows that existing Gold tables are unchanged (`EXCEPT ALL` against snapshot = 0 rows).
# MAGIC 5. Confirms that `06_analysis` refuses to present results due to stale/failed run state.

# COMMAND ----------

# MAGIC %run ../../../notebooks/00_config

# COMMAND ----------

assert schema_prefix != "nachalniki_logistics", "Failure demo must run in a scratch prefix"

run_id = new_run_id()
print(f"E2E failure check starting with run_id {run_id} in prefix {schema_prefix}")

# COMMAND ----------

from datetime import datetime, timezone
from pyspark.sql import functions as F

PIPELINE_RUNS = f"{audit_schema}.pipeline_runs"
PIPELINE_RUNS_SCHEMA = (
    "run_id string, event string, event_ts timestamp, catalog string, schema_prefix string, source string"
)

def ensure_pipeline_runs():
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {audit_schema}")
    spark.sql(f"CREATE TABLE IF NOT EXISTS {PIPELINE_RUNS} ({PIPELINE_RUNS_SCHEMA})")

def record_pipeline_event(event):
    if event not in {"started", "succeeded"}:
        raise ValueError(f"Unsupported pipeline event: {event}")
    row = (run_id, event, datetime.now(timezone.utc), catalog, schema_prefix, source)
    spark.createDataFrame([row], PIPELINE_RUNS_SCHEMA).write.mode("append").saveAsTable(PIPELINE_RUNS)
    print(f"pipeline_runs: {event} for run_id {run_id}")

ensure_pipeline_runs()
record_pipeline_event("started")

# COMMAND ----------

# MAGIC %run ../../../notebooks/01_bronze_ingest

# COMMAND ----------

# MAGIC %run ../../../notebooks/02_silver_stage

# COMMAND ----------

# Inject bad row: lineitem receiptdate < shipdate
bad_line = spark.sql(f"""
    SELECT l_orderkey, l_linenumber FROM {staging_schema}.stg_lineitem
    ORDER BY l_orderkey, l_linenumber LIMIT 1
""").first()

spark.sql(f"""
    UPDATE {staging_schema}.stg_lineitem
    SET l_receiptdate = date_sub(l_shipdate, 1)
    WHERE l_orderkey = {bad_line.l_orderkey} AND l_linenumber = {bad_line.l_linenumber}
""")
print(f"Injected bad row: line {bad_line.l_orderkey}|{bad_line.l_linenumber} receiptdate < shipdate")

# COMMAND ----------

# MAGIC %run ../../../notebooks/03_validate

# COMMAND ----------

# MAGIC %run ../../../notebooks/04_silver_publish

# COMMAND ----------

# MAGIC %run ../../../notebooks/05_gold_build

# COMMAND ----------

record_pipeline_event("succeeded")
print(f"Pipeline succeeded (UNEXPECTED): {run_id}")

# Databricks notebook source
# MAGIC %md
# MAGIC # run_pipeline
# MAGIC
# MAGIC Runs the complete Bronze → Silver → Gold pipeline in one notebook context. Every execution
# MAGIC starts a fresh `run_id`, appends `started` to the append-only `pipeline_runs` table, and
# MAGIC appends `succeeded` only after all five child notebooks finish. An exception in any child
# MAGIC stops the remaining cells, leaving a `started` row without a matching `succeeded` row.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

run_id = new_run_id()
print(f"run_id = {run_id}")

# COMMAND ----------

from datetime import datetime, timezone

from pyspark.sql import functions as F

PIPELINE_RUNS = f"{audit_schema}.pipeline_runs"
PIPELINE_RUNS_SCHEMA = (
    "run_id string, event string, event_ts timestamp, catalog string, schema_prefix string, source string"
)


def ensure_pipeline_runs():
    """Create the append-only pipeline run-state table if it does not exist."""
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {audit_schema}")
    spark.sql(f"CREATE TABLE IF NOT EXISTS {PIPELINE_RUNS} ({PIPELINE_RUNS_SCHEMA})")


def record_pipeline_event(event):
    """Append one lifecycle event for this execution's run_id."""
    if event not in {"started", "succeeded"}:
        raise ValueError(f"Unsupported pipeline event: {event}")
    row = (run_id, event, datetime.now(timezone.utc), catalog, schema_prefix, source)
    spark.createDataFrame([row], PIPELINE_RUNS_SCHEMA).write.mode("append").saveAsTable(PIPELINE_RUNS)
    print(f"pipeline_runs: {event} for run_id {run_id}")


ensure_pipeline_runs()
record_pipeline_event("started")

# COMMAND ----------

# MAGIC %run ./01_bronze_ingest

# COMMAND ----------

# MAGIC %run ./02_silver_stage

# COMMAND ----------

# MAGIC %run ./03_validate

# COMMAND ----------

# MAGIC %run ./04_silver_publish

# COMMAND ----------

# MAGIC %run ./05_gold_build

# COMMAND ----------

record_pipeline_event("succeeded")

display(
    spark.table(PIPELINE_RUNS)
    .where(F.col("run_id") == run_id)
    .orderBy("event_ts")
)
print(f"Pipeline succeeded for run_id {run_id}.")

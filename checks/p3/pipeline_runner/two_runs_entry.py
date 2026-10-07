# Databricks notebook source
# MAGIC %md
# MAGIC # Two consecutive pipeline executions (MAX-09)
# MAGIC
# MAGIC Runs the full pipeline twice in the same notebook context. The second execution must replace
# MAGIC the session's old `run_id` with a fresh one, and append-only audit tables must retain rows from
# MAGIC the first execution.

# COMMAND ----------

# MAGIC %run ../../../notebooks/run_pipeline

# COMMAND ----------

first_run_id = run_id
first_pipeline_rows = spark.table(PIPELINE_RUNS).where(F.col("run_id") == first_run_id).count()
first_dq_rows = spark.table(DQ_CHECK_RESULTS).where(F.col("run_id") == first_run_id).count()
assert first_pipeline_rows == 2
assert first_dq_rows > 0
print(f"first run_id = {first_run_id}, pipeline rows = {first_pipeline_rows}, DQ rows = {first_dq_rows}")

# COMMAND ----------

# MAGIC %run ../../../notebooks/run_pipeline

# COMMAND ----------

second_run_id = run_id
assert second_run_id != first_run_id

retained_pipeline_rows = spark.table(PIPELINE_RUNS).where(F.col("run_id") == first_run_id).count()
retained_dq_rows = spark.table(DQ_CHECK_RESULTS).where(F.col("run_id") == first_run_id).count()
second_pipeline_rows = spark.table(PIPELINE_RUNS).where(F.col("run_id") == second_run_id).count()
second_dq_rows = spark.table(DQ_CHECK_RESULTS).where(F.col("run_id") == second_run_id).count()

assert retained_pipeline_rows == first_pipeline_rows
assert retained_dq_rows == first_dq_rows
assert second_pipeline_rows == 2
assert second_dq_rows == first_dq_rows

display(
    spark.table(PIPELINE_RUNS)
    .where(F.col("run_id").isin([first_run_id, second_run_id]))
    .orderBy("event_ts")
)
print(
    f"MAX-09 two-run check passed: first={first_run_id}, second={second_run_id}, "
    f"retained DQ rows={retained_dq_rows}, second DQ rows={second_dq_rows}"
)

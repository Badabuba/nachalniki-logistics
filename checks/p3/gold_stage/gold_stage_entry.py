# Databricks notebook source
# MAGIC %md
# MAGIC # Gold stage execution (entry notebook)
# MAGIC
# MAGIC Runs `05_gold_build` against an already-published Silver layer with a fresh run id. This is a
# MAGIC stage-level MAX-03 check, not the full pipeline; it writes Gold DQ rows but not `pipeline_runs`.

# COMMAND ----------

# MAGIC %run ../../../notebooks/00_config

# COMMAND ----------

run_id = new_run_id()
print(f"run_id = {run_id}")

# COMMAND ----------

# MAGIC %run ../../../notebooks/05_gold_build

# COMMAND ----------

print(f"Gold stage completed for run_id {run_id}")

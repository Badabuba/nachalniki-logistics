# Databricks notebook source
print(f"child_reads_run_id: on entry run_id={run_id!r}")
child_entry_run_id = run_id

# COMMAND ----------

# MAGIC %run ./config_stub

# COMMAND ----------

print(f"child_reads_run_id: after config_stub run_id={run_id!r}")
child_seen_run_id = run_id

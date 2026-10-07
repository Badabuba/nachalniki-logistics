# Databricks notebook source
# MAGIC %md
# MAGIC # A5 interactive (test notebook, not pipeline code)
# MAGIC Handoff check A5 in an attached notebook session. Attach to compute and click **Run all**
# MAGIC twice in the same session. Each run is one execution: `%run 00_config` → `run_id = new_run_id()`
# MAGIC → `%run` child. The second run must print a different run_id than the first, and the child
# MAGIC must print its caller's id both times.
# MAGIC
# MAGIC Unlike `a5_entry`, this notebook does not assume a clean session, because the second run
# MAGIC starts with the first run's `run_id` still defined.

# COMMAND ----------

# MAGIC %run ../../../notebooks/00_config

# COMMAND ----------

# The previous execution's id, if this session already ran this notebook.
previous_run_id = globals().get("run_id")
print(f"run_id before this execution: {previous_run_id}")

run_id = new_run_id()
print(f"this execution: run_id = {run_id}")
assert run_id != previous_run_id

# COMMAND ----------

# MAGIC %run ./a5_child

# COMMAND ----------

assert child_seen_run_id == run_id
print(f"child saw {child_seen_run_id}")
print(f"A5 interactive OK: previous = {previous_run_id}, this = {run_id}")

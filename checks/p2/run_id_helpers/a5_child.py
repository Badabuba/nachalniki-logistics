# Databricks notebook source
# MAGIC %md
# MAGIC # A5 child (test notebook, not pipeline code)
# MAGIC Reads the caller's run_id with `require_run_id()`. Run on its own, with no caller, it must fail.

# COMMAND ----------

# MAGIC %run ../../../notebooks/00_config

# COMMAND ----------

child_seen_run_id = require_run_id()
print(f"a5_child: require_run_id() = {child_seen_run_id}")

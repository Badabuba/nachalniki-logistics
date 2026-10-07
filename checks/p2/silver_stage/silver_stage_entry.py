# Databricks notebook source
# MAGIC %md
# MAGIC # Silver stage execution (entry notebook)
# MAGIC Design §3.1: `%run 00_config` → `run_id = new_run_id()` → `%run 02` → `%run 03` → `%run 04`, each
# MAGIC in its own cell. Writes `dq_check_results` but not `pipeline_runs`; once `run_pipeline` has
# MAGIC produced Gold in a prefix, use a scratch `schema_prefix` here.
# MAGIC
# MAGIC Failure demo only: widget `inject_bad_row = receipt_before_ship` changes one staged line item so
# MAGIC that it is received one day before it was shipped. `03_validate` must then fail DQ-L2 and raise,
# MAGIC and `04_silver_publish` must not run. The default `none` changes nothing.

# COMMAND ----------

dbutils.widgets.text("inject_bad_row", "none", "inject_bad_row (none | receipt_before_ship)")
inject_bad_row = dbutils.widgets.get("inject_bad_row").strip()
assert inject_bad_row in ("none", "receipt_before_ship"), inject_bad_row

# COMMAND ----------

# MAGIC %run ../../../notebooks/00_config

# COMMAND ----------

run_id = new_run_id()
print(f"Silver stage execution: run_id = {run_id}, schema_prefix = {schema_prefix}, inject_bad_row = {inject_bad_row}")

# COMMAND ----------

# MAGIC %run ../../../notebooks/02_silver_stage

# COMMAND ----------

if inject_bad_row == "receipt_before_ship":
    assert schema_prefix != "nachalniki_logistics", "the failure demo runs only in a scratch prefix"
    bad_line = spark.sql(f"""
        SELECT l_orderkey, l_linenumber FROM {staging_schema}.stg_lineitem
        ORDER BY l_orderkey, l_linenumber LIMIT 1
    """).first()
    spark.sql(f"""
        UPDATE {staging_schema}.stg_lineitem
        SET l_receiptdate = date_sub(l_shipdate, 1)
        WHERE l_orderkey = {bad_line.l_orderkey} AND l_linenumber = {bad_line.l_linenumber}
    """)
    print(f"injected: line {bad_line.l_orderkey}|{bad_line.l_linenumber} now has l_receiptdate = l_shipdate - 1")

# COMMAND ----------

# MAGIC %run ../../../notebooks/03_validate

# COMMAND ----------

# MAGIC %run ../../../notebooks/04_silver_publish

# COMMAND ----------

print(f"Silver stage execution succeeded: run_id = {run_id}")

# Databricks notebook source
# MAGIC %md
# MAGIC # Silver snapshot and comparison (failure demo, not pipeline code)
# MAGIC `action = snapshot` copies every Silver table into `{prefix}_snapshot`.
# MAGIC `action = compare` checks that Silver still equals that snapshot (`EXCEPT ALL` in both
# MAGIC directions, 0 rows expected) and shows the DQ results of the latest run in this prefix.
# MAGIC Runs only in a scratch prefix.

# COMMAND ----------

dbutils.widgets.text("action", "compare", "action (snapshot | compare)")
action = dbutils.widgets.get("action").strip()
assert action in ("snapshot", "compare"), action

# COMMAND ----------

# MAGIC %run ../../../notebooks/00_config

# COMMAND ----------

# MAGIC %run ../../../notebooks/silver_contract

# COMMAND ----------

assert schema_prefix != "nachalniki_logistics", "snapshots are taken only in a scratch prefix"
snapshot_schema = f"{catalog}.{schema_prefix}_snapshot"

if action == "snapshot":
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {snapshot_schema}")
    for t in SILVER_TABLES:
        spark.sql(f"CREATE OR REPLACE TABLE {snapshot_schema}.{t} AS SELECT * FROM {silver_schema}.{t}")
        print(f"snapshot {silver_schema}.{t} -> {snapshot_schema}.{t}")

# COMMAND ----------

if action == "compare":
    rows = []
    for t in SILVER_TABLES:
        silver_minus_snapshot = spark.sql(
            f"SELECT * FROM {silver_schema}.{t} EXCEPT ALL SELECT * FROM {snapshot_schema}.{t}").count()
        snapshot_minus_silver = spark.sql(
            f"SELECT * FROM {snapshot_schema}.{t} EXCEPT ALL SELECT * FROM {silver_schema}.{t}").count()
        rows.append((t, silver_minus_snapshot, snapshot_minus_silver, silver_minus_snapshot + snapshot_minus_silver == 0))
    display(spark.createDataFrame(rows, "table_name string, silver_except_snapshot bigint, snapshot_except_silver bigint, unchanged boolean"))

    latest_run = spark.sql(f"""
        SELECT run_id FROM {audit_schema}.dq_check_results ORDER BY run_ts DESC LIMIT 1
    """).first().run_id
    print(f"latest run_id in dq_check_results: {latest_run}")
    display(spark.sql(f"""
        SELECT rule_id, table_name, violation_count, sample_keys, passed
        FROM {audit_schema}.dq_check_results
        WHERE run_id = '{latest_run}'
        ORDER BY passed, rule_id, table_name
    """))
    assert all(r[-1] for r in rows), "Silver changed"
    print("OK: Silver is unchanged against the snapshot")

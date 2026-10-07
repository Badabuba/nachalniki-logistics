# Databricks notebook source
# MAGIC %md
# MAGIC # 02_silver_stage
# MAGIC
# MAGIC Builds the proposed Silver in `{prefix}_staging` as `stg_<table>`: column selection and casts to
# MAGIC the Silver contract only. No row is filtered and no constraint is added; `03_validate` checks
# MAGIC the staging tables and `04_silver_publish` publishes them only after every rule has passed.
# MAGIC
# MAGIC Run it from a Silver stage execution or `run_pipeline`, never on its own.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %run ./silver_contract

# COMMAND ----------

run_id = require_run_id()
print(f"run_id = {run_id}")

# COMMAND ----------

def staging_select(table_name):
    columns = ", ".join(f"CAST({c} AS {t}) AS {c}" for c, t in SILVER_COLUMNS[table_name])
    source_table = f"{bronze_schema}.{SILVER_SOURCE_TABLES[table_name]}"
    if table_name in DECOMPOSED_TABLES:
        # One row per distinct combination; a duplicated key here means the rule is broken (DQ-G1).
        return f"SELECT DISTINCT {columns} FROM {source_table}"
    return f"SELECT {columns} FROM {source_table}"


spark.sql(f"CREATE SCHEMA IF NOT EXISTS {staging_schema}")
for table_name in SILVER_TABLES:
    spark.sql(f"CREATE OR REPLACE TABLE {staging_schema}.stg_{table_name} AS {staging_select(table_name)}")
    print(f"staged {staging_schema}.stg_{table_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Check: staging matches the contract and keeps every Bronze row

# COMMAND ----------

def compare_staging_with_contract(table_name):
    staged = spark.table(f"{staging_schema}.stg_{table_name}")
    columns_match = staged.dtypes == [(c, t) for c, t in SILVER_COLUMNS[table_name]]
    staging_rows = staged.count()
    if table_name in DECOMPOSED_TABLES:
        bronze_rows = None
        counts_match = True
    else:
        bronze_rows = spark.table(f"{bronze_schema}.{table_name}").count()
        counts_match = staging_rows == bronze_rows
    return (table_name, columns_match, bronze_rows, staging_rows, counts_match, columns_match and counts_match)


results = [compare_staging_with_contract(t) for t in SILVER_TABLES]
display(spark.createDataFrame(
    results,
    "table_name string, columns_match_contract boolean, bronze_rows bigint, staging_rows bigint, "
    "row_counts_match boolean, ok boolean",
))
failed = [r[0] for r in results if not r[-1]]
if failed:
    raise AssertionError(f"staging does not match the contract or Bronze for: {failed}")
print(f"OK: {len(results)} staging tables match the Silver contract; source tables keep every Bronze row.")

# Databricks notebook source
# MAGIC %md
# MAGIC # 01_bronze_ingest
# MAGIC
# MAGIC Copies every source table as-is into `{prefix}_bronze`, adding only two metadata columns:
# MAGIC `_ingested_at` (one timestamp per execution) and `_source_table` (full source table name).
# MAGIC Each table is fully replaced on every run. Bronze does not use `run_id` or audit tables.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

from datetime import datetime, timezone

METADATA_COLUMNS = ["_ingested_at", "_source_table"]

# COMMAND ----------

def ingest_table(table_name, ingested_at):
    spark.sql(f"""
        CREATE OR REPLACE TABLE {bronze_schema}.{table_name} AS
        SELECT *,
               TIMESTAMP'{ingested_at}' AS _ingested_at,
               '{source}.{table_name}' AS _source_table
        FROM {source}.{table_name}
    """)


spark.sql(f"CREATE SCHEMA IF NOT EXISTS {bronze_schema}")

# One timestamp for the whole execution, so all 8 tables can be traced to the same load.
ingested_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
for table_name in TPCH_TABLES:
    ingest_table(table_name, ingested_at)
    print(f"ingested {source}.{table_name} -> {bronze_schema}.{table_name}")
print(f"_ingested_at = {ingested_at} (UTC)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Check: Bronze matches the source
# MAGIC
# MAGIC For each table, the Bronze columns (without the metadata columns) must have the same names,
# MAGIC order and data types as the source, the metadata columns must be present, and the row counts
# MAGIC must be equal. Counts are compared between layers, never against fixed numbers.

# COMMAND ----------

def compare_bronze_with_source(table_name):
    source_df = spark.table(f"{source}.{table_name}")
    bronze_df = spark.table(f"{bronze_schema}.{table_name}")
    source_columns = source_df.dtypes
    bronze_columns = [c for c in bronze_df.dtypes if c[0] not in METADATA_COLUMNS]
    bronze_metadata = [c[0] for c in bronze_df.dtypes if c[0] in METADATA_COLUMNS]
    source_count = source_df.count()
    bronze_count = bronze_df.count()
    columns_match = source_columns == bronze_columns
    metadata_present = bronze_metadata == METADATA_COLUMNS
    counts_match = source_count == bronze_count
    return (
        table_name,
        len(source_columns),
        len(bronze_columns),
        columns_match,
        metadata_present,
        source_count,
        bronze_count,
        counts_match,
        columns_match and metadata_present and counts_match,
    )


results = [compare_bronze_with_source(t) for t in TPCH_TABLES]
display(spark.createDataFrame(
    results,
    "table_name string, source_columns int, bronze_columns int, names_and_types_match boolean, "
    "metadata_columns_present boolean, source_rows bigint, bronze_rows bigint, row_counts_match boolean, ok boolean",
))

failed = [r[0] for r in results if not r[-1]]
if failed:
    raise AssertionError(f"Bronze does not match the source for: {failed}")
print(f"OK: {len(results)} Bronze tables match {source} (column names, types, row counts).")

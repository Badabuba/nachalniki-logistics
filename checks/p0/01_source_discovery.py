# Databricks notebook source
# MAGIC %md
# MAGIC # P0 source discovery (NAZ-01, NAZ-02; read-only)
# MAGIC
# MAGIC Diagnostic notebook for plan.md NAZ-01 (catalogs) and NAZ-02 (source inventory).
# MAGIC It only reads. It has no `%run` and does not depend on `00_config` or any pipeline table.
# MAGIC Row counts are displayed for the evidence log only; no logic compares against a number.
# MAGIC
# MAGIC Run all cells top to bottom and copy every output into the evidence log.

# COMMAND ----------

import re

dbutils.widgets.text("source", "samples.tpch", "source (<catalog>.<schema>)")
source = dbutils.widgets.get("source").strip()

_ident = r"[A-Za-z0-9_][A-Za-z0-9_-]*"
if not re.fullmatch(rf"{_ident}\.{_ident}", source):
    raise ValueError(f"source must be <catalog>.<schema>, got {source!r}")
source_cat, source_schema = source.split(".")
source_q = f"`{source_cat}`.`{source_schema}`"
print(f"source = {source}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## NAZ-01 — catalogs and the current catalog

# COMMAND ----------

display(spark.sql("SHOW CATALOGS"))

# COMMAND ----------

display(spark.sql("SELECT current_catalog() AS current_catalog, current_schema() AS current_schema"))

# COMMAND ----------

# Compute version, recorded as evidence for which runtime the checks ran on.
print(f"spark.version = {spark.version}")
try:
    display(spark.sql("SELECT current_version() AS current_version"))
except Exception as e:
    print(f"current_version() not available: {type(e).__name__}: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## NAZ-02 — tables in the source

# COMMAND ----------

tables_df = spark.sql(f"SHOW TABLES IN {source_q}")
display(tables_df)

observed_tables = sorted(r["tableName"] for r in tables_df.collect())
# Documented TPC-H table names (design §4). Names only, never counts.
expected_tables = sorted(["region", "nation", "supplier", "customer", "part", "partsupp", "orders", "lineitem"])
missing = sorted(set(expected_tables) - set(observed_tables))
unexpected = sorted(set(observed_tables) - set(expected_tables))
print(f"observed ({len(observed_tables)}): {observed_tables}")
print(f"missing vs documented: {missing}")
print(f"unexpected vs documented: {unexpected}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## NAZ-02 — row counts (reference only)

# COMMAND ----------

count_rows = []
for t in observed_tables:
    n = spark.sql(f"SELECT count(*) AS n FROM {source_q}.`{t}`").collect()[0]["n"]
    count_rows.append((t, int(n)))
display(spark.createDataFrame(count_rows, "table_name string, row_count bigint"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## NAZ-02 — `DESCRIBE TABLE` for every table

# COMMAND ----------

describe_rows = []
for t in observed_tables:
    for pos, r in enumerate(spark.sql(f"DESCRIBE TABLE {source_q}.`{t}`").collect(), start=1):
        describe_rows.append((t, pos, r["col_name"], r["data_type"], r["comment"]))
display(spark.createDataFrame(
    describe_rows,
    "table_name string, position int, col_name string, data_type string, comment string",
))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

if missing or unexpected:
    raise AssertionError(f"Source tables differ from the documented 8: missing={missing}, unexpected={unexpected}")
print(f"OK: {source} has exactly the 8 documented TPC-H tables.")

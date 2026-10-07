# Databricks notebook source
# MAGIC %md
# MAGIC # 03_validate
# MAGIC
# MAGIC Runs every blocking rule of design §6 on the staging tables (DQ-G3 also reads the source and
# MAGIC Bronze), records one result row per rule and table in `{prefix}_audit.dq_check_results` with up
# MAGIC to 10 sample keys, and ends with `raise_if_failed` for this run. If any rule fails, the run
# MAGIC stops here and `04_silver_publish` does not execute.
# MAGIC
# MAGIC Late deliveries (`l_receiptdate > l_commitdate`) are valid data and have no rule.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %run ./silver_contract

# COMMAND ----------

# MAGIC %run ./dq_helpers

# COMMAND ----------

from pyspark.sql import functions as F

run_id = require_run_id()
print(f"run_id = {run_id}")


def stg(table_name):
    return spark.table(f"{staging_schema}.stg_{table_name}")


def record_violations(rule_id, table_name, violations, key_columns):
    """Record a rule whose violating rows are the rows of `violations`."""
    violation_count = violations.count()
    sample_keys = [
        r.k for r in violations.select(F.concat_ws("|", *key_columns).alias("k")).limit(MAX_SAMPLE_KEYS).collect()
    ]
    record_dq_result(run_id, rule_id, "staging", table_name, violation_count, sample_keys)


LINE_KEY = ["l_orderkey", "l_linenumber"]
lineitem = stg("lineitem")
orders = stg("orders")
lines_with_orders = lineitem.join(orders, lineitem.l_orderkey == orders.o_orderkey, "inner")

# COMMAND ----------

# MAGIC %md
# MAGIC ## V1: dates make sense (DQ-L1–L4)
# MAGIC Equality passes: same-day ship, receipt and commit are valid.

# COMMAND ----------

record_violations("DQ-L1", "lineitem", lines_with_orders.where("l_shipdate < o_orderdate"), LINE_KEY)
record_violations("DQ-L2", "lineitem", lineitem.where("l_receiptdate < l_shipdate"), LINE_KEY)
record_violations("DQ-L3", "lineitem", lines_with_orders.where("l_commitdate < o_orderdate"), LINE_KEY)
record_violations(
    "DQ-L4", "lineitem",
    lineitem.where("l_shipdate IS NULL OR l_commitdate IS NULL OR l_receiptdate IS NULL"), LINE_KEY,
)
record_violations("DQ-L4", "orders", orders.where("o_orderdate IS NULL"), ["o_orderkey"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## V2: categorical values are in the allowed lists (DQ-L5–L7)
# MAGIC `l_linestatus` lives in `ship_date_status` after the 3NF decomposition; that table holds every
# MAGIC `(l_shipdate, l_linestatus)` pair of the staged line items, so any unexpected value appears there.

# COMMAND ----------

def outside_allowed(df, column, allowed_values):
    return df.where(F.col(column).isNull() | ~F.col(column).isin(allowed_values))


record_violations("DQ-L5", "lineitem", outside_allowed(lineitem, "l_shipmode", ALLOWED_SHIP_MODES), LINE_KEY)
record_violations("DQ-L6", "lineitem", outside_allowed(lineitem, "l_returnflag", ALLOWED_RETURN_FLAGS), LINE_KEY)
record_violations(
    "DQ-L7", "ship_date_status",
    outside_allowed(stg("ship_date_status"), "l_linestatus", ALLOWED_LINE_STATUSES), ["l_shipdate"],
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## V3: orders and line items reference each other (DQ-L8, DQ-L9)

# COMMAND ----------

record_violations(
    "DQ-L8", "lineitem",
    lineitem.join(orders, lineitem.l_orderkey == orders.o_orderkey, "left_anti"), LINE_KEY,
)
record_violations(
    "DQ-L9", "orders",
    orders.join(lineitem, orders.o_orderkey == lineitem.l_orderkey, "left_anti"), ["o_orderkey"],
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Keys and references of every Silver table (DQ-G1, DQ-G2)
# MAGIC DQ-G1: a primary key is NULL or duplicated (sample keys are the duplicated or NULL keys).
# MAGIC DQ-G2: a foreign key has no matching parent row (anti join on all key columns).

# COMMAND ----------

for table_name, key_columns in SILVER_PRIMARY_KEYS.items():
    staged = stg(table_name)
    any_null = " OR ".join(f"{c} IS NULL" for c in key_columns)
    null_keys = staged.where(any_null).select(*key_columns)
    duplicate_keys = staged.groupBy(*key_columns).count().where("count > 1").select(*key_columns)
    record_violations("DQ-G1", table_name, null_keys.unionByName(duplicate_keys), key_columns)

for name, child, child_columns, parent, parent_columns in SILVER_FOREIGN_KEYS:
    child_df = stg(child).select(*child_columns).alias("c")
    parent_df = stg(parent).select(*parent_columns).alias("p")
    condition = [F.col(f"c.{cc}") == F.col(f"p.{pc}") for cc, pc in zip(child_columns, parent_columns)]
    orphans = child_df.join(parent_df, condition, "left_anti")
    record_violations("DQ-G2", f"{child}.{name}", orphans, child_columns)

# COMMAND ----------

# MAGIC %md
# MAGIC ## No silent loss between source, Bronze and staging (DQ-G3)
# MAGIC For each source table, the violation count is the total row difference between the layers.

# COMMAND ----------

for table_name in TPCH_TABLES:
    source_rows = spark.table(f"{source}.{table_name}").count()
    bronze_rows = spark.table(f"{bronze_schema}.{table_name}").count()
    staging_rows = stg(table_name).count()
    difference = abs(source_rows - bronze_rows) + abs(bronze_rows - staging_rows)
    sample = [] if difference == 0 else [f"source={source_rows}", f"bronze={bronze_rows}", f"staging={staging_rows}"]
    record_dq_result(run_id, "DQ-G3", "staging", table_name, difference, sample)

# COMMAND ----------

VALIDATE_RULE_IDS = [f"DQ-L{i}" for i in range(1, 10)] + ["DQ-G1", "DQ-G2", "DQ-G3"]
display(
    spark.table(DQ_CHECK_RESULTS)
    .where(F.col("run_id") == run_id)
    .where(F.col("rule_id").isin(VALIDATE_RULE_IDS))
    .orderBy("rule_id", "table_name")
)
raise_if_failed(run_id, VALIDATE_RULE_IDS)

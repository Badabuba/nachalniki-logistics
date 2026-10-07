# Databricks notebook source
# MAGIC %md
# MAGIC # profile_source
# MAGIC
# MAGIC Profiles Bronze (an as-is copy of the source) to build the allowed-value lists and to record
# MAGIC the date ranges and the lines-per-order distribution. Read-only: it writes no tables.
# MAGIC
# MAGIC Requires `01_bronze_ingest` to have run for the same `catalog` and `schema_prefix`.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC ## Value profiling
# MAGIC
# MAGIC ### Categorical values
# MAGIC Every distinct value with its row count. NULL appears as its own row. `value_length` and the
# MAGIC bracketed value make leading or trailing whitespace visible.

# COMMAND ----------

lineitem_values = spark.sql(f"""
    SELECT column_name, concat('[', value, ']') AS bracketed_value, length(value) AS value_length,
           count(*) AS row_count
    FROM (
        SELECT stack(3,
                     'l_shipmode', l_shipmode,
                     'l_returnflag', l_returnflag,
                     'l_linestatus', l_linestatus) AS (column_name, value)
        FROM {bronze_schema}.lineitem
    )
    GROUP BY column_name, value
    ORDER BY column_name, value
""")
display(lineitem_values)

# COMMAND ----------

order_priority_values = spark.sql(f"""
    SELECT 'o_orderpriority' AS column_name, concat('[', o_orderpriority, ']') AS bracketed_value,
           length(o_orderpriority) AS value_length, count(*) AS row_count
    FROM {bronze_schema}.orders
    GROUP BY o_orderpriority
    ORDER BY o_orderpriority
""")
display(order_priority_values)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Date ranges

# COMMAND ----------

date_ranges = spark.sql(f"""
    SELECT 'l_shipdate' AS column_name, min(l_shipdate) AS min_date, max(l_shipdate) AS max_date,
           count_if(l_shipdate IS NULL) AS null_count
    FROM {bronze_schema}.lineitem
    UNION ALL
    SELECT 'l_commitdate', min(l_commitdate), max(l_commitdate), count_if(l_commitdate IS NULL)
    FROM {bronze_schema}.lineitem
    UNION ALL
    SELECT 'l_receiptdate', min(l_receiptdate), max(l_receiptdate), count_if(l_receiptdate IS NULL)
    FROM {bronze_schema}.lineitem
    UNION ALL
    SELECT 'o_orderdate', min(o_orderdate), max(o_orderdate), count_if(o_orderdate IS NULL)
    FROM {bronze_schema}.orders
""")
display(date_ranges)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Lines per order
# MAGIC Starts from every order, so an order without line items counts as 0 lines instead of being
# MAGIC left out.

# COMMAND ----------

lines_per_order = spark.sql(f"""
    WITH line_counts AS (
        SELECT l_orderkey, count(*) AS line_count
        FROM {bronze_schema}.lineitem
        GROUP BY l_orderkey
    ),
    order_lines AS (
        SELECT o.o_orderkey, coalesce(lc.line_count, 0) AS line_count
        FROM {bronze_schema}.orders AS o
        LEFT JOIN line_counts AS lc ON lc.l_orderkey = o.o_orderkey
    )
    SELECT count(*) AS order_count,
           count_if(line_count = 0) AS orders_without_lines,
           min(line_count) AS lines_min,
           percentile_cont(0.5) WITHIN GROUP (ORDER BY line_count) AS lines_median,
           avg(line_count) AS lines_mean,
           max(line_count) AS lines_max
    FROM order_lines
""")
display(lines_per_order)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Functional dependencies
# MAGIC Added in a separate section by the Silver stage (candidate-key and FD tests).

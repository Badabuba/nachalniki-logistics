# Databricks notebook source
# MAGIC %md
# MAGIC # 05_gold_build
# MAGIC
# MAGIC Builds the eight Logistics Gold tables from the published Silver `orders` and `lineitem`
# MAGIC tables. Line metrics come only from the line-grain fact; order metrics come only from the
# MAGIC order-grain fact, so aggregations cannot multiply rows.
# MAGIC
# MAGIC Run this notebook from `run_pipeline` or another entry notebook that has assigned a fresh
# MAGIC `run_id`. It records DQ-GOLD1 and DQ-GOLD2 and fails if either fact loses or duplicates rows.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %run ./dq_helpers

# COMMAND ----------

from pyspark.sql import functions as F

run_id = require_run_id()
print(f"run_id = {run_id}")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {gold_schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Facts

# COMMAND ----------

spark.sql(f"""
    CREATE OR REPLACE TABLE {gold_schema}.fct_lineitem_delivery AS
    SELECT
        l.l_orderkey AS order_key,
        l.l_linenumber AS line_number,
        o.o_orderdate AS order_date,
        o.o_orderpriority AS order_priority,
        o.o_orderpriority = '1-URGENT' AS is_urgent,
        l.l_shipmode AS ship_mode,
        l.l_shipdate AS ship_date,
        l.l_commitdate AS commit_date,
        l.l_receiptdate AS receipt_date,
        datediff(l.l_receiptdate, l.l_shipdate) AS transit_days,
        datediff(l.l_shipdate, o.o_orderdate) AS order_to_ship_days,
        l.l_receiptdate > l.l_commitdate AS is_late,
        CAST(date_trunc('MONTH', l.l_commitdate) AS DATE) AS commit_month
    FROM {silver_schema}.lineitem AS l
    INNER JOIN {silver_schema}.orders AS o
      ON o.o_orderkey = l.l_orderkey
""")

spark.sql(f"""
    CREATE OR REPLACE TABLE {gold_schema}.fct_order_fulfillment AS
    WITH line_rollup AS (
        SELECT
            l_orderkey AS order_key,
            COUNT(*) AS line_count,
            SUM(CASE WHEN l_receiptdate > l_commitdate THEN 1 ELSE 0 END) AS late_line_count,
            MIN(l_shipdate) AS first_ship_date,
            MAX(l_receiptdate) AS last_receipt_date
        FROM {silver_schema}.lineitem
        GROUP BY l_orderkey
    )
    SELECT
        o.o_orderkey AS order_key,
        o.o_orderdate AS order_date,
        o.o_orderpriority AS order_priority,
        o.o_orderpriority = '1-URGENT' AS is_urgent,
        COALESCE(r.line_count, 0) AS line_count,
        COALESCE(r.late_line_count, 0) AS late_line_count,
        COALESCE(r.line_count, 0) >= 1 AND COALESCE(r.late_line_count, 0) = 0 AS is_fully_on_time,
        r.first_ship_date,
        r.last_receipt_date,
        datediff(r.last_receipt_date, o.o_orderdate) AS order_to_complete_days
    FROM {silver_schema}.orders AS o
    LEFT JOIN line_rollup AS r
      ON r.order_key = o.o_orderkey
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Q1 and Q3: shipping-mode performance

# COMMAND ----------

spark.sql(f"""
    CREATE OR REPLACE TABLE {gold_schema}.agg_ship_mode_performance AS
    WITH metrics AS (
        SELECT
            ship_mode,
            COUNT(*) AS line_count,
            percentile_cont(0.25) WITHIN GROUP (ORDER BY transit_days) AS transit_p25_days,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY transit_days) AS transit_p50_days,
            percentile_cont(0.75) WITHIN GROUP (ORDER BY transit_days) AS transit_p75_days,
            percentile_cont(0.90) WITHIN GROUP (ORDER BY transit_days) AS transit_p90_days,
            AVG(transit_days) AS transit_mean_days,
            stddev_pop(transit_days) AS transit_stddev_days,
            SUM(CASE WHEN is_late THEN 1 ELSE 0 END) AS late_line_count
        FROM {gold_schema}.fct_lineitem_delivery
        GROUP BY ship_mode
    )
    SELECT
        ship_mode,
        line_count,
        transit_p50_days,
        transit_p90_days,
        transit_p90_days - transit_p50_days AS transit_p90_minus_p50_days,
        transit_p75_days - transit_p25_days AS transit_iqr_days,
        transit_mean_days,
        transit_stddev_days,
        late_line_count,
        CAST(late_line_count AS DOUBLE) / line_count AS delay_rate
    FROM metrics
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Q2: line and order on-time performance

# COMMAND ----------

spark.sql(f"""
    CREATE OR REPLACE TABLE {gold_schema}.agg_on_time_summary AS
    WITH order_metrics AS (
        SELECT
            COUNT(*) AS order_count,
            SUM(CASE WHEN is_fully_on_time THEN 1 ELSE 0 END) AS fully_on_time_order_count,
            MIN(line_count) AS lines_per_order_min,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY line_count) AS lines_per_order_p50,
            AVG(line_count) AS lines_per_order_mean,
            MAX(line_count) AS lines_per_order_max
        FROM {gold_schema}.fct_order_fulfillment
        WHERE line_count >= 1
    ),
    line_metrics AS (
        SELECT
            COUNT(*) AS line_count,
            SUM(CASE WHEN NOT is_late THEN 1 ELSE 0 END) AS on_time_line_count
        FROM {gold_schema}.fct_lineitem_delivery
    )
    SELECT
        o.order_count,
        o.fully_on_time_order_count,
        CAST(o.fully_on_time_order_count AS DOUBLE) / o.order_count AS order_on_time_share,
        l.line_count,
        l.on_time_line_count,
        CAST(l.on_time_line_count AS DOUBLE) / l.line_count AS line_on_time_share,
        o.lines_per_order_min,
        o.lines_per_order_p50,
        o.lines_per_order_mean,
        o.lines_per_order_max
    FROM order_metrics AS o
    CROSS JOIN line_metrics AS l
""")

spark.sql(f"""
    CREATE OR REPLACE TABLE {gold_schema}.agg_on_time_by_line_count AS
    SELECT
        line_count AS lines_in_order,
        COUNT(*) AS order_count,
        SUM(CASE WHEN is_fully_on_time THEN 1 ELSE 0 END) AS fully_on_time_order_count,
        CAST(SUM(CASE WHEN is_fully_on_time THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) AS order_on_time_share,
        CAST(SUM(line_count - late_line_count) AS DOUBLE) / SUM(line_count) AS line_on_time_share
    FROM {gold_schema}.fct_order_fulfillment
    WHERE line_count >= 1
    GROUP BY line_count
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Q4: priority and urgency
# MAGIC Order completion metrics use the order fact. Transit and order-to-ship metrics use the line fact.

# COMMAND ----------

spark.sql(f"""
    CREATE OR REPLACE TABLE {gold_schema}.agg_priority_fulfillment AS
    WITH order_metrics AS (
        SELECT
            order_priority,
            is_urgent,
            COUNT(*) AS order_count,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY order_to_complete_days) AS complete_p50_days,
            percentile_cont(0.90) WITHIN GROUP (ORDER BY order_to_complete_days) AS complete_p90_days,
            AVG(order_to_complete_days) AS complete_mean_days
        FROM {gold_schema}.fct_order_fulfillment
        WHERE line_count >= 1
        GROUP BY order_priority, is_urgent
    ),
    line_metrics AS (
        SELECT
            order_priority,
            is_urgent,
            COUNT(*) AS line_count,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY transit_days) AS transit_p50_days,
            percentile_cont(0.90) WITHIN GROUP (ORDER BY transit_days) AS transit_p90_days,
            AVG(transit_days) AS transit_mean_days,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY order_to_ship_days) AS order_to_ship_p50_days,
            percentile_cont(0.90) WITHIN GROUP (ORDER BY order_to_ship_days) AS order_to_ship_p90_days,
            AVG(order_to_ship_days) AS order_to_ship_mean_days
        FROM {gold_schema}.fct_lineitem_delivery
        GROUP BY order_priority, is_urgent
    )
    SELECT
        o.order_priority,
        o.is_urgent,
        o.order_count,
        o.complete_p50_days,
        o.complete_p90_days,
        o.complete_mean_days,
        l.line_count,
        l.transit_p50_days,
        l.transit_p90_days,
        l.transit_mean_days,
        l.order_to_ship_p50_days,
        l.order_to_ship_p90_days,
        l.order_to_ship_mean_days
    FROM order_metrics AS o
    INNER JOIN line_metrics AS l
      ON l.order_priority = o.order_priority AND l.is_urgent = o.is_urgent
""")

spark.sql(f"""
    CREATE OR REPLACE TABLE {gold_schema}.agg_urgency_fulfillment AS
    WITH order_metrics AS (
        SELECT
            is_urgent,
            COUNT(*) AS order_count,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY order_to_complete_days) AS complete_p50_days,
            percentile_cont(0.90) WITHIN GROUP (ORDER BY order_to_complete_days) AS complete_p90_days,
            AVG(order_to_complete_days) AS complete_mean_days
        FROM {gold_schema}.fct_order_fulfillment
        WHERE line_count >= 1
        GROUP BY is_urgent
    ),
    line_metrics AS (
        SELECT
            is_urgent,
            COUNT(*) AS line_count,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY transit_days) AS transit_p50_days,
            percentile_cont(0.90) WITHIN GROUP (ORDER BY transit_days) AS transit_p90_days,
            AVG(transit_days) AS transit_mean_days,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY order_to_ship_days) AS order_to_ship_p50_days,
            percentile_cont(0.90) WITHIN GROUP (ORDER BY order_to_ship_days) AS order_to_ship_p90_days,
            AVG(order_to_ship_days) AS order_to_ship_mean_days
        FROM {gold_schema}.fct_lineitem_delivery
        GROUP BY is_urgent
    )
    SELECT
        o.is_urgent,
        o.order_count,
        o.complete_p50_days,
        o.complete_p90_days,
        o.complete_mean_days,
        l.line_count,
        l.transit_p50_days,
        l.transit_p90_days,
        l.transit_mean_days,
        l.order_to_ship_p50_days,
        l.order_to_ship_p90_days,
        l.order_to_ship_mean_days
    FROM order_metrics AS o
    INNER JOIN line_metrics AS l
      ON l.is_urgent = o.is_urgent
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monitoring: delay rate by commit month

# COMMAND ----------

spark.sql(f"""
    CREATE OR REPLACE TABLE {gold_schema}.agg_delay_rate_monthly AS
    WITH monthly AS (
        SELECT
            commit_month,
            COUNT(*) AS line_count,
            SUM(CASE WHEN is_late THEN 1 ELSE 0 END) AS late_line_count
        FROM {gold_schema}.fct_lineitem_delivery
        GROUP BY commit_month
    ),
    boundaries AS (
        SELECT MIN(commit_month) AS first_month, MAX(commit_month) AS last_month
        FROM monthly
    )
    SELECT
        m.commit_month,
        m.line_count,
        m.late_line_count,
        CAST(m.late_line_count AS DOUBLE) / m.line_count AS delay_rate,
        m.commit_month = b.first_month OR m.commit_month = b.last_month AS is_boundary_month
    FROM monthly AS m
    CROSS JOIN boundaries AS b
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Contract and reconciliation checks

# COMMAND ----------

GOLD_COLUMNS = {
    "fct_lineitem_delivery": [
        "order_key", "line_number", "order_date", "order_priority", "is_urgent", "ship_mode",
        "ship_date", "commit_date", "receipt_date", "transit_days", "order_to_ship_days", "is_late",
        "commit_month",
    ],
    "fct_order_fulfillment": [
        "order_key", "order_date", "order_priority", "is_urgent", "line_count", "late_line_count",
        "is_fully_on_time", "first_ship_date", "last_receipt_date", "order_to_complete_days",
    ],
    "agg_ship_mode_performance": [
        "ship_mode", "line_count", "transit_p50_days", "transit_p90_days",
        "transit_p90_minus_p50_days", "transit_iqr_days", "transit_mean_days",
        "transit_stddev_days", "late_line_count", "delay_rate",
    ],
    "agg_on_time_summary": [
        "order_count", "fully_on_time_order_count", "order_on_time_share", "line_count",
        "on_time_line_count", "line_on_time_share", "lines_per_order_min", "lines_per_order_p50",
        "lines_per_order_mean", "lines_per_order_max",
    ],
    "agg_on_time_by_line_count": [
        "lines_in_order", "order_count", "fully_on_time_order_count", "order_on_time_share",
        "line_on_time_share",
    ],
    "agg_priority_fulfillment": [
        "order_priority", "is_urgent", "order_count", "complete_p50_days", "complete_p90_days",
        "complete_mean_days", "line_count", "transit_p50_days", "transit_p90_days",
        "transit_mean_days", "order_to_ship_p50_days", "order_to_ship_p90_days",
        "order_to_ship_mean_days",
    ],
    "agg_urgency_fulfillment": [
        "is_urgent", "order_count", "complete_p50_days", "complete_p90_days", "complete_mean_days",
        "line_count", "transit_p50_days", "transit_p90_days", "transit_mean_days",
        "order_to_ship_p50_days", "order_to_ship_p90_days", "order_to_ship_mean_days",
    ],
    "agg_delay_rate_monthly": [
        "commit_month", "line_count", "late_line_count", "delay_rate", "is_boundary_month",
    ],
}

contract_results = []
for table_name, expected_columns in GOLD_COLUMNS.items():
    actual_columns = spark.table(f"{gold_schema}.{table_name}").columns
    columns_match = actual_columns == expected_columns
    row_count = spark.table(f"{gold_schema}.{table_name}").count()
    contract_results.append((table_name, row_count, columns_match))

display(spark.createDataFrame(
    contract_results,
    "table_name string, row_count bigint, columns_match_contract boolean",
).orderBy("table_name"))

bad_contracts = [table_name for table_name, _, ok in contract_results if not ok]
if bad_contracts:
    raise AssertionError(f"Gold columns do not match the Gold contract for: {bad_contracts}")

silver_line_count = spark.table(f"{silver_schema}.lineitem").count()
gold_line_count = spark.table(f"{gold_schema}.fct_lineitem_delivery").count()
line_difference = abs(silver_line_count - gold_line_count)
line_sample = [] if line_difference == 0 else [f"silver={silver_line_count}", f"gold={gold_line_count}"]
record_dq_result(run_id, "DQ-GOLD1", "gold", "fct_lineitem_delivery", line_difference, line_sample)

silver_order_count = spark.table(f"{silver_schema}.orders").count()
gold_order_count = spark.table(f"{gold_schema}.fct_order_fulfillment").count()
order_difference = abs(silver_order_count - gold_order_count)
order_sample = [] if order_difference == 0 else [f"silver={silver_order_count}", f"gold={gold_order_count}"]
record_dq_result(run_id, "DQ-GOLD2", "gold", "fct_order_fulfillment", order_difference, order_sample)

GOLD_RULE_IDS = ["DQ-GOLD1", "DQ-GOLD2"]
display(
    spark.table(DQ_CHECK_RESULTS)
    .where(F.col("run_id") == run_id)
    .where(F.col("rule_id").isin(GOLD_RULE_IDS))
    .orderBy("rule_id")
)
raise_if_failed(run_id, GOLD_RULE_IDS)
print(f"OK: {len(GOLD_COLUMNS)} Gold tables match the Gold contract for run_id {run_id}.")

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
# MAGIC
# MAGIC 3NF evidence (design §5.3): candidate keys, then each candidate non-key dependency `X → A`.
# MAGIC A dependency holds in this snapshot when no value of `X` has more than one distinct `A`.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Candidate keys
# MAGIC Declared primary keys must be unique and non-null. Name columns are checked as possible
# MAGIC alternative keys; an alternative key does not break 3NF, it only makes more attributes prime.

# COMMAND ----------

PRIMARY_KEYS = {
    "region": ["r_regionkey"],
    "nation": ["n_nationkey"],
    "supplier": ["s_suppkey"],
    "customer": ["c_custkey"],
    "part": ["p_partkey"],
    "partsupp": ["ps_partkey", "ps_suppkey"],
    "orders": ["o_orderkey"],
    "lineitem": ["l_orderkey", "l_linenumber"],
}
ALTERNATIVE_KEY_CANDIDATES = {
    "region": ["r_name"],
    "nation": ["n_name"],
    "supplier": ["s_name"],
    "customer": ["c_name"],
    "part": ["p_name"],
}


def key_check(table_name, key_columns, kind):
    columns = ", ".join(key_columns)
    any_null = " OR ".join(f"{c} IS NULL" for c in key_columns)
    return spark.sql(f"""
        SELECT '{table_name}' AS table_name, '{columns}' AS key_columns, '{kind}' AS kind,
               count(*) AS row_count,
               count(DISTINCT {columns}) AS distinct_keys,
               count_if({any_null}) AS rows_with_null_key,
               count(*) = count(DISTINCT {columns}) AND count_if({any_null}) = 0 AS is_key
        FROM {bronze_schema}.{table_name}
    """)


key_checks = [key_check(t, cols, "primary key") for t, cols in PRIMARY_KEYS.items()]
key_checks += [key_check(t, cols, "alternative candidate") for t, cols in ALTERNATIVE_KEY_CANDIDATES.items()]
candidate_keys = key_checks[0]
for df in key_checks[1:]:
    candidate_keys = candidate_keys.unionByName(df)
display(candidate_keys)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Candidate non-key dependencies
# MAGIC Candidates from design §5.3. `violating_groups` counts values of `X` with more than one
# MAGIC distinct `A`; 0 means the dependency holds in this snapshot. `A` may be an expression
# MAGIC (the phone prefix).

# COMMAND ----------

FD_CANDIDATES = [
    ("part", ["p_brand"], "p_mfgr"),
    ("lineitem", ["l_shipdate"], "l_linestatus"),
    ("lineitem", ["l_receiptdate"], "l_returnflag"),
    ("lineitem", ["l_partkey", "l_quantity"], "l_extendedprice"),
    ("customer", ["c_nationkey"], "substring(c_phone, 1, 2)"),
    ("supplier", ["s_nationkey"], "substring(s_phone, 1, 2)"),
]


def fd_check(table_name, determinant, dependent):
    columns = ", ".join(determinant)
    return spark.sql(f"""
        SELECT '{table_name}' AS table_name, '{columns}' AS determinant, '{dependent}' AS dependent,
               count(*) AS determinant_values,
               count_if(dependent_values > 1) AS violating_groups,
               count_if(dependent_values > 1) = 0 AS holds_in_data
        FROM (
            SELECT {columns}, count(DISTINCT {dependent}) AS dependent_values
            FROM {bronze_schema}.{table_name}
            GROUP BY {columns}
        )
    """)


fd_results = fd_check(*FD_CANDIDATES[0])
for candidate in FD_CANDIDATES[1:]:
    fd_results = fd_results.unionByName(fd_check(*candidate))
display(fd_results)

# COMMAND ----------

# The specification sets o_shippriority to 0 for every order: a constant column, i.e. a dependency
# with an empty determinant.
display(spark.sql(f"""
    SELECT count(DISTINCT o_shippriority) AS distinct_values, min(o_shippriority) AS min_value,
           max(o_shippriority) AS max_value
    FROM {bronze_schema}.orders
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Documented rules behind the candidates
# MAGIC Each count compares the data with the generation rule in the TPC-H specification. 0 rows
# MAGIC means every row follows the rule.
# MAGIC - `p_brand` is `Brand#MN`, where `M` is the manufacturer number of `p_mfgr` (`Manufacturer#M`).
# MAGIC - `l_linestatus` is `O` when `l_shipdate` is after the snapshot date, otherwise `F`: the latest
# MAGIC   `F` ship date must be earlier than the earliest `O` ship date.
# MAGIC - `l_extendedprice` is `l_quantity * p_retailprice`.
# MAGIC - The phone country code is `nationkey + 10`.

# COMMAND ----------

documented_rules = spark.sql(f"""
    SELECT 'p_brand digit M = p_mfgr number' AS rule,
           count_if(substring(p_brand, 7, 1) <> substring(p_mfgr, 14)) AS rows_breaking_rule
    FROM {bronze_schema}.part
    UNION ALL
    SELECT 'l_extendedprice = l_quantity * p_retailprice',
           count_if(l.l_extendedprice <> l.l_quantity * p.p_retailprice)
    FROM {bronze_schema}.lineitem AS l
    JOIN {bronze_schema}.part AS p ON p.p_partkey = l.l_partkey
    UNION ALL
    SELECT 'c_phone country code = c_nationkey + 10',
           count_if(cast(substring(c_phone, 1, 2) AS int) <> c_nationkey + 10)
    FROM {bronze_schema}.customer
    UNION ALL
    SELECT 's_phone country code = s_nationkey + 10',
           count_if(cast(substring(s_phone, 1, 2) AS int) <> s_nationkey + 10)
    FROM {bronze_schema}.supplier
""")
display(documented_rules)

# The snapshot-date cutoffs behind l_linestatus (ship date) and l_returnflag (receipt date: N after
# the cutoff, R or A on or before it).
snapshot_cutoffs = spark.sql(f"""
    SELECT max(CASE WHEN l_linestatus = 'F' THEN l_shipdate END) AS latest_f_shipdate,
           min(CASE WHEN l_linestatus = 'O' THEN l_shipdate END) AS earliest_o_shipdate,
           max(CASE WHEN l_returnflag IN ('A', 'R') THEN l_receiptdate END) AS latest_a_or_r_receiptdate,
           min(CASE WHEN l_returnflag = 'N' THEN l_receiptdate END) AS earliest_n_receiptdate
    FROM {bronze_schema}.lineitem
""")
display(snapshot_cutoffs)

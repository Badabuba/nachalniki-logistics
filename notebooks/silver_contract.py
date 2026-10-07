# Databricks notebook source
# MAGIC %md
# MAGIC # silver_contract
# MAGIC
# MAGIC The Silver contract (design §5.1) in one place, loaded with `%run ./silver_contract` by
# MAGIC `02_silver_stage`, `03_validate` and `04_silver_publish`: tables and typed columns, where each
# MAGIC table comes from in Bronze, primary keys, foreign keys and the enforced constraints.
# MAGIC
# MAGIC Three tables are 3NF decompositions of documented TPC-H generation rules (design §5.3–5.4):
# MAGIC `brand` (`p_brand → p_mfgr`), `ship_date_status` (`l_shipdate → l_linestatus`) and
# MAGIC `part_quantity_price` (`(l_partkey, l_quantity) → l_extendedprice`). Each holds one row per
# MAGIC distinct determinant value; if the data ever broke the rule, its primary key would be
# MAGIC duplicated and DQ-G1 would block the run.

# COMMAND ----------

SILVER_COLUMNS = {
    "region": [("r_regionkey", "bigint"), ("r_name", "string"), ("r_comment", "string")],
    "nation": [("n_nationkey", "bigint"), ("n_name", "string"), ("n_regionkey", "bigint"), ("n_comment", "string")],
    "supplier": [
        ("s_suppkey", "bigint"), ("s_name", "string"), ("s_address", "string"), ("s_nationkey", "bigint"),
        ("s_phone", "string"), ("s_acctbal", "decimal(18,2)"), ("s_comment", "string"),
    ],
    "customer": [
        ("c_custkey", "bigint"), ("c_name", "string"), ("c_address", "string"), ("c_nationkey", "bigint"),
        ("c_phone", "string"), ("c_acctbal", "decimal(18,2)"), ("c_mktsegment", "string"), ("c_comment", "string"),
    ],
    "brand": [("p_brand", "string"), ("p_mfgr", "string")],
    "part": [
        ("p_partkey", "bigint"), ("p_name", "string"), ("p_brand", "string"), ("p_type", "string"),
        ("p_size", "int"), ("p_container", "string"), ("p_retailprice", "decimal(18,2)"), ("p_comment", "string"),
    ],
    "partsupp": [
        ("ps_partkey", "bigint"), ("ps_suppkey", "bigint"), ("ps_availqty", "int"),
        ("ps_supplycost", "decimal(18,2)"), ("ps_comment", "string"),
    ],
    "orders": [
        ("o_orderkey", "bigint"), ("o_custkey", "bigint"), ("o_orderstatus", "string"),
        ("o_totalprice", "decimal(18,2)"), ("o_orderdate", "date"), ("o_orderpriority", "string"),
        ("o_clerk", "string"), ("o_shippriority", "int"), ("o_comment", "string"),
    ],
    "ship_date_status": [("l_shipdate", "date"), ("l_linestatus", "string")],
    "part_quantity_price": [("l_partkey", "bigint"), ("l_quantity", "decimal(18,2)"), ("l_extendedprice", "decimal(18,2)")],
    "lineitem": [
        ("l_orderkey", "bigint"), ("l_partkey", "bigint"), ("l_suppkey", "bigint"), ("l_linenumber", "int"),
        ("l_quantity", "decimal(18,2)"), ("l_discount", "decimal(18,2)"), ("l_tax", "decimal(18,2)"),
        ("l_returnflag", "string"), ("l_shipdate", "date"), ("l_commitdate", "date"), ("l_receiptdate", "date"),
        ("l_shipinstruct", "string"), ("l_shipmode", "string"), ("l_comment", "string"),
    ],
}

# Bronze table each Silver table is built from. The decomposed tables take the distinct values
# of their columns from the source table they were split off.
SILVER_SOURCE_TABLES = {t: t for t in SILVER_COLUMNS}
SILVER_SOURCE_TABLES.update({"brand": "part", "ship_date_status": "lineitem", "part_quantity_price": "lineitem"})
DECOMPOSED_TABLES = ["brand", "ship_date_status", "part_quantity_price"]

SILVER_PRIMARY_KEYS = {
    "region": ["r_regionkey"],
    "nation": ["n_nationkey"],
    "supplier": ["s_suppkey"],
    "customer": ["c_custkey"],
    "brand": ["p_brand"],
    "part": ["p_partkey"],
    "partsupp": ["ps_partkey", "ps_suppkey"],
    "orders": ["o_orderkey"],
    "ship_date_status": ["l_shipdate"],
    "part_quantity_price": ["l_partkey", "l_quantity"],
    "lineitem": ["l_orderkey", "l_linenumber"],
}

# (constraint name, child table, child columns, parent table, parent columns)
SILVER_FOREIGN_KEYS = [
    ("nation_region_fk", "nation", ["n_regionkey"], "region", ["r_regionkey"]),
    ("supplier_nation_fk", "supplier", ["s_nationkey"], "nation", ["n_nationkey"]),
    ("customer_nation_fk", "customer", ["c_nationkey"], "nation", ["n_nationkey"]),
    ("part_brand_fk", "part", ["p_brand"], "brand", ["p_brand"]),
    ("partsupp_part_fk", "partsupp", ["ps_partkey"], "part", ["p_partkey"]),
    ("partsupp_supplier_fk", "partsupp", ["ps_suppkey"], "supplier", ["s_suppkey"]),
    ("orders_customer_fk", "orders", ["o_custkey"], "customer", ["c_custkey"]),
    ("part_quantity_price_part_fk", "part_quantity_price", ["l_partkey"], "part", ["p_partkey"]),
    ("lineitem_orders_fk", "lineitem", ["l_orderkey"], "orders", ["o_orderkey"]),
    ("lineitem_partsupp_fk", "lineitem", ["l_partkey", "l_suppkey"], "partsupp", ["ps_partkey", "ps_suppkey"]),
    ("lineitem_ship_date_status_fk", "lineitem", ["l_shipdate"], "ship_date_status", ["l_shipdate"]),
    ("lineitem_part_quantity_price_fk", "lineitem", ["l_partkey", "l_quantity"], "part_quantity_price", ["l_partkey", "l_quantity"]),
]

# Enforced at publish, in addition to NOT NULL on every primary-key column.
SILVER_NOT_NULL = {
    "orders": ["o_orderdate"],
    "lineitem": ["l_shipdate", "l_commitdate", "l_receiptdate", "l_shipmode", "l_returnflag"],
    "ship_date_status": ["l_linestatus"],
}
SILVER_CHECKS = {
    "lineitem": [("lineitem_receipt_after_ship", "l_receiptdate >= l_shipdate")],
}

# Order in which tables are published: every parent before its children.
SILVER_TABLES = list(SILVER_COLUMNS)

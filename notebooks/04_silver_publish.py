# Databricks notebook source
# MAGIC %md
# MAGIC # 04_silver_publish
# MAGIC
# MAGIC Publishes the validated staging tables to `{prefix}_silver`, then adds the constraints:
# MAGIC `NOT NULL` and `CHECK` (enforced), primary and foreign keys (informational: Databricks does not
# MAGIC enforce them, referential integrity is proven by DQ-G2 in `03_validate`).
# MAGIC
# MAGIC Runs only after `03_validate` has passed in the same execution: if validation raised, the
# MAGIC cells of this notebook never run and Silver keeps its previous content.
# MAGIC If an enforced constraint rejects data here, the validation has a bug and the run fails.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %run ./silver_contract

# COMMAND ----------

run_id = require_run_id()
print(f"run_id = {run_id}")


def silver_table_exists(table_name):
    return spark.catalog.tableExists(f"{silver_schema}.{table_name}")


spark.sql(f"CREATE SCHEMA IF NOT EXISTS {silver_schema}")

# Foreign keys of the previous publication are dropped first, so the parent tables can be replaced.
for name, child, _, _, _ in SILVER_FOREIGN_KEYS:
    if silver_table_exists(child):
        spark.sql(f"ALTER TABLE {silver_schema}.{child} DROP CONSTRAINT IF EXISTS {name}")

# COMMAND ----------

for table_name in SILVER_TABLES:
    spark.sql(f"CREATE OR REPLACE TABLE {silver_schema}.{table_name} AS SELECT * FROM {staging_schema}.stg_{table_name}")
    print(f"published {silver_schema}.{table_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Constraints

# COMMAND ----------

for table_name in SILVER_TABLES:
    full_name = f"{silver_schema}.{table_name}"
    for column in SILVER_PRIMARY_KEYS[table_name] + SILVER_NOT_NULL.get(table_name, []):
        spark.sql(f"ALTER TABLE {full_name} ALTER COLUMN {column} SET NOT NULL")
    # Dropped first in case the replaced table kept constraints of the previous publication.
    for name, expression in SILVER_CHECKS.get(table_name, []):
        spark.sql(f"ALTER TABLE {full_name} DROP CONSTRAINT IF EXISTS {name}")
        spark.sql(f"ALTER TABLE {full_name} ADD CONSTRAINT {name} CHECK ({expression})")
    key = ", ".join(SILVER_PRIMARY_KEYS[table_name])
    spark.sql(f"ALTER TABLE {full_name} DROP CONSTRAINT IF EXISTS {table_name}_pk")
    spark.sql(f"ALTER TABLE {full_name} ADD CONSTRAINT {table_name}_pk PRIMARY KEY ({key})")

for name, child, child_columns, parent, parent_columns in SILVER_FOREIGN_KEYS:
    spark.sql(f"""
        ALTER TABLE {silver_schema}.{child} ADD CONSTRAINT {name}
        FOREIGN KEY ({", ".join(child_columns)}) REFERENCES {silver_schema}.{parent} ({", ".join(parent_columns)})
    """)
print("constraints added")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Check: Silver equals staging and carries the constraints

# COMMAND ----------

def compare_silver_with_staging(table_name):
    silver_rows = spark.table(f"{silver_schema}.{table_name}").count()
    staging_rows = spark.table(f"{staging_schema}.stg_{table_name}").count()
    return (table_name, staging_rows, silver_rows, staging_rows == silver_rows)


counts = [compare_silver_with_staging(t) for t in SILVER_TABLES]
display(spark.createDataFrame(counts, "table_name string, staging_rows bigint, silver_rows bigint, ok boolean"))
if not all(r[-1] for r in counts):
    raise AssertionError("Silver row counts differ from staging")

display(spark.sql(f"""
    SELECT tc.table_name, tc.constraint_name, tc.constraint_type,
           concat_ws(', ', transform(array_sort(collect_list(struct(kcu.ordinal_position, kcu.column_name))),
                                     x -> x.column_name)) AS columns
    FROM {catalog}.information_schema.table_constraints AS tc
    LEFT JOIN {catalog}.information_schema.key_column_usage AS kcu
      ON kcu.constraint_schema = tc.constraint_schema AND kcu.constraint_name = tc.constraint_name
    WHERE tc.table_schema = '{schema_prefix}_silver'
    GROUP BY tc.table_name, tc.constraint_name, tc.constraint_type
    ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name
"""))

display(spark.sql(f"""
    SELECT table_name, column_name, is_nullable
    FROM {catalog}.information_schema.columns
    WHERE table_schema = '{schema_prefix}_silver' AND is_nullable = 'NO'
    ORDER BY table_name, ordinal_position
"""))
# CHECK constraints are stored as table properties (delta.constraints.<name>).
for table_name in SILVER_CHECKS:
    display(spark.sql(f"SHOW TBLPROPERTIES {silver_schema}.{table_name}").where("key LIKE 'delta.constraints.%'"))
print(f"OK: {len(counts)} Silver tables published for run_id {run_id}.")

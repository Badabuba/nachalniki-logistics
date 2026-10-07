# Databricks notebook source
# MAGIC %md
# MAGIC # P0 workspace capability checks (NAZ-03)
# MAGIC
# MAGIC Diagnostic notebook for plan.md NAZ-03. In the catalog given by the `write_catalog` widget it:
# MAGIC 1. creates a **new, uniquely named** scratch schema (never `IF NOT EXISTS`, never an existing schema);
# MAGIC 2. checks table creation, an enforced `CHECK` constraint, an informational `PRIMARY KEY` and `percentile_cont`;
# MAGIC 3. drops **only** the table and schema this run created (no `CASCADE`), even if a check fails.
# MAGIC
# MAGIC It has no `%run` and does not depend on `00_config` or any pipeline table.
# MAGIC Set `write_catalog`, then run all cells. The last cell prints and displays the results table
# MAGIC after cleanup, then raises if anything failed.

# COMMAND ----------

dbutils.widgets.text("write_catalog", "", "write_catalog (required)")

# COMMAND ----------

import re
import secrets
from datetime import datetime, timezone

write_catalog = dbutils.widgets.get("write_catalog").strip()
if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_-]*", write_catalog):
    raise ValueError(f"Set the write_catalog widget to a plain catalog name, got {write_catalog!r}")

schema_name = (
    f"nachalniki_access_check_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}_{secrets.token_hex(2)}"
)
cat_q = f"`{write_catalog}`"
schema_q = f"{cat_q}.`{schema_name}`"
table_q = f"{schema_q}.`t`"

PCT_TOL = 1e-9
results = []          # (step, status, detail); status is ok / fail / info
created_schema = False
created_table = False


class CheckFailed(Exception):
    pass


def record(step, status, detail=""):
    results.append((step, status, str(detail)[:2000]))
    print(f"[{status.upper():4}] {step}: {detail}")


def run(sql):
    # collect() forces execution on every compute type, including Spark Connect.
    return spark.sql(sql).collect()


def schema_matches():
    rows = run(f"SHOW SCHEMAS IN {cat_q} LIKE '{schema_name}'")
    return [r[0] for r in rows if r[0].lower() == schema_name.lower()]


def row_count():
    return run(f"SELECT count(*) AS n FROM {table_q}")[0]["n"]


def close(x, y):
    return x is not None and abs(float(x) - y) <= PCT_TOL


def run_checks():
    global created_schema, created_table

    # 1. The name must not exist yet.
    existing = schema_matches()
    if existing:
        raise CheckFailed(f"schema {schema_name} already exists; nothing touched, rerun for a new name")
    record("1 name is unused", "ok", f"{write_catalog}.{schema_name}")

    # 2. Create the schema without IF NOT EXISTS, so an existing schema can never be adopted.
    run(f"CREATE SCHEMA {schema_q}")
    created_schema = True
    record("2 create schema", "ok", f"CREATE SCHEMA {write_catalog}.{schema_name}")

    # 3. Create the table.
    run(f"CREATE TABLE {table_q} (a INT NOT NULL, b INT) USING DELTA")
    created_table = True
    record("3 create table", "ok", "t (a INT NOT NULL, b INT) USING DELTA")

    # 4. Add the CHECK constraint.
    run(f"ALTER TABLE {table_q} ADD CONSTRAINT b_chk CHECK (b >= a)")
    props = run(f"SHOW TBLPROPERTIES {table_q} ('delta.constraints.b_chk')")
    record("4 add CHECK b_chk", "ok", f"delta.constraints.b_chk = {props[0]['value'] if props else '<not shown>'}")

    # 5. The invalid row must be rejected by b_chk, not by an unrelated error.
    try:
        run(f"INSERT INTO {table_q} VALUES (2, 1)")
    except Exception as e:
        sqlstate = e.getSqlState() if hasattr(e, "getSqlState") else None
        condition = None
        for attr in ("getCondition", "getErrorClass"):
            if hasattr(e, attr):
                condition = getattr(e, attr)()
                break
        msg = str(e)
        detail = f"sqlstate={sqlstate}, condition={condition}, message={msg.splitlines()[0] if msg else ''}"
        sqlstate_ok = sqlstate == "23001" if sqlstate is not None else "CHECK constraint" in msg
        if not (sqlstate_ok and "b_chk" in msg):
            raise CheckFailed(f"invalid insert failed for an unexpected reason: {detail}")
        record("5a invalid insert (2,1) rejected by b_chk", "ok", detail)
    else:
        raise CheckFailed("invalid insert (2,1) was accepted; CHECK is not enforced")
    n = row_count()
    if n != 0:
        raise CheckFailed(f"table has {n} rows after the rejected insert, expected 0")
    record("5b nothing written by the rejected insert", "ok", "count(*) = 0")

    # 6. A valid row is accepted.
    run(f"INSERT INTO {table_q} VALUES (1, 2)")
    n = row_count()
    if n != 1:
        raise CheckFailed(f"count(*) = {n} after the valid insert, expected 1")
    record("6 valid insert (1,2) accepted", "ok", "count(*) = 1")

    # 7. Informational primary key: the declaration works, and duplicates are not rejected.
    run(f"ALTER TABLE {table_q} ADD CONSTRAINT t_pk PRIMARY KEY (a)")
    record("7a declare PRIMARY KEY t_pk (a)", "ok", "ALTER TABLE ... ADD CONSTRAINT t_pk PRIMARY KEY (a)")
    ext = run(f"DESCRIBE TABLE EXTENDED {table_q}")
    pk_rows = [" | ".join(str(v) for v in r) for r in ext if any("t_pk" in str(v) for v in r)]
    record("7b t_pk shown by DESCRIBE TABLE EXTENDED", "ok" if pk_rows else "fail",
           "; ".join(pk_rows) if pk_rows else "no row mentions t_pk")
    try:
        run(f"INSERT INTO {table_q} VALUES (1, 3)")
        record("7c duplicate key (1,3) accepted: PK is informational", "ok", f"count(*) = {row_count()}")
    except Exception as e:
        record("7c duplicate key (1,3) rejected: PK is enforced, design assumes informational", "fail",
               f"{type(e).__name__}: {str(e).splitlines()[0]}")

    # 8. percentile_cont on the table, and an exact interpolation check on literal values.
    p_tab = run(f"SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY a) AS p50 FROM {table_q}")[0]["p50"]
    record("8a percentile_cont(0.5) on t", "ok" if close(p_tab, 1.0) else "fail", f"p50 = {p_tab} (expected 1.0)")
    lit = run(
        "SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY x) AS p50, "
        "percentile_cont(0.9) WITHIN GROUP (ORDER BY x) AS p90 "
        "FROM VALUES (1), (2), (3), (4) AS v(x)"
    )[0]
    ok = close(lit["p50"], 2.5) and close(lit["p90"], 3.7)
    record("8b percentile_cont interpolation on 1..4", "ok" if ok else "fail",
           f"p50 = {lit['p50']} (expected 2.5), p90 = {lit['p90']} (expected 3.7), tolerance {PCT_TOL}")


def cleanup():
    # Drop only what this run created. Each step is independent so one failure does not skip the next.
    if created_table:
        try:
            run(f"DROP TABLE {table_q}")
            record("cleanup drop table", "ok", f"{schema_name}.t")
        except Exception as e:
            record("cleanup drop table", "fail", f"{type(e).__name__}: {e}")
    if created_schema:
        try:
            run(f"DROP SCHEMA {schema_q}")
            record("cleanup drop schema", "ok", schema_name)
        except Exception as e:
            record("cleanup drop schema", "fail", f"{type(e).__name__}: {e}")
        try:
            left = schema_matches()
            record("cleanup schema is gone", "fail" if left else "ok",
                   f"SHOW SCHEMAS LIKE returned {left}" if left else "SHOW SCHEMAS LIKE returned 0 rows")
        except Exception as e:
            record("cleanup schema is gone", "fail", f"could not verify: {type(e).__name__}: {e}")


# COMMAND ----------

# Checks, cleanup and the results table run in this one cell, so cleanup and reporting
# happen even when a check fails.
primary_error = None
try:
    run_checks()
except BaseException as e:
    primary_error = e
    record("aborted", "fail", f"{type(e).__name__}: {e}")

cleanup()

failed = [r for r in results if r[1] == "fail"]
cleanup_failed = [r for r in failed if r[0].startswith("cleanup")]
overall = "PASSED" if not failed and primary_error is None else "FAILED"
record("overall", "ok" if overall == "PASSED" else "fail",
       f"{overall}: catalog={write_catalog}, schema={schema_name}, failures={len(failed)}, "
       f"cleanup failures={len(cleanup_failed)}")

print()
for step, status, detail in results:
    print(f"{status:4} | {step} | {detail}")
try:
    display(spark.createDataFrame(results, "step string, status string, detail string"))
except Exception as e:
    print(f"(could not display results as a table: {type(e).__name__}: {e})")

if cleanup_failed:
    print(f"CLEANUP FAILED: drop {write_catalog}.{schema_name} manually after checking it contains only table t.")
if primary_error is not None:
    raise primary_error
if failed:
    raise CheckFailed(f"{len(failed)} step(s) failed: {[r[0] for r in failed]}")

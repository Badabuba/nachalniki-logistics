# Databricks notebook source
# MAGIC %md
# MAGIC # dq_helpers test (test notebook, not pipeline code)
# MAGIC Checks `dq_helpers` in a scratch `schema_prefix`:
# MAGIC (a) `dq_check_results` keeps earlier rows across runs, (b) a failing row of the active run
# MAGIC raises, (c) a failing row of an earlier run does not affect the active run, and a rule with
# MAGIC no row raises. Run it twice as a job: the second run must still see the first run's rows.
# MAGIC Uses rule IDs `TEST-*` only.

# COMMAND ----------

# MAGIC %run ../../../notebooks/00_config

# COMMAND ----------

# Only a scratch prefix: this test writes test rows into {prefix}_audit.
assert schema_prefix.endswith("_dqtest"), f"use a scratch prefix ending in _dqtest, got {schema_prefix!r}"

# COMMAND ----------

# MAGIC %run ../../../notebooks/dq_helpers

# COMMAND ----------

def expect_raise(rule_ids, active_run_id):
    try:
        raise_if_failed(active_run_id, rule_ids)
    except RuntimeError as e:
        print(f"OK, raised as expected: {e}")
        return
    raise AssertionError(f"raise_if_failed({rule_ids}) did not raise")


rows_before = spark.table(DQ_CHECK_RESULTS).count()
run_ids_before = [r.run_id for r in spark.table(DQ_CHECK_RESULTS).select("run_id").distinct().collect()]
print(f"rows before this test run: {rows_before}, earlier run_ids: {run_ids_before}")

# COMMAND ----------

# Execution A: TEST-1 fails, TEST-2 passes.
run_id = new_run_id()
run_a = require_run_id()
record_dq_result(run_a, "TEST-1", "staging", "lineitem", 3, ["1|1", "1|2", "2|1"])
record_dq_result(run_a, "TEST-2", "staging", "orders", 0, [])

expect_raise(["TEST-1"], run_a)            # (b) failing row of the active run raises
expect_raise(["TEST-1", "TEST-2"], run_a)
raise_if_failed(run_a, ["TEST-2"])         # a passing rule alone does not raise

# COMMAND ----------

# Execution B: both rules pass. The failed TEST-1 row of execution A must not matter.
run_id = new_run_id()
run_b = require_run_id()
assert run_b != run_a
record_dq_result(run_b, "TEST-1", "staging", "lineitem", 0, [])
record_dq_result(run_b, "TEST-2", "staging", "orders", 0, [])

raise_if_failed(run_b, ["TEST-1", "TEST-2"])   # (c) earlier failed run is ignored
expect_raise(["TEST-3"], run_b)                # a rule with no row for this run is a failure

# COMMAND ----------

# (a) earlier rows are kept: every run_id seen before this test run is still present.
rows_after = spark.table(DQ_CHECK_RESULTS).count()
run_ids_after = {r.run_id for r in spark.table(DQ_CHECK_RESULTS).select("run_id").distinct().collect()}
assert rows_after == rows_before + 4, (rows_before, rows_after)
assert set(run_ids_before) <= run_ids_after
display(spark.table(DQ_CHECK_RESULTS).orderBy("run_ts"))
print(f"dq_helpers test OK: run A = {run_a}, run B = {run_b}; rows {rows_before} -> {rows_after}; "
      f"earlier run_ids kept: {len(run_ids_before)}")

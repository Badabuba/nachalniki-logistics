# Databricks notebook source
# MAGIC %md
# MAGIC # A5 entry (test notebook, not pipeline code)
# MAGIC Checks the run_id helpers of `00_config` (handoff checks A1 and A5) inside ONE execution
# MAGIC context: two consecutive executions are simulated by repeating the entry sequence
# MAGIC (`%run 00_config` → `run_id = new_run_id()` → `%run` child) twice in the same notebook.

# COMMAND ----------

# MAGIC %run ../../../notebooks/00_config

# COMMAND ----------

# A1: every name is defined after %run ./00_config.
expected_names = [
    "catalog", "schema_prefix", "source",
    "bronze_schema", "staging_schema", "silver_schema", "gold_schema", "audit_schema",
    "TPCH_TABLES", "ALLOWED_SHIP_MODES", "ALLOWED_RETURN_FLAGS", "ALLOWED_LINE_STATUSES",
    "new_run_id", "require_run_id",
]
missing_names = [n for n in expected_names if n not in globals()]
for n in expected_names:
    if n in globals() and not callable(globals()[n]):
        print(f"{n} = {globals()[n]!r}")
assert not missing_names, f"missing names: {missing_names}"
assert "run_id" not in globals(), "00_config must not assign run_id"
print("A1 OK: all config names defined; 00_config did not assign run_id")

# COMMAND ----------

# Before any execution starts, require_run_id() must fail.
try:
    require_run_id()
    raise AssertionError("require_run_id() did not raise without a run_id")
except RuntimeError as e:
    print(f"OK: require_run_id() without run_id raised RuntimeError: {e}")

# COMMAND ----------

# Execution 1
run_id = new_run_id()
execution_1_run_id = run_id
print(f"execution 1: run_id = {run_id}")

# COMMAND ----------

# MAGIC %run ./a5_child

# COMMAND ----------

assert child_seen_run_id == execution_1_run_id
execution_1_child_seen = child_seen_run_id
print(f"execution 1: child saw {child_seen_run_id}")

# COMMAND ----------

# Execution 2 in the same context: config is loaded again while run_id from execution 1 still exists.

# COMMAND ----------

# MAGIC %run ../../../notebooks/00_config

# COMMAND ----------

assert run_id == execution_1_run_id, "re-running 00_config changed run_id"
print(f"after second %run 00_config, run_id is still execution 1's: {run_id}")
run_id = new_run_id()
execution_2_run_id = run_id
print(f"execution 2: run_id = {run_id}")

# COMMAND ----------

# MAGIC %run ./a5_child

# COMMAND ----------

assert child_seen_run_id == execution_2_run_id
assert execution_2_run_id != execution_1_run_id
print(f"execution 2: child saw {child_seen_run_id}")
print(f"A5 OK in one context: execution 1 = {execution_1_run_id}, execution 2 = {execution_2_run_id}")

# Databricks notebook source
# MAGIC %run ./config_stub

# COMMAND ----------

import uuid
run_id = str(uuid.uuid4())
original_run_id = run_id
print(f"t3 caller: assigned run_id={run_id!r}")

# COMMAND ----------

# MAGIC %run ./child_reads_run_id

# COMMAND ----------

print(f"t3 caller: after child run_id={run_id!r}, child_entry_run_id={child_entry_run_id!r}, child_seen_run_id={child_seen_run_id!r}")
assert child_entry_run_id == original_run_id
assert child_seen_run_id == original_run_id
assert run_id == original_run_id
print("t3 RESULT: caller run_id visible in child and unchanged after nested %run of config_stub")

# Databricks notebook source
# MAGIC %run ./config_stub

# COMMAND ----------

print(f"t1 caller: CONFIG_LOADED={CONFIG_LOADED}, catalog={catalog!r}")
assert CONFIG_LOADED is True
print("t1 RESULT: variables from %run child are visible in caller")

# Databricks notebook source
print("t2 caller: before %run")

# COMMAND ----------

# MAGIC %run ./child_raises

# COMMAND ----------

print("t2 caller: after %run (SHOULD NOT RUN)")

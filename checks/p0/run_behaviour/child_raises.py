# Databricks notebook source
print("child_raises: before raise")
raise RuntimeError("NAZ-04 deliberate failure")

# COMMAND ----------

print("child_raises: after raise (SHOULD NOT RUN)")

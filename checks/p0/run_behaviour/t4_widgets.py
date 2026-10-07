# Databricks notebook source
dbutils.widgets.text("caller_widget", "caller_default")

# COMMAND ----------

# MAGIC %run ./config_stub

# COMMAND ----------

caller_catalog = dbutils.widgets.get("catalog")
caller_caller_widget = dbutils.widgets.get("caller_widget")
print(f"t4 caller: catalog={caller_catalog!r}, caller_widget={caller_caller_widget!r}")

# COMMAND ----------

# MAGIC %run ./child_reads_widgets

# COMMAND ----------

assert child_catalog == caller_catalog
assert child_caller_widget == caller_caller_widget
print("t4 RESULT: %run child read the same widget values as the caller")

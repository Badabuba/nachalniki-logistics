# Databricks notebook source
# Stand-in for 00_config: creates a widget and a variable, never assigns run_id.
dbutils.widgets.text("catalog", "stub_default")
catalog = dbutils.widgets.get("catalog")
CONFIG_LOADED = True
print(f"config_stub: catalog={catalog!r}, CONFIG_LOADED={CONFIG_LOADED}")

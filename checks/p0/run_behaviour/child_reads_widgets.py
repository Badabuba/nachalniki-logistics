# Databricks notebook source
child_catalog = dbutils.widgets.get("catalog")
child_caller_widget = dbutils.widgets.get("caller_widget")
print(f"child_reads_widgets: catalog={child_catalog!r}, caller_widget={child_caller_widget!r}")

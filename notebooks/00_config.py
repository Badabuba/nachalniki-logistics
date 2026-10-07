# Databricks notebook source
# MAGIC %md
# MAGIC # 00_config
# MAGIC
# MAGIC Shared configuration. Every other notebook loads it with `%run ./00_config` and takes
# MAGIC catalog, schema and source names only from here.
# MAGIC
# MAGIC This notebook never assigns `run_id`. An entry notebook starts a run with
# MAGIC `run_id = new_run_id()`; child notebooks read it with `require_run_id()`.

# COMMAND ----------

import re
import uuid

dbutils.widgets.text("catalog", "workspace", "catalog")
dbutils.widgets.text("schema_prefix", "nachalniki_logistics", "schema_prefix")
dbutils.widgets.text("source", "samples.tpch", "source (<catalog>.<schema>)")

catalog = dbutils.widgets.get("catalog").strip()
schema_prefix = dbutils.widgets.get("schema_prefix").strip()
source = dbutils.widgets.get("source").strip()

# Names are put into SQL unquoted, so only plain identifiers are accepted.
_identifier = r"[A-Za-z0-9_]+"
if not re.fullmatch(_identifier, catalog):
    raise ValueError(f"catalog must be a plain identifier, got {catalog!r}")
if not re.fullmatch(_identifier, schema_prefix):
    raise ValueError(f"schema_prefix must be a plain identifier, got {schema_prefix!r}")
if not re.fullmatch(rf"{_identifier}\.{_identifier}", source):
    raise ValueError(f"source must be <catalog>.<schema>, got {source!r}")

bronze_schema = f"{catalog}.{schema_prefix}_bronze"
staging_schema = f"{catalog}.{schema_prefix}_staging"
silver_schema = f"{catalog}.{schema_prefix}_silver"
gold_schema = f"{catalog}.{schema_prefix}_gold"
audit_schema = f"{catalog}.{schema_prefix}_audit"

TPCH_TABLES = ["region", "nation", "supplier", "customer", "part", "partsupp", "orders", "lineitem"]

# COMMAND ----------

# Allowed categorical values (validation rules DQ-L5–L7).
# Built by profiling Bronze (profile_source, 2026-10-07) and cross-checked against the
# TPC-H Standard Specification rev. 3.0.1: ship modes from the "Modes" list (clause 4.2.2.13),
# return flag and line status from the LINEITEM generation rules (clause 4.2.3).
# Every value below was both observed in the data and documented; no value was observed
# without being documented, and no documented value was missing from the data.
ALLOWED_SHIP_MODES = ["AIR", "FOB", "MAIL", "RAIL", "REG AIR", "SHIP", "TRUCK"]
ALLOWED_RETURN_FLAGS = ["A", "N", "R"]
ALLOWED_LINE_STATUSES = ["F", "O"]

# COMMAND ----------

def new_run_id():
    """Return a fresh run id. Entry notebooks call this once per execution."""
    return str(uuid.uuid4())


def require_run_id():
    """Return the run_id set by the calling entry notebook, or fail if there is none."""
    run_id = globals().get("run_id")
    if not run_id:
        raise RuntimeError(
            "run_id is not defined. Start from an entry notebook that runs "
            "`run_id = new_run_id()` after `%run ./00_config`."
        )
    return run_id

# COMMAND ----------

print(f"catalog={catalog!r}, schema_prefix={schema_prefix!r}, source={source!r}")

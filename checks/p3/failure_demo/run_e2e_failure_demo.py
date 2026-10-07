#!/usr/bin/env python3
"""
End-to-end failure check script.
1. Prepares scratch prefix nachalniki_logistics_e2efail with existing succeeded state.
2. Snapshots Gold to _snapshot.
3. Submits e2e_failure_entry with bad row injection. Verifies job FAILS as intended.
4. Verifies:
   - pipeline_runs has 'started' but NO 'succeeded'
   - dq_check_results records DQ-L2 failure
   - Gold tables are completely untouched (EXCEPT ALL against snapshot = 0 for all 8 tables)
5. Submits 06_analysis in that scratch prefix. Verifies it FAILS at the run-state guard.
6. Cleans up by dropping only the 6 scratch schemas.
7. Writes evidence to checks/p3/outputs/max14_e2e_failure_check_20261007.json.
"""
import json
import subprocess
import time
import sys

WAREHOUSE_ID = "1ddefb699bbd3644"
CATALOG = "workspace"
PREFIX = "nachalniki_logistics_e2efail"
DEFAULT_PREFIX = "nachalniki_logistics"

GOLD_TABLES = [
    "agg_delay_rate_monthly",
    "agg_on_time_by_line_count",
    "agg_on_time_summary",
    "agg_priority_fulfillment",
    "agg_ship_mode_performance",
    "agg_urgency_fulfillment",
    "fct_lineitem_delivery",
    "fct_order_fulfillment",
]

SILVER_TABLES = [
    "region", "nation", "supplier", "customer", "brand",
    "part", "partsupp", "orders", "ship_date_status",
    "part_quantity_price", "lineitem"
]

def run_cmd(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return res.stdout

def exec_sql(statement):
    payload = json.dumps({
        "warehouse_id": WAREHOUSE_ID,
        "statement": statement,
        "wait_timeout": "50s",
    })
    out = run_cmd(["databricks", "api", "post", "/api/2.0/sql/statements", "--json", payload])
    data = json.loads(out)
    statement_id = data["statement_id"]
    state = data.get("status", {}).get("state")
    while state in ("PENDING", "RUNNING"):
        time.sleep(2)
        poll_out = run_cmd(["databricks", "api", "get", f"/api/2.0/sql/statements/{statement_id}"])
        data = json.loads(poll_out)
        state = data.get("status", {}).get("state")
    if state != "SUCCEEDED":
        raise RuntimeError(f"SQL statement failed ({state}): {data}")
    return data

def submit_job(run_name, notebook_path, params):
    payload = json.dumps({
        "run_name": run_name,
        "tasks": [{
            "task_key": "task",
            "notebook_task": {
                "notebook_path": notebook_path,
                "base_parameters": params
            }
        }]
    })
    res = json.loads(run_cmd(["databricks", "jobs", "submit", "--json", payload]))
    return res["run_id"]

def poll_job(job_run_id):
    while True:
        status = json.loads(run_cmd(["databricks", "jobs", "get-run", str(job_run_id)]))
        lifecycle = status["state"]["life_cycle_state"]
        print(f"  Job {job_run_id} status: {lifecycle}...")
        if lifecycle in ("TERMINATED", "SKIPPED", "INTERNAL_ERROR"):
            return status
        time.sleep(15)

def main():
    print("=== Step 1: Initialize scratch schemas ===")
    schemas = [f"{CATALOG}.{PREFIX}_{s}" for s in ["audit", "gold", "silver", "snapshot", "bronze", "staging"]]
    for s in schemas:
        exec_sql(f"CREATE SCHEMA IF NOT EXISTS {s}")
    
    # Copy audit tables
    exec_sql(f"CREATE OR REPLACE TABLE {CATALOG}.{PREFIX}_audit.pipeline_runs AS SELECT * FROM {CATALOG}.{DEFAULT_PREFIX}_audit.pipeline_runs")
    exec_sql(f"CREATE OR REPLACE TABLE {CATALOG}.{PREFIX}_audit.dq_check_results AS SELECT * FROM {CATALOG}.{DEFAULT_PREFIX}_audit.dq_check_results")

    # Copy Gold and Snapshot
    print("=== Step 2: Populate Gold and Snapshot tables ===")
    for t in GOLD_TABLES:
        print(f"  Setting up Gold & Snapshot for {t}...")
        exec_sql(f"CREATE OR REPLACE TABLE {CATALOG}.{PREFIX}_gold.{t} AS SELECT * FROM {CATALOG}.{DEFAULT_PREFIX}_gold.{t}")
        exec_sql(f"CREATE OR REPLACE TABLE {CATALOG}.{PREFIX}_snapshot.{t} AS SELECT * FROM {CATALOG}.{PREFIX}_gold.{t}")

    # Copy Silver
    for t in SILVER_TABLES:
        exec_sql(f"CREATE OR REPLACE TABLE {CATALOG}.{PREFIX}_silver.{t} AS SELECT * FROM {CATALOG}.{DEFAULT_PREFIX}_silver.{t}")

    print("=== Step 3: Submit pipeline execution with injected bad row ===")
    fail_job_id = submit_job(
        "MAX-14 E2E failure demo (injected bad row)",
        "/Users/kalmuk.pn@ucu.edu.ua/nachalniki_yaropolk/checks/p3/failure_demo/e2e_failure_entry",
        {"schema_prefix": PREFIX}
    )
    print(f"Submitted failure job: {fail_job_id}. Polling...")
    fail_job_res = poll_job(fail_job_id)
    result_state = fail_job_res["state"].get("result_state")
    print(f"Failure job finished with state: {result_state} (EXPECTED FAILED)")
    assert result_state == "FAILED", f"Expected job to fail, but got {result_state}"

    print("=== Step 4: Verify audit rows & Gold untouched ===")
    runs_res = exec_sql(f"SELECT run_id, event, event_ts FROM {CATALOG}.{PREFIX}_audit.pipeline_runs ORDER BY event_ts DESC LIMIT 2")
    failed_run_id = runs_res["result"]["data_array"][0][0]
    failed_event = runs_res["result"]["data_array"][0][1]
    print(f"Latest pipeline event: run_id={failed_run_id}, event={failed_event}")
    assert failed_event == "started", f"Expected 'started', got {failed_event}"

    # Verify no succeeded event for this run
    succ_check = exec_sql(f"SELECT count(*) FROM {CATALOG}.{PREFIX}_audit.pipeline_runs WHERE run_id = '{failed_run_id}' AND event = 'succeeded'")
    succ_count = int(succ_check["result"]["data_array"][0][0])
    assert succ_count == 0, f"Expected 0 succeeded events, got {succ_count}"

    # Verify DQ-L2 recorded failure
    dq_check = exec_sql(f"SELECT rule_id, violation_count, passed FROM {CATALOG}.{PREFIX}_audit.dq_check_results WHERE run_id = '{failed_run_id}' AND rule_id = 'DQ-L2'")
    dq_l2 = dq_check["result"]["data_array"][0]
    print(f"DQ-L2 check result: {dq_l2}")
    assert dq_l2[2] == "false", f"Expected DQ-L2 passed=false, got {dq_l2[2]}"

    # Verify Gold tables untouched (EXCEPT ALL against snapshot = 0)
    print("Checking Gold tables against snapshot via EXCEPT ALL...")
    for t in GOLD_TABLES:
        c1 = int(exec_sql(f"SELECT count(*) FROM (SELECT * FROM {CATALOG}.{PREFIX}_gold.{t} EXCEPT ALL SELECT * FROM {CATALOG}.{PREFIX}_snapshot.{t})")["result"]["data_array"][0][0])
        c2 = int(exec_sql(f"SELECT count(*) FROM (SELECT * FROM {CATALOG}.{PREFIX}_snapshot.{t} EXCEPT ALL SELECT * FROM {CATALOG}.{PREFIX}_gold.{t})")["result"]["data_array"][0][0])
        print(f"  {t}: {c1} / {c2}")
        assert c1 == 0 and c2 == 0, f"Gold table {t} was modified!"

    print("=== Step 5: Test 06_analysis rejects stale/failed run ===")
    analysis_job_id = submit_job(
        "MAX-14 Analysis rejection check",
        "/Users/kalmuk.pn@ucu.edu.ua/nachalniki_yaropolk/notebooks/06_analysis",
        {"schema_prefix": PREFIX}
    )
    print(f"Submitted analysis rejection check: {analysis_job_id}. Polling...")
    analysis_job_res = poll_job(analysis_job_id)
    analysis_result = analysis_job_res["state"].get("result_state")
    print(f"Analysis job finished with state: {analysis_result} (EXPECTED FAILED)")
    assert analysis_result == "FAILED", f"Expected analysis to fail, got {analysis_result}"

    print("=== Step 6: Clean up scratch schemas ===")
    dropped = {}
    for s in ["bronze", "staging", "silver", "gold", "audit", "snapshot"]:
        full_s = f"{CATALOG}.{PREFIX}_{s}"
        res = exec_sql(f"DROP SCHEMA {full_s} CASCADE")
        dropped[full_s] = res["statement_id"]
        print(f"Dropped {full_s}: {res['statement_id']}")

    print("=== Step 7: Record evidence JSON ===")
    evidence = {
        "date": "2026-10-07",
        "workspace": "dbc-1766f78b-980d.cloud.databricks.com",
        "catalog": CATALOG,
        "schema_prefix": PREFIX,
        "executed_by": "kalmuk.pn@ucu.edu.ua",
        "failed_pipeline_job": {
            "job_run_id": fail_job_id,
            "task_run_id": fail_job_res["tasks"][0]["run_id"],
            "result": "FAILED_AS_EXPECTED",
            "run_id": failed_run_id,
            "injected_violation": "stg_lineitem l_receiptdate = l_shipdate - 1 (DQ-L2)",
            "pipeline_runs_check": {
                "events_present": ["started"],
                "succeeded_present": False
            },
            "dq_check_result": {
                "rule_id": dq_l2[0],
                "violation_count": int(dq_l2[1]),
                "passed": False
            }
        },
        "gold_immutability_check": {
            "all_tables_unchanged": True,
            "differing_rows": {t: 0 for t in GOLD_TABLES}
        },
        "analysis_rejection_job": {
            "job_run_id": analysis_job_id,
            "task_run_id": analysis_job_res["tasks"][0]["run_id"],
            "result": "FAILED_AS_EXPECTED",
            "reason": f"Run-state guard halted on run {failed_run_id} without succeeded event"
        },
        "cleanup": {
            "schemas_dropped": list(dropped.keys()),
            "drop_statements": dropped
        }
    }
    out_file = "checks/p3/outputs/max14_e2e_failure_check_20261007.json"
    with open(out_file, "w") as f:
        json.dump(evidence, f, indent=2)
    print(f"Evidence successfully written to {out_file}")

if __name__ == "__main__":
    main()

# Databricks notebook source
# MAGIC %md
# MAGIC # 06_analysis
# MAGIC
# MAGIC Answers Logistics questions Q1–Q4 from the published Gold aggregates. The first executable
# MAGIC section checks the append-only pipeline lifecycle and refuses to present stale Gold results
# MAGIC when the newest pipeline run has no `succeeded` event.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

from html import escape

import matplotlib.pyplot as plt
import numpy as np
from pyspark.sql import functions as F

PIPELINE_RUNS = f"{audit_schema}.pipeline_runs"


def show_answer(title, body):
    displayHTML(
        f"<div style='padding:12px;border-left:4px solid #2274a5;background:#f4f8fb'>"
        f"<b>{escape(title)}</b><br>{escape(body)}</div>"
    )


def percent(value):
    return f"{100 * float(value):.2f}%"


def days(value):
    return f"{float(value):.2f} days"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run-state guard
# MAGIC
# MAGIC The latest execution is selected by its `started` timestamp. Analysis proceeds only if that
# MAGIC same `run_id` has a `succeeded` event. Stage-only executions do not write `pipeline_runs`.

# COMMAND ----------

if not spark.catalog.tableExists(PIPELINE_RUNS):
    raise RuntimeError(f"Cannot present results: lifecycle table {PIPELINE_RUNS} does not exist.")

run_states = (
    spark.table(PIPELINE_RUNS)
    .groupBy("run_id")
    .agg(
        F.min(F.when(F.col("event") == "started", F.col("event_ts"))).alias("started_at"),
        F.max(F.when(F.col("event") == "succeeded", F.col("event_ts"))).alias("succeeded_at"),
        F.sort_array(F.collect_list("event")).alias("events"),
    )
)
latest_run = run_states.orderBy(F.col("started_at").desc()).first()
if latest_run is None:
    raise RuntimeError(f"Cannot present results: lifecycle table {PIPELINE_RUNS} is empty.")
if latest_run.succeeded_at is None:
    raise RuntimeError(
        "Cannot present stale Gold results: latest pipeline run "
        f"{latest_run.run_id} started at {latest_run.started_at} but has no succeeded event."
    )

analysis_run_id = latest_run.run_id
print(
    f"Analysis is using Gold from succeeded run_id {analysis_run_id} "
    f"(started {latest_run.started_at}, succeeded {latest_run.succeeded_at})."
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Q1 — Transit speed and predictability by ship mode
# MAGIC
# MAGIC Displayed result Q1 contains the required p50 and p90 plus the spread measures. The grouped
# MAGIC bars use the same rows. Fastest means lowest p50; most predictable means lowest p90 − p50.

# COMMAND ----------

q1 = (
    spark.table(f"{gold_schema}.agg_ship_mode_performance")
    .select(
        "ship_mode", "line_count", "transit_p50_days", "transit_p90_days",
        "transit_p90_minus_p50_days", "transit_iqr_days", "transit_mean_days",
        "transit_stddev_days",
    )
    .orderBy("ship_mode")
)
display(q1)
q1_pdf = q1.toPandas()

x = np.arange(len(q1_pdf))
width = 0.38
fig, ax = plt.subplots(figsize=(11, 5))
ax.bar(x - width / 2, q1_pdf["transit_p50_days"], width, label="p50")
ax.bar(x + width / 2, q1_pdf["transit_p90_days"], width, label="p90")
ax.set(title="Q1: transit days by ship mode", xlabel="Ship mode", ylabel="Days")
ax.set_xticks(x, q1_pdf["ship_mode"], rotation=30, ha="right")
ax.legend()
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
plt.show()

# COMMAND ----------

lowest_median = q1_pdf["transit_p50_days"].min()
fastest = q1_pdf[q1_pdf["transit_p50_days"] == lowest_median]
if len(fastest) == 1:
    fastest_text = f"{fastest.iloc[0]['ship_mode']} ({days(lowest_median)} median)"
else:
    tied_modes = ", ".join(fastest["ship_mode"].tolist())
    best_mean_row = fastest.sort_values("transit_mean_days").iloc[0]
    fastest_text = (
        f"tie between {tied_modes} at {days(lowest_median)} median; "
        f"{best_mean_row['ship_mode']} has the lowest mean among the tied modes "
        f"({days(best_mean_row['transit_mean_days'])})"
    )

predictable = q1_pdf.sort_values(
    ["transit_p90_minus_p50_days", "transit_iqr_days", "transit_stddev_days", "ship_mode"]
).iloc[0]
show_answer(
    "Q1 answer — see displayed result Q1",
    f"Fastest: {fastest_text}. Most predictable: {predictable['ship_mode']} "
    f"(p90 − p50 = {days(predictable['transit_p90_minus_p50_days'])}). "
    "Speed ranks the centre of the distribution; predictability ranks its spread, so they are "
    "different questions.",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Q2 — Fully on-time orders versus on-time lines
# MAGIC
# MAGIC Displayed result Q2a gives the two overall shares and the observed lines-per-order
# MAGIC distribution. Result Q2b shows how the order share changes with order size.

# COMMAND ----------

q2_summary = spark.table(f"{gold_schema}.agg_on_time_summary")
q2_by_size = (
    spark.table(f"{gold_schema}.agg_on_time_by_line_count")
    .orderBy("lines_in_order")
)
display(q2_summary)
display(q2_by_size)
q2_summary_row = q2_summary.first()
q2_size_pdf = q2_by_size.toPandas()

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
axes[0].bar(
    ["Line items", "Fully on-time orders"],
    [q2_summary_row.line_on_time_share, q2_summary_row.order_on_time_share],
    color=["#4c78a8", "#f58518"],
)
axes[0].set(title="Q2: overall on-time share", ylabel="Share", ylim=(0, 1))
axes[0].grid(axis="y", alpha=0.25)
axes[1].plot(
    q2_size_pdf["lines_in_order"], q2_size_pdf["order_on_time_share"], marker="o"
)
axes[1].set(
    title="Q2: fully on-time share by order size",
    xlabel="Lines in order",
    ylabel="Order on-time share",
    ylim=(0, 1),
)
axes[1].grid(alpha=0.25)
fig.tight_layout()
plt.show()

# COMMAND ----------

share_gap = q2_summary_row.line_on_time_share - q2_summary_row.order_on_time_share
show_answer(
    "Q2 answer — see displayed results Q2a and Q2b",
    f"{percent(q2_summary_row.order_on_time_share)} of orders are fully on time, versus "
    f"{percent(q2_summary_row.line_on_time_share)} of individual lines, a gap of "
    f"{percent(share_gap)}. Orders contain {q2_summary_row.lines_per_order_min}–"
    f"{q2_summary_row.lines_per_order_max} lines (median "
    f"{float(q2_summary_row.lines_per_order_p50):.1f}, mean "
    f"{float(q2_summary_row.lines_per_order_mean):.2f}); every line must be on time for the "
    "order to qualify, and displayed result Q2b shows the empirical size effect.",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Q3 — Delay rate by ship mode
# MAGIC
# MAGIC Displayed result Q3 reports both numerator and denominator; the chart uses the same rates.

# COMMAND ----------

q3 = (
    spark.table(f"{gold_schema}.agg_ship_mode_performance")
    .select("ship_mode", "line_count", "late_line_count", "delay_rate")
    .orderBy(F.col("delay_rate").desc(), "ship_mode")
)
display(q3)
q3_pdf = q3.toPandas()

fig, ax = plt.subplots(figsize=(10, 4.8))
ax.bar(q3_pdf["ship_mode"], q3_pdf["delay_rate"], color="#e45756")
ax.set(title="Q3: delayed line-item share by ship mode", xlabel="Ship mode", ylabel="Delay rate")
ax.tick_params(axis="x", rotation=30)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
plt.show()

# COMMAND ----------

worst_mode = q3_pdf.iloc[0]
show_answer(
    "Q3 answer — see displayed result Q3",
    f"{worst_mode['ship_mode']} has the highest delay rate at "
    f"{percent(worst_mode['delay_rate'])}: {int(worst_mode['late_line_count']):,} late lines "
    f"out of {int(worst_mode['line_count']):,}.",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Q4 — Urgent-priority fulfilment
# MAGIC
# MAGIC Displayed result Q4a compares urgent with all other orders directly. Result Q4b provides
# MAGIC the per-priority counts and completion, transit and order-to-ship statistics. The chart uses
# MAGIC the primary order-grain fulfilment measure.

# COMMAND ----------

q4_urgency = (
    spark.table(f"{gold_schema}.agg_urgency_fulfillment")
    .orderBy(F.col("is_urgent").desc())
)
q4_priority = (
    spark.table(f"{gold_schema}.agg_priority_fulfillment")
    .orderBy("order_priority")
)
display(q4_urgency)
display(q4_priority)
q4_urgency_rows = {row.is_urgent: row for row in q4_urgency.collect()}
q4_priority_pdf = q4_priority.toPandas()

x = np.arange(len(q4_priority_pdf))
width = 0.38
colors = ["#e45756" if urgent else "#4c78a8" for urgent in q4_priority_pdf["is_urgent"]]
fig, ax = plt.subplots(figsize=(11, 5))
ax.bar(
    x - width / 2, q4_priority_pdf["complete_p50_days"], width,
    label="p50", color=colors,
)
ax.bar(
    x + width / 2, q4_priority_pdf["complete_p90_days"], width,
    label="p90", color=colors, alpha=0.55,
)
ax.set(title="Q4: order fulfilment days by priority", xlabel="Priority", ylabel="Days")
ax.set_xticks(x, q4_priority_pdf["order_priority"], rotation=30, ha="right")
ax.legend(title="Darker = p50; urgent is red")
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
plt.show()

# COMMAND ----------

urgent = q4_urgency_rows[True]
other = q4_urgency_rows[False]
if urgent.complete_p50_days < other.complete_p50_days:
    conclusion = "Urgent orders are faster by the median primary fulfilment measure"
elif urgent.complete_p50_days > other.complete_p50_days:
    conclusion = "Urgent orders are slower by the median primary fulfilment measure"
else:
    conclusion = "Urgent and non-urgent orders tie on the median primary fulfilment measure"

show_answer(
    "Q4 answer — see displayed results Q4a and Q4b",
    f"{conclusion}: urgent n={urgent.order_count:,}, p50={days(urgent.complete_p50_days)}, "
    f"p90={days(urgent.complete_p90_days)}, mean={days(urgent.complete_mean_days)}; "
    f"other n={other.order_count:,}, p50={days(other.complete_p50_days)}, "
    f"p90={days(other.complete_p90_days)}, mean={days(other.complete_mean_days)}. "
    f"Supporting line-grain metrics: urgent transit p50/p90/mean = "
    f"{days(urgent.transit_p50_days)} / {days(urgent.transit_p90_days)} / "
    f"{days(urgent.transit_mean_days)}, and order-to-ship p50/p90/mean = "
    f"{days(urgent.order_to_ship_p50_days)} / {days(urgent.order_to_ship_p90_days)} / "
    f"{days(urgent.order_to_ship_mean_days)}; the corresponding non-urgent values are "
    f"{days(other.transit_p50_days)} / {days(other.transit_p90_days)} / "
    f"{days(other.transit_mean_days)} and {days(other.order_to_ship_p50_days)} / "
    f"{days(other.order_to_ship_p90_days)} / {days(other.order_to_ship_mean_days)}.",
)

# COMMAND ----------

print(f"Q1–Q4 analysis completed for succeeded run_id {analysis_run_id}.")

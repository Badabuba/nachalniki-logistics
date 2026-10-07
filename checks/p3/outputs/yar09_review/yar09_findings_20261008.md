# YAR-09 review of README "Results" (MAX-07)

Reviewer: Max (independent of the author, D22). Date: 2026-10-08.

**Gold used for the check.** `workspace.makc_logistics_gold`, built by the YAR-14 reproduction run `25979743-a4a7-4ab8-a4b2-c37af6d03805` (job `317490104173577`, SUCCESS) from the code of branch `feat/stage3-reassignment` at `7bbbf70`, with the default `catalog` and `source`. The README cites run `64829233-…` in `nachalniki_logistics_gold`, which Max cannot read (no `USE SCHEMA` on Yaropolk's schemas). MAX-11 and MAX-12 show that Gold is identical across reruns and prefixes, so the same code on the same source must give the same numbers. Raw query results: [gold_makc_logistics_20261008.json](gold_makc_logistics_20261008.json).

**Result: not approved.** The README numbers below differ from Gold. Numbers not listed match after rounding.

## Q1 — numbers match; one statement is not supported

All values of the ship-mode table match. The sentence "An air shipment arrives faster on average but exhibits greater variability than ocean freight" is not supported: the means are equal (AIR 15.4987, SHIP 15.4995 days). AIR is faster only at the median (15 vs 16 days) and has the wider p90 − p50 spread (13 vs 11).

## Q2 — the line-count bucket table differs in every row

The summary (36.77 %, 11,031,691 lines; 8.30 %, 622,660 orders; gap 28.47 points) matches.

| Lines in order | README orders / fully on-time | Gold orders / fully on-time | README order share / line share | Gold order share / line share |
|---|---|---|---|---|
| 1 | 1,072,504 / 393,874 | 1,071,498 / 393,504 | 36.72 % / 36.72 % | 36.72 % / 36.72 % |
| 2 | 1,070,397 / 144,870 | 1,072,178 / 145,111 | 13.53 % / 36.78 % | 13.53 % / 36.77 % |
| 3 | 1,072,746 / 53,831 | 1,070,076 / 53,697 | 5.02 % / 36.77 % | 5.02 % / 36.81 % |
| 4 | 1,070,379 / 19,474 | 1,071,495 / 19,494 | 1.82 % / 36.79 % | 1.82 % / 36.77 % |
| 5 | 1,073,348 / 7,207 | 1,072,080 / 7,198 | 0.67 % / 36.76 % | 0.67 % / 36.77 % |
| 6 | 1,069,961 / 2,609 | 1,071,378 / 2,613 | 0.24 % / 36.77 % | 0.24 % / 36.78 % |
| 7 | 1,070,665 / 795 | 1,071,295 / 1,043 | **0.07 %** / 36.76 % | **0.10 %** / 36.76 % |

## Q3 — late-line counts differ for 6 of 7 modes

The delay rates match after rounding; the late-line counts do not:

| Mode | README late lines | Gold late lines |
|---|---|---|
| AIR | 2,712,448 | 2,712,448 |
| RAIL | 2,710,349 | 2,710,348 |
| REG AIR | 2,709,642 | 2,709,635 |
| SHIP | 2,709,036 | 2,709,034 |
| TRUCK | 2,710,879 | 2,710,869 |
| MAIL | 2,706,819 | 2,706,820 |
| FOB | 2,708,930 | 2,708,950 |

## Q4 — priority table rows 2–5 differ

The `1-URGENT` row, the urgent vs non-urgent comparison in the text and the conclusion match.

| Priority | README orders / complete mean / lines / transit p50 / p90 | Gold |
|---|---|---|
| 2-HIGH | 1,498,908 / 108.38 / 5,995,953 / 16 / 27 | 1,499,192 / 108.41 / 6,000,786 / 16 / **28** |
| 3-MEDIUM | 1,500,757 / 108.41 / 6,003,506 / 16 / 27 | 1,498,710 / 108.41 / 5,991,279 / 16 / **28** |
| 4-NOT SPECIFIED | 1,499,655 / 108.37 / 5,999,017 / 16 / 27 | 1,501,281 / 108.38 / 6,004,909 / **15** / 27 |
| 5-LOW | 1,499,580 / 108.39 / 5,996,612 / 16 / 27 | 1,499,717 / 108.35 / 5,998,114 / **15** / **28** |

The Gold order counts equal the profiled `o_orderpriority` counts (design §5.5); the README counts do not.

## Monitoring — first month and the stable-period summary differ

| Item | README | Gold |
|---|---|---|
| 1992-01 (boundary) | 101,741 lines, 63.29 % | **213 lines, 86.38 %** |
| 1998-09 (edge) | 284,559 lines, 57.86 % | matches |
| 1998-10 (boundary) | 101,741 lines, 47.08 % | matches |
| stable period | 79 months, mean 63.23 %, 62.97–63.42 %, 350,000–389,000 lines | 80 non-boundary months: mean 63.44 %, 57.86–80.11 %, 95,167–389,002 lines. 1992-03 to 1998-08 (78 months): mean 63.30 %, 62.97–68.72 %, 291,339–389,002 lines |

1992-02 is also a low-count edge month (95,167 lines, 80.11 %) and is not mentioned.

## Evidence files

`checks/p3/outputs/max06_chart5_analysis_20261007.json` contains the same 1992-01 values (101,741 lines, 64,391 late). It is a written summary, not a Databricks run export, so it cannot be checked against the run. Please replace the README numbers with values read from Gold (e.g. the displayed tables of `06_analysis`) and attach the run exports.

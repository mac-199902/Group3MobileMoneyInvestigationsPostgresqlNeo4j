"""q2.py - Q2 daily activity (CAT days): date, transfer count, total RWF."""
import csv
import json
import os
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import mm_common as m

SQL_Q2 = """
SELECT to_char(to_timestamp(occurred_at) AT TIME ZONE 'Africa/Kigali', 'YYYY-MM-DD') AS day,
       COUNT(*) AS transfers, SUM(amount_rwf)::bigint AS total_rwf
FROM transfers
GROUP BY 1
ORDER BY 1
"""

CYPHER_Q2 = """
MATCH ()-[t:TRANSFER]->()
WITH datetime({epochSeconds: t.occurred_at, timezone: 'Africa/Kigali'}) AS dt, t
WITH toString(date(dt)) AS day, t
RETURN day, count(t) AS transfers, sum(t.amount_rwf) AS total_rwf
ORDER BY day
"""

audit = json.load(open(r"D:\MobileMoneyProject\results\capture_audit.json"))
cap_count = audit["transfers"]["written"]
cap_sum = audit["transfers"]["sum_amount_rwf"]

t0 = perf_counter()
pg_rows = m.run_pg(SQL_Q2, {})
t1 = perf_counter()
neo_rows = m.run_neo(CYPHER_Q2, {})
t2 = perf_counter()

print(f"{'date (CAT)':<12}{'PG count':>10}{'PG total RWF':>17}{'Neo count':>11}{'Neo total RWF':>17}  match")
for p, n in zip(pg_rows, neo_rows):
    print(f"{p[0]:<12}{p[1]:>10,}{p[2]:>17,}{n[1]:>11,}{n[2]:>17,}  {p == n}")

same = pg_rows == neo_rows
days_ok = len(pg_rows) == 30 and pg_rows[0][0] == "2026-09-01" and pg_rows[-1][0] == "2026-09-30"
print("-" * 70)
print(f"Days returned: PG {len(pg_rows)}, Neo4j {len(neo_rows)} (expected 30, 2026-09-01 to 2026-09-30): {days_ok}")
print(f"Rows identical in both engines: {same}")
print(f"Sum of daily counts : PG {sum(r[1] for r in pg_rows):,} | Neo4j {sum(r[1] for r in neo_rows):,} | capture {cap_count:,}")
print(f"Sum of daily RWF    : PG {sum(r[2] for r in pg_rows):,} | Neo4j {sum(r[2] for r in neo_rows):,} | capture {cap_sum:,}")
recon = (sum(r[1] for r in pg_rows) == cap_count and sum(r[2] for r in pg_rows) == cap_sum
         and sum(r[1] for r in neo_rows) == cap_count and sum(r[2] for r in neo_rows) == cap_sum)
print(f"Reconciles to capture totals: {recon}")
print(f"Seconds: PG {t1 - t0:.1f} | Neo4j {t2 - t1:.1f}")

with open(r"D:\MobileMoneyProject\results\q2_daily.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date_cat", "pg_count", "pg_total_rwf", "neo4j_count", "neo4j_total_rwf"])
    for p, n in zip(pg_rows, neo_rows):
        w.writerow([p[0], p[1], p[2], n[1], n[2]])

days = [int(r[0][-2:]) for r in pg_rows]
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
ax1.bar(days, [r[1] for r in pg_rows], color="#3b78b5")
ax1.set_ylabel("Transfers per day (count)")
ax1.set_title("Q2 daily activity, September 2026 (CAT days)")
ax2.bar(days, [r[2] / 1e6 for r in pg_rows], color="#d9822b")
ax2.set_ylabel("Total transferred per day (million RWF)")
ax2.set_xlabel("Day of September 2026")
ax2.set_xticks(days)
for ax in (ax1, ax2):
    ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(r"D:\MobileMoneyProject\results\q2_daily_charts.png", dpi=150)
print("Chart saved: results\\q2_daily_charts.png")
os.startfile(r"D:\MobileMoneyProject\results\q2_daily_charts.png")
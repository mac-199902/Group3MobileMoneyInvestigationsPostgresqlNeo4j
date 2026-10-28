"""plot_q2.py - redraw the Q2 charts from results\\q2_daily.csv (no database needed)."""
import csv

import matplotlib.pyplot as plt

rows = list(csv.DictReader(open(r"D:\MobileMoneyProject\results\q2_daily.csv")))
days = [int(r["date_cat"][-2:]) for r in rows]
counts = [int(r["pg_count"]) for r in rows]
values = [int(r["pg_total_rwf"]) / 1e6 for r in rows]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)
ax1.bar(days, counts, color="#3b78b5")
ax1.set_ylim(666_000, 667_100)
ax1.set_ylabel("Transfers per day (count)")
ax1.set_title("Q2 daily activity, September 2026 (CAT days)")
ax2.bar(days, values, color="#d9822b")
ax2.set_ylim(7_600, 7_900)
ax2.set_ylabel("Total transferred per day (million RWF)")
ax2.set_xlabel("Day of September 2026")
ax2.set_xticks(days)
for ax in (ax1, ax2):
    ax.grid(axis="y", alpha=0.3)
fig.text(0.5, 0.005, "Note: y-axes start above zero to show small daily differences.",
         ha="center", fontsize=9)
plt.tight_layout(rect=(0, 0.02, 1, 1))
plt.savefig(r"D:\MobileMoneyProject\results\q2_daily_charts_zoomed.png", dpi=150)
plt.show()
"""plot_load.py - throughput and p95 against client count for both workloads and engines."""
import json
import os
from statistics import median

import matplotlib.pyplot as plt

RES = r"D:\MobileMoneyProject\results"
data = {}
for engine in ("pg", "neo"):
    path = rf"{RES}\load_{engine}.jsonl"
    if not os.path.exists(path):
        continue
    for line in open(path):
        r = json.loads(line)
        if r["completed"] > 0:
            data.setdefault((engine, r["workload"], r["clients"]), []).append(r)

label = {"pg": "PostgreSQL", "neo": "Neo4j"}
fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
for col, workload in enumerate(("Q4", "Q7")):
    for engine in ("pg", "neo"):
        xs = [n for n in (1, 4, 8, 16) if (engine, workload, n) in data]
        if not xs:
            continue
        tp = [median(r["throughput"] for r in data[(engine, workload, n)]) for n in xs]
        p95 = [median(r["p95_ms"] for r in data[(engine, workload, n)]) for n in xs]
        axes[0][col].plot(xs, tp, marker="o", label=label[engine])
        axes[1][col].plot(xs, p95, marker="o", label=label[engine])
    title = "Q4 depth 10" if workload == "Q4" else "Q7 length-only bound 6"
    axes[0][col].set_title(title)
    axes[0][col].set_ylabel("Throughput (correct requests per second)")
    axes[1][col].set_ylabel("p95 latency (ms)")
    axes[1][col].set_xlabel("Number of concurrent clients")
    for row in (0, 1):
        axes[row][col].set_xticks([1, 4, 8, 16])
        axes[row][col].grid(alpha=0.3)
        axes[row][col].legend()
fig.text(0.5, 0.005, "Median of 3 repetitions; 15 s runs; 4-core laptop, 8 GB RAM.", ha="center", fontsize=9)
plt.tight_layout(rect=(0, 0.02, 1, 1))
plt.savefig(rf"{RES}\load_plots.png", dpi=150)
plt.show()
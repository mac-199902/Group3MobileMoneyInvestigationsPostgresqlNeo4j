"""load_summary.py - per-repetition table and the median of 3 repetitions for each combination."""
import json
import os
import sys
from statistics import median

engine = sys.argv[1] if len(sys.argv) > 1 else "pg"
path = rf"D:\MobileMoneyProject\results\load_{engine}.jsonl"
if not os.path.exists(path):
    raise SystemExit(f"no results yet for engine {engine}")
recs = [json.loads(l) for l in open(path)]
recs.sort(key=lambda r: (r["workload"], r["clients"], r["rep"]))
fmt = lambda x: "-" if x is None else f"{x:.1f}"

print(f"ENGINE {engine}: every repetition")
print(f"{'workload':<9}{'clients':>8}{'rep':>4}{'req/s':>9}{'median ms':>11}{'p95 ms':>10}"
      f"{'done':>7}{'wrong':>7}{'err':>5}{'t/o':>5}  note")
for r in recs:
    note = "CHECK" if (r["errors"] or r["timeouts"] or r["wrong"] or r["completed"] < 50) else ""
    print(f"{r['workload']:<9}{r['clients']:>8}{r['rep']:>4}{r['throughput']:>9.2f}"
          f"{fmt(r['median_ms']):>11}{fmt(r['p95_ms']):>10}{r['completed']:>7}{r['wrong']:>7}"
          f"{r['errors']:>5}{r['timeouts']:>5}  {note}")

print()
print(f"ENGINE {engine}: median of the repetitions (the 16 combinations)")
print(f"{'workload':<9}{'clients':>8}{'reps':>5}{'req/s':>9}{'median ms':>11}{'p95 ms':>10}"
      f"{'errors':>8}{'t/o':>5}{'wrong':>7}")
groups = {}
for r in recs:
    groups.setdefault((r["workload"], r["clients"]), []).append(r)
for (w, n), g in sorted(groups.items()):
    good = [r for r in g if r["completed"] > 0]
    pick = lambda k: median([r[k] for r in good if r[k] is not None]) if good else None
    print(f"{w:<9}{n:>8}{len(g):>5}{(pick('throughput') or 0):>9.2f}{fmt(pick('median_ms')):>11}"
          f"{fmt(pick('p95_ms')):>10}{sum(r['errors'] for r in g):>8}{sum(r['timeouts'] for r in g):>5}"
          f"{sum(r['wrong'] for r in g):>7}")
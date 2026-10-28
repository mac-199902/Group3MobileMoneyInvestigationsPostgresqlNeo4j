"""q4_table.py - print Q4 comparisons from results\\q4_results.json.
Usage: python q4_table.py            (all 24)
       python q4_table.py 4 6        (only those depths)"""
import json
import sys

store = json.load(open(r"D:\MobileMoneyProject\results\q4_results.json"))
keep = [int(x) for x in sys.argv[1:]]
rows = sorted((v for v in store.values() if not keep or v["depth"] in keep),
              key=lambda v: (v["depth"], v["set"]) if keep else (v["set"], v["depth"]))
print(f"{'depth':>5} {'set':<4}{'account':>8}{'PG total':>10}{'Neo total':>11}  match   "
      f"{'PG s':>6}{'Neo s':>8}   regions (PostgreSQL)")
for v in rows:
    regions = ", ".join(f"{r[0][:3]} {r[1]}" for r in v["pg"])
    print(f"{v['depth']:>5} {v['set']:<4}{v['account']:>8}{sum(r[1] for r in v['pg']):>10}"
          f"{sum(r[1] for r in v['neo4j']):>11}  {str(v['match']):<6}  "
          f"{v['pg_seconds']:>6.1f}{v['neo_seconds']:>8.1f}   {regions}")
print(f"Comparisons: {len(rows)} | all match: {all(v['match'] for v in rows)}")
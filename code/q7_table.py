"""q7_table.py - print the Q7 comparisons from results\\q7_results.json."""
import json

store = json.load(open(r"D:\MobileMoneyProject\results\q7_results.json"))
rows = sorted(store.values(), key=lambda v: (v["bound"], v["set"]))
print(f"{'bound':>5} {'set':<4}{'source':>8}{'dest':>8}  {'PG len':>7}{'Neo len':>9}  match   "
      f"{'PG s':>7}{'Neo s':>8}")
for v in rows:
    pl = v["pg_length"] if v["pg_length"] is not None else "none"
    nl = v["neo_length"] if v["neo_length"] is not None else "none"
    print(f"{v['bound']:>5} {v['set']:<4}{v['source']:>8}{v['dest']:>8}  {pl:>7}{nl:>9}  "
          f"{str(v['match']):<6}  {v['pg_seconds']:>7.1f}{v['neo_seconds']:>8.1f}")
print(f"Comparisons: {len(rows)} | all match: {all(v['match'] for v in rows)}")
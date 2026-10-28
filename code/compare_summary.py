"""compare_summary.py - summary of the 61-case comparison, grouped by question."""
import csv
from collections import defaultdict

rows = list(csv.DictReader(open(r"D:\MobileMoneyProject\results\compare_61_status.csv")))
groups = defaultdict(list)
for r in rows:
    groups[r["question"]].append(r)
expected = {"Q1": 6, "Q2": 1, "Q3": 6, "Q4": 24, "Q5": 6, "Q6": 6, "Q7": 12}
print(f"{'question':<9}{'cases':>6}{'expected':>9}{'match':>7}{'mismatch':>9}   status")
for q in sorted(groups):
    g = groups[q]
    match = sum(r["status"] == "MATCH" for r in g)
    print(f"{q:<9}{len(g):>6}{expected[q]:>9}{match:>7}{len(g) - match:>9}   "
          f"{'ALL MATCH' if match == len(g) else 'CHECK'}")
print("-" * 52)
print(f"{'TOTAL':<9}{len(rows):>6}{sum(expected.values()):>9}"
      f"{sum(r['status'] == 'MATCH' for r in rows):>7}"
      f"{sum(r['status'] != 'MATCH' for r in rows):>9}")
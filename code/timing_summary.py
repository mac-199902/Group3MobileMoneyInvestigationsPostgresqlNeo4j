"""timing_summary.py - median/min/max ms per case for both engines and the PG/Neo4j median ratio."""
import csv
import json
import os
from statistics import median

RES = r"D:\MobileMoneyProject\results"


def load(engine):
    path = rf"{RES}\timing_{engine}.jsonl"
    cases = {}
    if not os.path.exists(path):
        return cases
    for line in open(path):
        r = json.loads(line)
        c = cases.setdefault(r["case"], {"ms": [], "digests": set(), "status": "OK"})
        if r["phase"] == "case_done":
            c["status"] = r["status"]
        elif r["phase"] == "measured" and r["status"] == "OK":
            c["ms"].append(r["seconds"] * 1000)
            c["digests"].add(r["digest"])
    return cases


def stats(c):
    if c is None:
        return None, "not run", "-", "-"
    if c["status"] != "OK" or len(c["ms"]) < 5:
        return None, c["status"], "-", "-"
    ms = c["ms"]
    return median(ms), f"{median(ms):.1f}", f"{min(ms):.1f}", f"{max(ms):.1f}"


pg, neo = load("pg"), load("neo")
order = list(pg) + [k for k in neo if k not in pg]
print(f"{'case':<14}{'PG median':>11}{'min':>9}{'max':>9}  {'Neo median':>11}{'min':>9}{'max':>9}"
      f"{'PG/Neo':>9}  answers")
rows = []
for case in order:
    pm, ptxt, pmin, pmax = stats(pg.get(case))
    nm, ntxt, nmin, nmax = stats(neo.get(case))
    ratio = f"{pm / nm:.1f}" if pm and nm else "-"
    if pm and nm:
        same = "same" if pg[case]["digests"] == neo[case]["digests"] and len(pg[case]["digests"]) == 1 else "DIFFERENT"
    else:
        same = "-"
    print(f"{case:<14}{ptxt:>11}{pmin:>9}{pmax:>9}  {ntxt:>11}{nmin:>9}{nmax:>9}{ratio:>9}  {same}")
    rows.append([case, ptxt, pmin, pmax, ntxt, nmin, nmax, ratio, same])
print("(milliseconds; a status word means no completed timing, see the .jsonl file)")
with open(rf"{RES}\timing_summary.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["case", "pg_median_ms", "pg_min", "pg_max", "neo_median_ms", "neo_min", "neo_max",
                "pg_over_neo_median", "answers"])
    w.writerows(rows)
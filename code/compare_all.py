"""compare_all.py - run all 61 cases in PostgreSQL and Neo4j and compare rows exactly."""
import csv
import json
from collections import Counter

import mm_common as m
import queries as q

DEST_DAY = m.SETS
rows_out = []


def record(case, question, params_text, pg_rows, neo_rows, note=""):
    same = pg_rows == neo_rows
    rows_out.append({"case": case, "question": question, "params": params_text,
                     "pg_rows": len(pg_rows), "neo_rows": len(neo_rows),
                     "status": "MATCH" if same else "MISMATCH", "note": note})
    print(f"{case:>3}  {question:<3} {params_text:<28} PG {len(pg_rows):>4} rows | "
          f"Neo4j {len(neo_rows):>4} rows | {'MATCH' if same else 'MISMATCH'} {note}", flush=True)


case = 0
for name, (account, dest, day) in m.SETS.items():                     # Q1: 6
    s, e = m.hour_window(day)
    p = {"account": account, "start": s, "end": e}
    case += 1
    record(case, "Q1", f"set {name} acct {account}", m.run_pg(q.SQL_Q1, p), m.run_neo(q.CYPHER_Q1, p))

case += 1                                                              # Q2: 1
record(case, "Q2", "full month", m.run_pg(q.SQL_Q2, {}), m.run_neo(q.CYPHER_Q2, {}))

for name, (account, dest, day) in m.SETS.items():                      # Q3: 6
    p = {"account": account}
    case += 1
    record(case, "Q3", f"set {name} acct {account}", m.run_pg(q.SQL_Q3, p), m.run_neo(q.CYPHER_Q3, p))

for depth in (4, 6, 8, 10):                                            # Q4: 24
    for name, (account, dest, day) in m.SETS.items():
        case += 1
        record(case, "Q4", f"set {name} depth {depth}",
               m.run_pg(q.SQL_Q4, {"account": account, "depth": depth}),
               m.run_neo(q.CYPHER_Q4.replace("DEPTH", str(depth)), {"account": account}))

for name, (account, dest, day) in m.SETS.items():                      # Q5: 6
    s, e = m.hour_window(day)
    p = {"account": account, "start": s, "end": e}
    case += 1
    record(case, "Q5", f"set {name} acct {account}", m.run_pg(q.SQL_Q5, p), m.run_neo(q.CYPHER_Q5, p))

for name, (account, dest, day) in m.SETS.items():                      # Q6: 6
    s, e = m.hour_window(day)
    p = {"account": account, "start": s, "end": e}
    case += 1
    record(case, "Q6", f"set {name} acct {account}", m.run_pg(q.SQL_Q6, p), m.run_neo(q.CYPHER_Q6, p))

for bound in (4, 6):                                                   # Q7: 12 (lengths)
    for name, (account, dest, day) in m.SETS.items():
        case += 1
        pg_rows = m.run_pg(q.SQL_Q7, {"src": account, "dst": dest, "bound": bound})
        neo_rows = m.run_neo(q.CYPHER_Q7.replace("BOUND", str(bound)), {"src": account, "dst": dest})
        record(case, "Q7", f"set {name} bound {bound}", pg_rows, neo_rows,
               f"length PG {pg_rows[0][0]} Neo {neo_rows[0][0]}")

by_q = Counter(r["question"] for r in rows_out)
ok = sum(r["status"] == "MATCH" for r in rows_out)
print("-" * 100)
print("Cases per question:", dict(sorted(by_q.items())), "| expected 6/1/6/24/6/6/12 = 61")
print(f"Total cases: {len(rows_out)} | MATCH {ok} | MISMATCH {len(rows_out) - ok}")

with open(r"D:\MobileMoneyProject\results\compare_61_status.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0]))
    w.writeheader()
    w.writerows(rows_out)
print("Saved: results\\compare_61_status.csv")
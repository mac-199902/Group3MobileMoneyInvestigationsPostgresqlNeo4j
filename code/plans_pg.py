"""plans_pg.py - EXPLAIN (ANALYZE, BUFFERS) for Q2, Q4 B depth 10 and Q7 B bound 6."""
import mm_common as m
import queries as q

account_b, dest_b, day_b = m.SETS["B"]
CASES = [
    ("Q2 full month", q.SQL_Q2, {}),
    ("Q4 set B depth 10", q.SQL_Q4, {"account": account_b, "depth": 10}),
    ("Q7 set B bound 6", q.SQL_Q7, {"src": account_b, "dst": dest_b, "bound": 6}),
]
out = open(r"D:\MobileMoneyProject\plans\pg_plans.txt", "w", encoding="utf-8")
for name, text, params in CASES:
    with m.pg().cursor() as cur:
        cur.execute("EXPLAIN (ANALYZE, BUFFERS) " + text, params)
        lines = [r[0] for r in cur.fetchall()]
    out.write(f"===== {name} =====\n" + "\n".join(lines) + "\n\n")
    print(f"===== {name} =====")
    keep = [l for l in lines if any(k in l for k in
            ("Scan", "Aggregate", "Recursive", "WorkTable", "Join", "Sort", "Execution Time",
             "Planning Time", "Buffers: shared hit", "Parallel"))]
    print("\n".join(l[:150] for l in keep[:28]))
    print()
out.close()
print("Full plans saved: plans\\pg_plans.txt")
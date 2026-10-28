"""q4.py - Q4 ownership and device network: distinct accounts within N links, by owner region.

Usage: python q4.py 4 6      (then, after writing predictions, python q4.py 8 10)
"""
import json
import os
import sys
from time import perf_counter

import mm_common as m

SQL_Q4 = """
WITH RECURSIVE edges(sk, si, dk, di) AS (
    SELECT 'Customer', customer_id, 'Account', account_id FROM accounts
    UNION ALL
    SELECT 'Account', account_id, 'Customer', customer_id FROM accounts
    UNION ALL
    SELECT 'Account', account_id, 'Device', device_id FROM account_devices
    UNION ALL
    SELECT 'Device', device_id, 'Account', account_id FROM account_devices
), walk(kind, id, depth) AS (
    SELECT 'Account', %(account)s::integer, 0
    UNION
    SELECT e.dk, e.di, w.depth + 1
    FROM walk w JOIN edges e ON e.sk = w.kind AND e.si = w.id
    WHERE w.depth < %(depth)s
)
SELECT c.region, COUNT(*) AS accounts
FROM (SELECT DISTINCT id FROM walk WHERE kind = 'Account' AND id <> %(account)s) r
JOIN accounts a ON a.account_id = r.id
JOIN customers c ON c.customer_id = a.customer_id
GROUP BY c.region
ORDER BY c.region
"""

CYPHER_Q4 = """
MATCH (a:Account {account_id: $account})
MATCH (a)-[:OWNS|USED_DEVICE*1..DEPTH]-(b:Account)
WHERE b <> a
WITH DISTINCT b
MATCH (c:Customer)-[:OWNS]->(b)
RETURN c.region AS region, count(b) AS accounts
ORDER BY region
"""

depths = [int(x) for x in sys.argv[1:]] or [4, 6]
out_path = r"D:\MobileMoneyProject\results\q4_results.json"
store = json.load(open(out_path)) if os.path.exists(out_path) else {}

print(f"{'depth':>5} {'set':<4}{'account':>8}  {'PG total':>8}{'Neo total':>10}  match   "
      f"{'PG s':>6}{'Neo s':>8}   regions (PostgreSQL)")
for depth in depths:
    for name, (account, destination, day) in m.SETS.items():
        t0 = perf_counter()
        pg_rows = m.run_pg(SQL_Q4, {"account": account, "depth": depth})
        t1 = perf_counter()
        neo_rows = m.run_neo(CYPHER_Q4.replace("DEPTH", str(depth)), {"account": account})
        t2 = perf_counter()
        same = pg_rows == neo_rows
        pg_total = sum(r[1] for r in pg_rows)
        neo_total = sum(r[1] for r in neo_rows)
        regions = ", ".join(f"{r[0][:3]} {r[1]}" for r in pg_rows)
        print(f"{depth:>5} {name:<4}{account:>8}  {pg_total:>8}{neo_total:>10}  {str(same):<6}  "
              f"{t1 - t0:>6.1f}{t2 - t1:>8.1f}   {regions}", flush=True)
        store[f"{name}-{depth}"] = {"set": name, "account": account, "depth": depth,
                                    "pg": pg_rows, "neo4j": neo_rows, "match": same,
                                    "pg_seconds": round(t1 - t0, 2),
                                    "neo_seconds": round(t2 - t1, 2)}
        with open(out_path, "w") as f:
            json.dump(store, f, indent=2, default=str)

done = [v for v in store.values() if v["depth"] in depths]
print(f"Comparisons run: {len(done)} | all match: {all(v['match'] for v in done)}")
print("Saved: results\\q4_results.json")
"""q3.py - Q3 shared devices with overlapping observation days."""
import json
from collections import Counter

import mm_common as m

SQL_Q3 = """
SELECT b.account_id, b.device_id, d.access_type,
       GREATEST(a.first_day, b.first_day) AS overlap_start,
       LEAST(a.last_day, b.last_day) AS overlap_end
FROM account_devices a
JOIN account_devices b ON b.device_id = a.device_id AND b.account_id <> a.account_id
JOIN devices d ON d.device_id = a.device_id
WHERE a.account_id = %(account)s
  AND GREATEST(a.first_day, b.first_day) <= LEAST(a.last_day, b.last_day)
ORDER BY b.account_id, b.device_id
"""

CYPHER_Q3 = """
MATCH (a:Account {account_id: $account})-[u1:USED_DEVICE]->(d:Device)<-[u2:USED_DEVICE]-(b:Account)
WHERE b <> a
WITH b, d, u1, u2,
     CASE WHEN u1.first_day > u2.first_day THEN u1.first_day ELSE u2.first_day END AS overlap_start,
     CASE WHEN u1.last_day < u2.last_day THEN u1.last_day ELSE u2.last_day END AS overlap_end
WHERE overlap_start <= overlap_end
RETURN b.account_id AS other_account, d.device_id AS device_id, d.access_type AS access_type,
       overlap_start, overlap_end
ORDER BY other_account, device_id
"""

results = []
print(f"{'set':<4}{'account':>8}{'PG rows':>9}{'Neo rows':>10}{'other accts':>13}"
      f"{'handset':>9}{'public_term':>13}  match")
examples = {}
for name, (account, destination, day) in m.SETS.items():
    params = {"account": account}
    pg_rows = m.run_pg(SQL_Q3, params)
    neo_rows = m.run_neo(CYPHER_Q3, params)
    same = pg_rows == neo_rows
    kinds = Counter(r[2] for r in pg_rows)
    print(f"{name:<4}{account:>8}{len(pg_rows):>9}{len(neo_rows):>10}"
          f"{len({r[0] for r in pg_rows}):>13}{kinds.get('handset', 0):>9}"
          f"{kinds.get('public_terminal', 0):>13}  {same}")
    examples[name] = pg_rows[:3]
    results.append({"set": name, "account": account, "pg": pg_rows, "neo4j": neo_rows,
                    "match": same})

print()
print("First rows per set: (other_account, device_id, access_type, overlap_start, overlap_end)")
for name, rows in examples.items():
    print(f"  {name}: {rows if rows else 'no shared device in an overlapping period'}")
print("All six pairs match:", all(r["match"] for r in results))

with open(r"D:\MobileMoneyProject\results\q3_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print("Full rows saved: results\\q3_results.json")
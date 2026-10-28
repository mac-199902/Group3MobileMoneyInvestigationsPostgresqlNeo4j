"""q1.py - Q1 account activity: outgoing count and total RWF in the review hour."""
import json
import os

import mm_common as m

SQL_Q1 = """
SELECT COUNT(*), COALESCE(SUM(amount_rwf), 0)
FROM transfers
WHERE sender_id = %(account)s
  AND occurred_at >= %(start)s AND occurred_at < %(end)s
"""

CYPHER_Q1 = """
MATCH (a:Account {account_id: $account})-[t:TRANSFER]->()
WHERE t.occurred_at >= $start AND t.occurred_at < $end
RETURN count(t) AS outgoing_count, coalesce(sum(t.amount_rwf), 0) AS total_rwf
"""

results = []
print(f"{'set':<4}{'account':>8}  {'window start (CAT)':<20}{'epoch start':>12}{'epoch end':>12}"
      f"  {'PG count':>8}{'PG RWF':>10}  {'Neo count':>9}{'Neo RWF':>10}  match")
for name, (account, destination, day) in m.SETS.items():
    start, end = m.hour_window(day)
    params = {"account": account, "start": start, "end": end}
    pg_rows = m.run_pg(SQL_Q1, params)
    neo_rows = m.run_neo(CYPHER_Q1, params)
    same = pg_rows == neo_rows
    (pg_n, pg_sum), (ne_n, ne_sum) = pg_rows[0], neo_rows[0]
    print(f"{name:<4}{account:>8}  {m.cat_text(start):<20}{start:>12}{end:>12}"
          f"  {pg_n:>8}{pg_sum:>10,}  {ne_n:>9}{ne_sum:>10,}  {same}")
    results.append({"set": name, "account": account, "day": day, "start": start,
                    "end": end, "pg": pg_rows, "neo4j": neo_rows, "match": same})

os.makedirs(r"D:\MobileMoneyProject\results", exist_ok=True)
with open(r"D:\MobileMoneyProject\results\q1_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print("All six pairs match:", all(r["match"] for r in results))
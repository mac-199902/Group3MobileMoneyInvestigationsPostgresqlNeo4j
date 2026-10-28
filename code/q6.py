"""q6.py - Q6 circular payments: 3 to 8 transfers that start and end at the review account."""
import json
from collections import Counter

import mm_common as m

SQL_Q6 = """
WITH RECURSIVE walk(current_account, ids, first_time, last_time, last_amount, len) AS (
    SELECT receiver_id, ARRAY[transfer_id], occurred_at, occurred_at, amount_rwf, 1
    FROM transfers
    WHERE sender_id = %(account)s
      AND occurred_at >= %(start)s AND occurred_at < %(end)s
  UNION ALL
    SELECT t.receiver_id, w.ids || t.transfer_id, w.first_time, t.occurred_at,
           t.amount_rwf, w.len + 1
    FROM walk w
    JOIN transfers t ON t.sender_id = w.current_account
    WHERE w.current_account <> %(account)s
      AND w.len < 8
      AND t.occurred_at > w.last_time
      AND t.occurred_at >= %(start)s AND t.occurred_at < %(end)s
      AND t.occurred_at - w.first_time <= 1800
      AND 90::bigint * w.last_amount <= 100::bigint * t.amount_rwf
      AND 100::bigint * t.amount_rwf <= 105::bigint * w.last_amount
)
SELECT ids, len FROM walk
WHERE current_account = %(account)s AND len BETWEEN 3 AND 8
ORDER BY ids
"""

CYPHER_Q6 = """
MATCH p = (a:Account {account_id: $account})-[ts:TRANSFER*3..8]->(a)
WHERE all(r IN ts WHERE r.occurred_at >= $start AND r.occurred_at < $end)
  AND none(n IN nodes(p)[1..-1] WHERE n = a)
  AND all(i IN range(0, size(ts) - 2) WHERE ts[i].occurred_at < ts[i + 1].occurred_at)
  AND ts[size(ts) - 1].occurred_at - ts[0].occurred_at <= 1800
  AND all(i IN range(0, size(ts) - 2) WHERE
          90 * ts[i].amount_rwf <= 100 * ts[i + 1].amount_rwf
          AND 100 * ts[i + 1].amount_rwf <= 105 * ts[i].amount_rwf)
RETURN [r IN ts | r.transfer_id] AS ids, size(ts) AS len
ORDER BY ids
"""

results = []
print(f"{'set':<4}{'account':>8}{'PG cycles':>11}{'Neo cycles':>12}  match   lengths (PostgreSQL)")
for name, (account, destination, day) in m.SETS.items():
    start, end = m.hour_window(day)
    params = {"account": account, "start": start, "end": end}
    pg_rows = m.run_pg(SQL_Q6, params)
    neo_rows = m.run_neo(CYPHER_Q6, params)
    same = pg_rows == neo_rows
    lengths = dict(sorted(Counter(r[1] for r in pg_rows).items()))
    print(f"{name:<4}{account:>8}{len(pg_rows):>11}{len(neo_rows):>12}  {str(same):<6}  {lengths}")
    results.append({"set": name, "account": account, "pg": pg_rows, "neo4j": neo_rows,
                    "match": same})

print("All six pairs match:", all(r["match"] for r in results))
print()
print("First cycle per set (ordered transfer IDs, length):")
for r in results:
    print(f"  {r['set']}: {r['pg'][0] if r['pg'] else 'no cycle'}")

with open(r"D:\MobileMoneyProject\results\q6_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print("Saved: results\\q6_results.json")
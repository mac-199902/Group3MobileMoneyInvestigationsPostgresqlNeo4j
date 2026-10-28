"""q5.py - Q5 rapid onward payments: three directed transfers through four distinct accounts."""
import json

import mm_common as m

SQL_Q5 = """
SELECT t1.transfer_id, t2.transfer_id, t3.transfer_id, t3.receiver_id
FROM transfers t1
JOIN transfers t2 ON t2.sender_id = t1.receiver_id
JOIN transfers t3 ON t3.sender_id = t2.receiver_id
WHERE t1.sender_id = %(account)s
  AND t1.occurred_at >= %(start)s AND t1.occurred_at < %(end)s
  AND t2.occurred_at > t1.occurred_at AND t2.occurred_at <= t1.occurred_at + 600
  AND t3.occurred_at > t2.occurred_at AND t3.occurred_at <= t2.occurred_at + 600
  AND 90::bigint * t1.amount_rwf <= 100::bigint * t2.amount_rwf
  AND 100::bigint * t2.amount_rwf <= 105::bigint * t1.amount_rwf
  AND 90::bigint * t2.amount_rwf <= 100::bigint * t3.amount_rwf
  AND 100::bigint * t3.amount_rwf <= 105::bigint * t2.amount_rwf
  AND t1.sender_id <> t1.receiver_id AND t1.sender_id <> t2.receiver_id
  AND t1.sender_id <> t3.receiver_id AND t1.receiver_id <> t2.receiver_id
  AND t1.receiver_id <> t3.receiver_id AND t2.receiver_id <> t3.receiver_id
ORDER BY t1.transfer_id, t2.transfer_id, t3.transfer_id
"""

CYPHER_Q5 = """
MATCH (a:Account {account_id: $account})-[t1:TRANSFER]->(b:Account)
      -[t2:TRANSFER]->(c:Account)-[t3:TRANSFER]->(d:Account)
WHERE t1.occurred_at >= $start AND t1.occurred_at < $end
  AND t2.occurred_at > t1.occurred_at AND t2.occurred_at <= t1.occurred_at + 600
  AND t3.occurred_at > t2.occurred_at AND t3.occurred_at <= t2.occurred_at + 600
  AND 90 * t1.amount_rwf <= 100 * t2.amount_rwf AND 100 * t2.amount_rwf <= 105 * t1.amount_rwf
  AND 90 * t2.amount_rwf <= 100 * t3.amount_rwf AND 100 * t3.amount_rwf <= 105 * t2.amount_rwf
  AND a <> b AND a <> c AND a <> d AND b <> c AND b <> d AND c <> d
RETURN t1.transfer_id AS t1_id, t2.transfer_id AS t2_id, t3.transfer_id AS t3_id,
       d.account_id AS final_receiver
ORDER BY t1_id, t2_id, t3_id
"""

results = []
print(f"{'set':<4}{'account':>8}{'PG chains':>11}{'Neo chains':>12}  match")
for name, (account, destination, day) in m.SETS.items():
    start, end = m.hour_window(day)
    params = {"account": account, "start": start, "end": end}
    pg_rows = m.run_pg(SQL_Q5, params)
    neo_rows = m.run_neo(CYPHER_Q5, params)
    same = pg_rows == neo_rows
    print(f"{name:<4}{account:>8}{len(pg_rows):>11}{len(neo_rows):>12}  {same}")
    results.append({"set": name, "account": account, "pg": pg_rows, "neo4j": neo_rows,
                    "match": same})

print("All six pairs match:", all(r["match"] for r in results))
print()
print("Ordered IDs and final receiver (first chain per set):")
for r in results:
    print(f"  {r['set']}: {r['pg'][0] if r['pg'] else 'no chain'}")

with open(r"D:\MobileMoneyProject\results\q5_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print("Saved: results\\q5_results.json")
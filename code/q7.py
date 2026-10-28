"""q7.py - Q7 shortest directed transfer connection through person accounts only.

Usage: python q7.py 4 6     (or one bound at a time, e.g. python q7.py 4)
"""
import json
import os
import sys
from time import perf_counter

import mm_common as m

SQL_Q7 = """
WITH RECURSIVE walk(account_id, depth) AS (
    SELECT account_id, 0 FROM accounts
    WHERE account_id = %(src)s AND role = 'person'
  UNION
    SELECT r.account_id, w.depth + 1
    FROM walk w
    CROSS JOIN LATERAL (SELECT DISTINCT receiver_id FROM transfers
                        WHERE sender_id = w.account_id) n
    JOIN accounts r ON r.account_id = n.receiver_id AND r.role = 'person'
    WHERE w.depth < %(bound)s
)
SELECT MIN(depth) FROM walk WHERE account_id = %(dst)s AND depth > 0
"""

CYPHER_Q7 = """
CYPHER 25
OPTIONAL MATCH p = SHORTEST 1
  (a:Account {account_id: $src, role: 'person'})
  (()-[:TRANSFER]->(:Account {role: 'person'})){1,BOUND}
  (b:Account {account_id: $dst, role: 'person'})
RETURN length(p) AS links
"""


def main():
    bounds = [int(x) for x in sys.argv[1:]] or [4, 6]
    out_path = r"D:\MobileMoneyProject\results\q7_results.json"
    store = json.load(open(out_path)) if os.path.exists(out_path) else {}
    print(f"{'bound':>5} {'set':<4}{'source':>8}{'dest':>8}  {'PG len':>7}{'Neo len':>9}  match   "
          f"{'PG s':>7}{'Neo s':>8}", flush=True)
    for bound in bounds:
        for name, (src, dst, day) in m.SETS.items():
            t0 = perf_counter()
            pg_rows = m.run_pg(SQL_Q7, {"src": src, "dst": dst, "bound": bound})
            t1 = perf_counter()
            neo_rows = m.run_neo(CYPHER_Q7.replace("BOUND", str(bound)),
                                 {"src": src, "dst": dst})
            t2 = perf_counter()
            pg_len = pg_rows[0][0]
            neo_len = neo_rows[0][0] if neo_rows else None
            same = pg_rows == neo_rows
            print(f"{bound:>5} {name:<4}{src:>8}{dst:>8}  {pg_len if pg_len is not None else 'none':>7}"
                  f"{neo_len if neo_len is not None else 'none':>9}  {str(same):<6}  "
                  f"{t1 - t0:>7.1f}{t2 - t1:>8.1f}", flush=True)
            store[f"{name}-{bound}"] = {"set": name, "source": src, "dest": dst, "bound": bound,
                                        "pg_length": pg_len, "neo_length": neo_len, "match": same,
                                        "pg_seconds": round(t1 - t0, 2),
                                        "neo_seconds": round(t2 - t1, 2)}
            with open(out_path, "w") as f:
                json.dump(store, f, indent=2)
    done = [v for v in store.values() if v["bound"] in bounds]
    print(f"Comparisons run: {len(done)} | all match: {all(v['match'] for v in done)}")
    print("Saved: results\\q7_results.json")


if __name__ == "__main__":
    main()
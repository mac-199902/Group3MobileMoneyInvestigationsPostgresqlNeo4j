"""q7_path.py - fetch one shortest path per successful Q7 case and verify it in PostgreSQL."""
import json

import mm_common as m

CYPHER_PATH = """
CYPHER 25
MATCH p = SHORTEST 1
  (a:Account {account_id: $src, role: 'person'})
  (()-[:TRANSFER]->(:Account {role: 'person'})){1,BOUND}
  (b:Account {account_id: $dst, role: 'person'})
RETURN [n IN nodes(p) | n.account_id] AS ids, length(p) AS links
"""

store = json.load(open(r"D:\MobileMoneyProject\results\q7_results.json"))
print(f"{'bound':>5} {'set':<4}{'len':>4}  path (account IDs)  |  checks")
for key in sorted(store, key=lambda k: (store[k]["bound"], store[k]["set"])):
    v = store[key]
    if v["pg_length"] is None:
        print(f"{v['bound']:>5} {v['set']:<4}{'none':>4}  no route within {v['bound']} transfers")
        continue
    rows = m.run_neo(CYPHER_PATH.replace("BOUND", str(v["bound"])),
                     {"src": v["source"], "dst": v["dest"]})
    ids, links = rows[0][0], rows[0][1]
    roles = dict(m.run_pg("SELECT account_id, role FROM accounts WHERE account_id = ANY(%(ids)s)",
                          {"ids": list(ids)}))
    hops = []
    for a, b in zip(ids, ids[1:]):
        c, first = m.run_pg("SELECT COUNT(*), MIN(transfer_id) FROM transfers "
                            "WHERE sender_id = %(a)s AND receiver_id = %(b)s", {"a": a, "b": b})[0]
        hops.append((c, first))
    checks = {
        "starts at source": ids[0] == v["source"],
        "ends at destination": ids[-1] == v["dest"],
        f"length {links} = {v['pg_length']}": links == v["pg_length"] == len(ids) - 1,
        "all person": all(roles.get(i) == "person" for i in ids),
        "every hop has a transfer (sender->receiver)": all(c > 0 for c, _ in hops),
    }
    print(f"{v['bound']:>5} {v['set']:<4}{links:>4}  {list(ids)}  |  "
          + " | ".join(f"{k}: {x}" for k, x in checks.items()))
    print(f"{'':>14}example transfer per hop: {[f for _, f in hops]}")
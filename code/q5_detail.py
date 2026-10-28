"""q5_detail.py - show the Q5 chains with sender, receiver, CAT time and amount."""
import json

import mm_common as m

data = json.load(open(r"D:\MobileMoneyProject\results\q5_results.json"))
SQL = """
SELECT transfer_id, sender_id, receiver_id, occurred_at, amount_rwf
FROM transfers WHERE transfer_id = %(id)s
"""
for item in data:
    if not item["pg"]:
        print(f"Set {item['set']} (account {item['account']}): no chain")
        continue
    for chain in item["pg"]:
        print(f"Set {item['set']} (account {item['account']}): chain {tuple(chain[:3])} -> final receiver {chain[3]}")
        previous = None
        for tid in chain[:3]:
            row = m.run_pg(SQL, {"id": tid})[0]
            ratio = f"{100 * row[4] / previous:.2f}% of previous" if previous else "first transfer"
            print(f"   transfer {row[0]}: {row[1]} -> {row[2]} | {m.cat_text(row[3])} CAT | "
                  f"{row[4]:,} RWF | {ratio}")
            previous = row[4]
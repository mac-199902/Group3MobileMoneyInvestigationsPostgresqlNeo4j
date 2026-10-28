"""q6_detail.py - show one Q6 cycle per set with CAT times, amounts and rule checks."""
import json

import mm_common as m

data = json.load(open(r"D:\MobileMoneyProject\results\q6_results.json"))
SQL = """
SELECT transfer_id, sender_id, receiver_id, occurred_at, amount_rwf
FROM transfers WHERE transfer_id = %(id)s
"""
for item in data:
    account = item["account"]
    start, end = m.hour_window({"A": 6, "B": 13, "C": 8, "D": 6, "E": 13, "F": 8}[item["set"]])
    if not item["pg"]:
        print(f"Set {item['set']} (account {account}): no cycle")
        continue
    ids, length = item["pg"][0]
    rows = [m.run_pg(SQL, {"id": i})[0] for i in ids]
    print(f"Set {item['set']} (account {account}): {len(item['pg'])} cycle(s); first = {tuple(ids)} (length {length})")
    previous = None
    for row in rows:
        ratio = f"{100 * row[4] / previous:6.2f}% of previous" if previous else "first transfer"
        print(f"   transfer {row[0]}: {row[1]} -> {row[2]} | {m.cat_text(row[3])} CAT | "
              f"{row[4]:,} RWF | {ratio}")
        previous = row[4]
    times = [r[3] for r in rows]
    checks = {
        "starts at review account": rows[0][1] == account,
        "ends at review account": rows[-1][2] == account,
        "chain is connected": all(rows[i][2] == rows[i + 1][1] for i in range(len(rows) - 1)),
        "all inside the hour": all(start <= t < end for t in times),
        "strictly increasing time": all(times[i] < times[i + 1] for i in range(len(times) - 1)),
        f"span {times[-1] - times[0]} s <= 1800": times[-1] - times[0] <= 1800,
        "amounts within 90-105%": all(90 * rows[i][4] <= 100 * rows[i + 1][4] <= 105 * rows[i][4]
                                       for i in range(len(rows) - 1)),
        "first return only": all(r[2] != account for r in rows[:-1]),
    }
    print("   checks:", " | ".join(f"{k}: {v}" for k, v in checks.items()))
"""pair_detail.py - transfers, times, amounts and device evidence for the pair A (998) and D (237998)."""
import json

import mm_common as m

PATHS = {"A": [998, 8917, 16836, 24755], "D": [237998, 5917, 13836, 21755]}   # verified Q7 routes
HOP = """SELECT transfer_id, sender_id, receiver_id, occurred_at, amount_rwf FROM transfers
         WHERE transfer_id = (SELECT MIN(transfer_id) FROM transfers
                              WHERE sender_id = %(a)s AND receiver_id = %(b)s)"""
RES = r"D:\MobileMoneyProject\results"
q1 = {r["set"]: r for r in json.load(open(rf"{RES}\q1_results.json"))}
q3 = {r["set"]: r for r in json.load(open(rf"{RES}\q3_results.json"))}

for s, path in PATHS.items():
    count, total = q1[s]["pg"][0]
    print(f"=== Set {s}: review account {path[0]}, Q7 destination {path[-1]} ===")
    print(f"Q1: {count} outgoing transfer(s) in the review hour, {total:,} RWF")
    previous = None
    for a, b in zip(path, path[1:]):
        t = m.run_pg(HOP, {"a": a, "b": b})[0]
        if previous:
            gap = t[3] - previous[3]
            note = f"gap {gap:+d} s ({gap / 86400:+.2f} days) | {100 * t[4] / previous[4]:.2f}% of previous"
        else:
            note = "first hop on the route"
        print(f"  transfer {t[0]}: {t[1]} -> {t[2]} | {m.cat_text(t[3])} CAT | {t[4]:,} RWF | {note}")
        previous = t
    print("  Q3 shared-device rows (other account, device, type, overlap days):")
    for row in q3[s]["pg"]:
        print(f"     account {row[0]:>7} on device {row[1]:>7} ({row[2]}), days {row[3]} to {row[4]}")
    print()
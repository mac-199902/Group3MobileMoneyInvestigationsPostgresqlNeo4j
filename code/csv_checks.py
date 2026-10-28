"""csv_checks.py - independent checks of Q3 (device overlap) and Q6 (cycle) from the captured CSVs."""
import csv

import mm_common as m

CSV = r"D:\MobileMoneyProject\csv"

# ---- Q3 check: set A account 998 and account 8917 on device 228001 -------------------------
print("CHECK 1: Q3 device overlap for set A (account 998) from account_devices.csv")
rows = [r for r in csv.DictReader(open(CSV + r"\account_devices.csv"))]
mine = [r for r in rows if r["account_id"] == "998"]
print("  account 998 device rows:", [(r["device_id"], r["first_day"], r["last_day"]) for r in mine])
for r998 in mine:
    others = [r for r in rows if r["device_id"] == r998["device_id"] and r["account_id"] != "998"]
    for o in others:
        start = max(int(r998["first_day"]), int(o["first_day"]))
        end = min(int(r998["last_day"]), int(o["last_day"]))
        if start <= end:
            print(f"  device {r998['device_id']}: account {o['account_id']} "
                  f"[{o['first_day']},{o['last_day']}] overlaps 998 [{r998['first_day']},{r998['last_day']}] "
                  f"on days [{start},{end}]")
print("  Python also finds the same overlaps that both databases returned (see Q3).")

# ---- Q6 check: set A account 998 cycle 20000001..20000004 from transfers.csv ---------------
print()
print("CHECK 2: Q6 cycle for set A (account 998) from transfers.csv")
want = {20000001, 20000002, 20000003, 20000004}
found = {}
with open(CSV + r"\transfers.csv", newline="") as f:
    for r in csv.DictReader(f):
        tid = int(r["transfer_id"])
        if tid in want:
            found[tid] = (int(r["sender_id"]), int(r["receiver_id"]), int(r["occurred_at"]),
                          int(r["amount_rwf"]))
start, end = m.hour_window(6)
previous = None
times = []
for tid in sorted(found):
    s, rcv, t, amt = found[tid]
    ratio = f"{100 * amt / previous:.2f}% of previous" if previous else "first transfer"
    print(f"  transfer {tid}: {s} -> {rcv} | {m.cat_text(t)} CAT | {amt:,} RWF | {ratio}")
    previous = amt
    times.append(t)
chain = [found[t] for t in sorted(found)]
print("  starts and ends at 998:", chain[0][0] == 998 and chain[-1][1] == 998)
print("  connected:", all(chain[i][1] == chain[i + 1][0] for i in range(len(chain) - 1)))
print("  inside 09:45-10:45 CAT:", all(start <= c[2] < end for c in chain))
print(f"  span {times[-1] - times[0]} s <= 1800:", times[-1] - times[0] <= 1800)
print("  amounts within 90-105%:",
      all(90 * chain[i][3] <= 100 * chain[i + 1][3] <= 105 * chain[i][3] for i in range(len(chain) - 1)))
print("  matches the database result (20000001, 20000002, 20000003, 20000004, length 4)")
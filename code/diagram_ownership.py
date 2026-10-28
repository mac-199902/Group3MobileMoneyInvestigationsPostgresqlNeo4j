"""diagram_ownership.py - ownership and device network within 4 links of account 998 (set A)."""
import json

import matplotlib.pyplot as plt

import mm_common as m

START, MAX_DEPTH = 998, 4
Q_CUST = "SELECT account_id, customer_id FROM accounts WHERE account_id = ANY(%(x)s)"
Q_ACCTS = "SELECT account_id, customer_id FROM accounts WHERE customer_id = ANY(%(x)s)"
Q_DEVS = "SELECT account_id, device_id FROM account_devices WHERE account_id = ANY(%(x)s)"
Q_ON = "SELECT account_id, device_id FROM account_devices WHERE device_id = ANY(%(x)s)"

depth = {("A", START): 0}
edges = set()
frontier = [("A", START)]
for d in range(1, MAX_DEPTH + 1):
    accts = [i for k, i in frontier if k == "A"]
    custs = [i for k, i in frontier if k == "C"]
    devs = [i for k, i in frontier if k == "D"]
    found = []
    if accts:
        found += [(("C", c), ("A", a)) for a, c in m.run_pg(Q_CUST, {"x": accts})]
        found += [(("A", a), ("D", dv)) for a, dv in m.run_pg(Q_DEVS, {"x": accts})]
    if custs:
        found += [(("C", c), ("A", a)) for a, c in m.run_pg(Q_ACCTS, {"x": custs})]
    if devs:
        found += [(("A", a), ("D", dv)) for a, dv in m.run_pg(Q_ON, {"x": devs})]
    frontier = []
    for u, v in found:
        edges.add((u, v))
        for node in (u, v):
            if node not in depth:
                depth[node] = d
                frontier.append(node)

n_acc = sum(1 for k, i in depth if k == "A" and i != START)
stored = sum(r[1] for r in json.load(open(r"D:\MobileMoneyProject\results\q4_results.json"))["A-4"]["pg"])
print(f"Accounts within 4 links of {START}: {n_acc} (Q4 stored result: {stored}) -> {'MATCH' if n_acc == stored else 'CHECK'}")

cycle = {r[0] for r in m.run_pg("SELECT sender_id FROM transfers WHERE transfer_id BETWEEN 20000001 AND 20000004", {})}
access = dict(m.run_pg("SELECT device_id, access_type FROM devices WHERE device_id = ANY(%(x)s)",
                       {"x": [i for k, i in depth if k == "D"]}))
accounts = sorted((i for k, i in depth if k == "A"), key=lambda i: (depth[("A", i)], i))
pos = {("A", i): (5.0, (len(accounts) - 1) / 2 - idx) for idx, i in enumerate(accounts)}
nbrs = {}
for u, v in edges:
    if u[0] == "C":
        nbrs.setdefault(u, []).append(v)
    if v[0] == "D":
        nbrs.setdefault(v, []).append(u)
for kind, x in (("C", 0.0), ("D", 10.0)):
    ids = [(kind, i) for k, i in depth if k == kind]
    ids.sort(key=lambda node: sum(pos[a][1] for a in nbrs.get(node, [])) / max(len(nbrs.get(node, [])), 1),
             reverse=True)
    for idx, node in enumerate(ids):
        pos[node] = (x, (len(ids) - 1) / 2 - idx)

fig, ax = plt.subplots(figsize=(14, 9))
for u, v in edges:
    ax.annotate("", xy=pos[v], xytext=pos[u],
                arrowprops=dict(arrowstyle="-|>", lw=0.9, color="#777", shrinkA=18, shrinkB=18))
users = {}
for u, v in edges:
    if v[0] == "D":
        users[v[1]] = users.get(v[1], 0) + 1
for (kind, i), (x, y) in pos.items():
    if kind == "C":
        text, colour = f"Customer {i}", "#d6ecf7"
    elif kind == "D":
        text, colour = f"Device {i}\n{access.get(i, '')} | {users.get(i, 0)} accts", "#dff3e0"
    else:
        tag = "\n(review)" if i == START else ("\n(in cycle)" if i in cycle else "")
        text, colour = f"Account {i}{tag}", "#ffe3a8" if i == START else ("#f9d0c4" if i in cycle else "#eeeeee")
    ax.text(x, y, text, ha="center", va="center", fontsize=8.5, zorder=5,
            bbox=dict(boxstyle="round,pad=0.3", fc=colour, ec="#333"))
for label, x in (("Customers (OWNS)", 0.0), ("Accounts", 5.0), ("Devices (USED_DEVICE)", 10.0)):
    ax.text(x, len(accounts) / 2 + 0.6, label, ha="center", fontsize=11, fontweight="bold")
ax.set_title("Ownership and device network within 4 links of account 998 (set A); "
             "arrows show the stored direction", fontsize=11)
ax.set_xlim(-1.8, 11.8)
ax.set_ylim(-len(accounts) / 2 - 0.8, len(accounts) / 2 + 1.4)
ax.axis("off")
plt.tight_layout()
plt.savefig(r"D:\MobileMoneyProject\plans\ownership_device_998.png", dpi=150)
plt.show()
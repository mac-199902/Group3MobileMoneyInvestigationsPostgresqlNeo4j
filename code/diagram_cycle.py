"""diagram_cycle.py - the Q6 cycles for sets A and C, drawn from the stored transfers."""
import math
from datetime import datetime

import matplotlib.pyplot as plt

import mm_common as m

CYCLES = {"Set A: account 998, 6 September": [20000001, 20000002, 20000003, 20000004],
          "Set C: account 206978, 8 September": [20000229, 20000230, 20000231, 20000232,
                                                  20000233, 20000234]}
SQL = ("SELECT transfer_id, sender_id, receiver_id, occurred_at, amount_rwf "
       "FROM transfers WHERE transfer_id = ANY(%(ids)s)")

fig, axes = plt.subplots(1, 2, figsize=(17, 8.5))
for ax, (title, ids) in zip(axes, CYCLES.items()):
    rows = {r[0]: r for r in m.run_pg(SQL, {"ids": ids})}
    hops = [rows[i] for i in ids]
    n = len(hops)
    pos = {h[1]: (math.cos(math.radians(90 - 360 * k / n)), math.sin(math.radians(90 - 360 * k / n)))
           for k, h in enumerate(hops)}
    for h in hops:
        (x1, y1), (x2, y2) = pos[h[1]], pos[h[2]]
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", lw=1.5, color="#333", shrinkA=26, shrinkB=26,
                                    connectionstyle="arc3,rad=0.12"))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        norm = math.hypot(mx, my) or 1
        lx, ly = 1.45 * mx / norm, 1.45 * my / norm
        side = "left" if lx > 0.25 else ("right" if lx < -0.25 else "center")
        clock = datetime.fromtimestamp(h[3], m.CAT).strftime("%H:%M:%S")
        ax.text(lx, ly, f"transfer {h[0]}\n{clock} CAT\n{h[4]:,} RWF", ha=side, va="center", fontsize=8.5)
    for k, h in enumerate(hops):
        ax.text(*pos[h[1]], f"Account\n{h[1]}", ha="center", va="center", fontsize=10, fontweight="bold",
                zorder=5, bbox=dict(boxstyle="round,pad=0.4", fc="#ffe3a8" if k == 0 else "#dbe9f6", ec="#333"))
    ax.set_title(title + "\n(each amount 98.00% of the previous; review account in amber)",
                 fontsize=11, pad=14)
    ax.set_xlim(-2.6, 2.6)
    ax.set_ylim(-1.9, 1.9)
    ax.set_aspect("equal")
    ax.axis("off")
fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.03, wspace=0.02)
plt.savefig(r"D:\MobileMoneyProject\plans\cycles_A_C.png", dpi=150)
plt.show()
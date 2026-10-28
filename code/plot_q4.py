"""plot_q4.py - Q4 accounts reached versus number of links."""
import json

import matplotlib.pyplot as plt

store = json.load(open(r"D:\MobileMoneyProject\results\q4_results.json"))
depths = [4, 6, 8, 10]
fig, ax = plt.subplots(figsize=(9, 6))
for name in "ABCDEF":
    counts = [sum(r[1] for r in store[f"{name}-{d}"]["pg"]) for d in depths]
    ax.plot(depths, counts, marker="o",
            label=f"Set {name} (account {store[f'{name}-4']['account']})")
ax.set_yscale("log")
ax.set_xticks(depths)
ax.set_xlabel("Maximum number of links (OWNS or USED_DEVICE)")
ax.set_ylabel("Distinct other accounts reached (count, log scale)")
ax.set_title("Q4 network size against depth")
ax.grid(alpha=0.3)
ax.legend()
fig.text(0.5, 0.005, "Note: log scale on the y-axis.", ha="center", fontsize=9)
plt.tight_layout(rect=(0, 0.02, 1, 1))
plt.savefig(r"D:\MobileMoneyProject\results\q4_count_vs_depth.png", dpi=150)
plt.show()
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

fig, ax = plt.subplots(figsize=(14, 7.5))
ax.set_xlim(0, 140)
ax.set_ylim(0, 75)
ax.axis("off")
ax.set_title("Neo4j graph schema: mobile_money", fontsize=13, fontweight="bold")

R = 9
nodes = {
    "Customer": (22, 30, "#dbe9f6", ["customer_id (int)", "region (string)"]),
    "Account": (70, 30, "#e3f3e0", ["account_id (int)", "role (string)"]),
    "Device": (118, 30, "#fbe8d3", ["device_id (int)", "access_type (string)"]),
}
for name, (x, y, color, props) in nodes.items():
    ax.add_patch(Circle((x, y), R, facecolor=color, edgecolor="#333333", lw=1.5))
    ax.text(x, y, name, ha="center", va="center", fontsize=11, fontweight="bold")
    for i, p in enumerate(props):
        ax.text(x, y - R - 4 - i * 4, p, ha="center", va="center",
                fontsize=9, family="monospace")


def arrow(p1, p2, rad=0.0):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=18, lw=1.5,
                                 color="#333333", connectionstyle=f"arc3,rad={rad}"))


arrow((22 + R, 30), (70 - R, 30))
ax.text(46, 32.5, "OWNS", ha="center", fontsize=10, fontweight="bold")

arrow((70 + R, 30), (118 - R, 30))
ax.text(94, 32.5, "USED_DEVICE", ha="center", fontsize=10, fontweight="bold")
ax.text(94, 26, "first_day, last_day, observations (int)", ha="center",
        fontsize=8.5, family="monospace")

arrow((64, 36.7), (76, 36.7), rad=-1.6)
ax.text(70, 52, "TRANSFER", ha="center", fontsize=10, fontweight="bold")
ax.text(70, 56, "transfer_id (long), occurred_at (long), amount_rwf (int)",
        ha="center", fontsize=8.5, family="monospace")

ax.text(70, 5, "Each transfer is a separate relationship, so repeated payments "
        "between the same accounts are kept.", ha="center", fontsize=9)
ax.text(70, 1.5, "accounts.customer_id becomes the OWNS relationship; "
        "account_devices and transfers become relationships with properties.",
        ha="center", fontsize=9)

plt.savefig(r"D:\MobileMoneyProject\plans\graph_schema.png", dpi=150, bbox_inches="tight")
print("Saved D:\\MobileMoneyProject\\plans\\graph_schema.png")
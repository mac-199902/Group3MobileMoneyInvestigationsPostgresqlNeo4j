import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

W, RH, HH = 34, 3.4, 4.2
TABLES = {
    "customers": (4, 76, [("PK", "customer_id", "INTEGER"), ("", "region", "TEXT")]),
    "accounts": (50, 76, [("PK", "account_id", "INTEGER"),
                          ("FK", "customer_id", "INTEGER"), ("", "role", "TEXT")]),
    "transfers": (98, 76, [("PK", "transfer_id", "BIGINT"), ("FK", "sender_id", "INTEGER"),
                           ("FK", "receiver_id", "INTEGER"), ("", "occurred_at", "BIGINT"),
                           ("", "amount_rwf", "INTEGER")]),
    "devices": (4, 40, [("PK", "device_id", "INTEGER"), ("", "access_type", "TEXT")]),
    "account_devices": (50, 40, [("PK,FK", "account_id", "INTEGER"),
                                 ("PK,FK", "device_id", "INTEGER"),
                                 ("", "first_day", "SMALLINT"),
                                 ("", "last_day", "SMALLINT"),
                                 ("", "observations", "INTEGER")]),
}

fig, ax = plt.subplots(figsize=(14, 8.5))
ax.set_xlim(0, 140)
ax.set_ylim(10, 84)
ax.axis("off")
ax.set_title("PostgreSQL schema: mobile_money (all columns NOT NULL)",
             fontsize=13, fontweight="bold")

box = {}
for name, (x, top, cols) in TABLES.items():
    h = HH + RH * len(cols)
    box[name] = (x, top, W, h)
    ax.add_patch(Rectangle((x, top - h), W, h, fill=False, lw=1.4))
    ax.add_patch(Rectangle((x, top - HH), W, HH, facecolor="#dbe9f6", lw=1.4))
    ax.text(x + W / 2, top - HH / 2, name, ha="center", va="center",
            fontsize=11, fontweight="bold")
    for i, (key, col, typ) in enumerate(cols):
        y = top - HH - RH * (i + 0.5)
        ax.text(x + 1, y, key, fontsize=8, va="center", color="#8a4b00", fontweight="bold")
        ax.text(x + 7, y, col, fontsize=9.5, va="center", family="monospace")
        ax.text(x + W - 1, y, typ, fontsize=8.5, va="center", ha="right", color="#555555")


def link(p1, p2, label, lab_xy):
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#333333"))
    ax.text(lab_xy[0], lab_xy[1], label, fontsize=9, ha="center", va="bottom", color="#333333")


cx, ct, cw, ch = box["customers"]
ax_, at, aw, ah = box["accounts"]
tx, tt, tw, th = box["transfers"]
dx, dt, dw, dh = box["devices"]
adx, adt, adw, adh = box["account_devices"]

link((cx + cw, at - 6), (ax_, at - 6), "owns (1 to many)", ((cx + cw + ax_) / 2, at - 5.5))
link((ax_ + aw, tt - 8), (tx, tt - 8), "sender_id (1 to many)", ((ax_ + aw + tx) / 2, tt - 7.5))
link((ax_ + aw, tt - 14), (tx, tt - 14), "receiver_id (1 to many)", ((ax_ + aw + tx) / 2, tt - 13.5))
link((ax_ + aw / 2, at - ah), (adx + adw / 2, adt), "uses (1 to many)", (ax_ + aw / 2 + 11, 50))
link((dx + dw, dt - 8), (adx, dt - 8), "observed on (1 to many)", ((dx + dw + adx) / 2, dt - 7.5))

plt.savefig(r"D:\MobileMoneyProject\plans\postgres_schema.png", dpi=150, bbox_inches="tight")
plt.show()
"""capture.py - stream the five generator outputs to CSV with audit totals."""
import csv
import json
import os
from datetime import datetime, timezone, timedelta
from time import perf_counter

import mobile_money_generator as g

CSV_DIR = r"D:\MobileMoneyProject\csv"
RES_DIR = r"D:\MobileMoneyProject\results"
CAT = timezone(timedelta(hours=2))
EXPECTED = {"customers": 228_000, "accounts": 248_000, "devices": 228_600,
            "account_devices": 285_600, "transfers": 20_003_300}
STREAMS = [("customers", g.iter_customers), ("accounts", g.iter_accounts),
           ("devices", g.iter_devices), ("account_devices", g.iter_account_devices),
           ("transfers", g.iter_transfers)]

os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)
log_file = open(os.path.join(RES_DIR, "capture_log.txt"), "w", encoding="utf-8")


def log(message):
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {message}"
    print(line, flush=True)
    log_file.write(line + "\n")
    log_file.flush()


def cat_text(epoch):
    return datetime.fromtimestamp(epoch, CAT).strftime("%Y-%m-%d %H:%M:%S CAT")


results = {}
overall_start = perf_counter()
log("Capture started. Period: " + g.dataset_info()["period"])

for name, make_iterator in STREAMS:
    path = os.path.join(CSV_DIR, name + ".csv")
    consumed = written = 0
    total_amount = 0
    first_time = last_time = None
    start = perf_counter()
    log(f"[{name}] started -> {path}")

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=g.FIELDS[name])
        writer.writeheader()
        for row in make_iterator():
            consumed += 1
            writer.writerow(row)
            written += 1
            if name == "transfers":
                t = row["occurred_at"]
                total_amount += row["amount_rwf"]
                if first_time is None or t < first_time:
                    first_time = t
                if last_time is None or t > last_time:
                    last_time = t
                if consumed % 1_000_000 == 0:
                    log(f"[transfers] {consumed:>10,} rows written "
                        f"({perf_counter() - start:,.0f} s)")

    seconds = perf_counter() - start
    size = os.path.getsize(path)
    results[name] = {"consumed": consumed, "written": written,
                     "expected": EXPECTED[name],
                     "match": consumed == written == EXPECTED[name],
                     "seconds": round(seconds, 1), "csv_bytes": size}
    if name == "transfers":
        results[name].update({"earliest_occurred_at": first_time,
                              "latest_occurred_at": last_time,
                              "earliest_cat": cat_text(first_time),
                              "latest_cat": cat_text(last_time),
                              "sum_amount_rwf": total_amount})
    log(f"[{name}] done: consumed {consumed:,}, written {written:,}, "
        f"{seconds:,.1f} s, {size / 1e9:.3f} GB")

total_seconds = perf_counter() - overall_start
total_rows = sum(r["written"] for r in results.values())
results["_total"] = {"rows": total_rows, "seconds": round(total_seconds, 1),
                     "csv_bytes": sum(r["csv_bytes"] for r in results.values()
                                      if "csv_bytes" in r)}

with open(os.path.join(RES_DIR, "capture_audit.json"), "w", encoding="utf-8") as out:
    json.dump(results, out, indent=2)

log("=" * 74)
log(f"{'stream':<16}{'consumed':>12}{'written':>12}{'expected':>12}{'match':>7}"
    f"{'seconds':>9}{'CSV GB':>8}")
for name, _ in STREAMS:
    r = results[name]
    log(f"{name:<16}{r['consumed']:>12,}{r['written']:>12,}{r['expected']:>12,}"
        f"{str(r['match']):>7}{r['seconds']:>9,.1f}{r['csv_bytes'] / 1e9:>8.3f}")
t = results["transfers"]
log(f"TOTAL rows {total_rows:,} (expected 20,993,500) in {total_seconds:,.1f} s, "
    f"CSV {results['_total']['csv_bytes'] / 1e9:.3f} GB")
log(f"transfers: count {t['written']:,} | sum amount_rwf {t['sum_amount_rwf']:,}")
log(f"transfers: earliest {t['earliest_occurred_at']} = {t['earliest_cat']}")
log(f"transfers: latest   {t['latest_occurred_at']} = {t['latest_cat']}")
log("Audit saved: results\\capture_audit.json")
log_file.close()
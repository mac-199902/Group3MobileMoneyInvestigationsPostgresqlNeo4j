"""prepare_import.py - typed-header copies of the CSVs for neo4j-admin import."""
import csv
import os
import shutil
import time

SRC = r"D:\MobileMoneyProject\csv"
TMP = r"D:\MobileMoneyProject\import_tmp"
RES = r"D:\MobileMoneyProject\results"

SOURCE_HEADERS = {
    "customers": "customer_id,region",
    "accounts": "account_id,customer_id,role",
    "devices": "device_id,access_type",
    "account_devices": "account_id,device_id,first_day,last_day,observations",
    "transfers": "transfer_id,sender_id,receiver_id,occurred_at,amount_rwf",
}
NEO_HEADERS = {
    "customers": "customer_id:ID(Customer),region:string",
    "accounts": "account_id:ID(Account),:IGNORE,role:string",
    "devices": "device_id:ID(Device),access_type:string",
    "account_devices": ":START_ID(Account),:END_ID(Device),first_day:int,last_day:int,observations:int",
    "transfers": "transfer_id:long,:START_ID(Account),:END_ID(Account),occurred_at:long,amount_rwf:int",
}
OWNS_HEADER = ":START_ID(Customer),:END_ID(Account)"
EXPECTED = {"customers": 228_000, "accounts": 248_000, "devices": 228_600,
            "account_devices": 285_600, "transfers": 20_003_300, "owns": 248_000}

os.makedirs(TMP, exist_ok=True)
os.makedirs(RES, exist_ok=True)
for leftover in os.listdir(TMP):
    if leftover.endswith(".csv"):
        os.remove(os.path.join(TMP, leftover))
log_file = open(os.path.join(RES, "prepare_import_log.txt"), "w", encoding="utf-8")


def log(message):
    print(message, flush=True)
    log_file.write(message + "\n")
    log_file.flush()


def count_data_rows(path):
    lines = 0
    with open(path, "rb") as f:
        while chunk := f.read(16 * 1024 * 1024):
            lines += chunk.count(b"\n")
    return lines - 1


sizes_before = {n: os.path.getsize(os.path.join(SRC, n + ".csv")) for n in SOURCE_HEADERS}
results = {}
overall = time.perf_counter()
log("prepare_import started")

for name in SOURCE_HEADERS:
    start = time.perf_counter()
    src_path = os.path.join(SRC, name + ".csv")
    dst_path = os.path.join(TMP, name + ".csv")
    with open(src_path, "rb") as fin, open(dst_path, "wb") as fout:
        first = fin.readline()
        if first.decode("utf-8").strip() != SOURCE_HEADERS[name]:
            raise SystemExit(f"Unexpected header in {name}.csv: {first!r}")
        newline = b"\r\n" if first.endswith(b"\r\n") else b"\n"
        fout.write(NEO_HEADERS[name].encode("utf-8") + newline)
        shutil.copyfileobj(fin, fout, 16 * 1024 * 1024)
    rows = count_data_rows(dst_path)
    results[name] = rows
    log(f"[{name}] rows {rows:,} | {os.path.getsize(dst_path):,} bytes | "
        f"{time.perf_counter() - start:.1f} s")

start = time.perf_counter()
pairs = []
with open(os.path.join(SRC, "accounts.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        pairs.append((int(row["customer_id"]), int(row["account_id"])))
pairs.sort()
with open(os.path.join(TMP, "owns.csv"), "w", newline="", encoding="utf-8") as f:
    f.write(OWNS_HEADER + "\r\n")
    csv.writer(f).writerows(pairs)
results["owns"] = count_data_rows(os.path.join(TMP, "owns.csv"))
log(f"[owns] rows {results['owns']:,} (sorted by customer_id, account_id) | "
    f"{time.perf_counter() - start:.1f} s")

sizes_after = {n: os.path.getsize(os.path.join(SRC, n + ".csv")) for n in SOURCE_HEADERS}
log("=" * 70)
for name in ["customers", "accounts", "devices", "account_devices", "transfers", "owns"]:
    log(f"{name:<16}{results[name]:>12,} expected {EXPECTED[name]:>12,}  "
        f"match {results[name] == EXPECTED[name]}")
log(f"Source CSVs unchanged: {sizes_before == sizes_after}")
log("")
log("Typed headers written to import_tmp:")
for name in ["customers", "accounts", "devices", "account_devices", "transfers"]:
    log(f"  {name + '.csv':<22}{NEO_HEADERS[name]}")
log(f"  {'owns.csv':<22}{OWNS_HEADER}")
log(f"Total {time.perf_counter() - overall:.1f} s")
log_file.close()
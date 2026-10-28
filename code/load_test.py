"""load_test.py - concurrent load test: Q4 depth 10 and Q7 length-only bound 6, sets A-B-C cycled.

Usage: python load_test.py pg     (PostgreSQL running, Neo4j stopped)
       python load_test.py neo    (Neo4j running, PostgreSQL service stopped)
Resumable. Client processes load only lt_common, queries and ONE database driver.
"""
import sys

for _name in ("numpy", "pandas", "pyarrow"):     # block heavy optional imports in every process
    sys.modules[_name] = None

import json
import math
import multiprocessing as mp
import os
import time
from statistics import median

import lt_common as lc
import queries as q
from lt_common import SQL_Q7_V2, q7_params

DURATION, QUERY_TIMEOUT = 15, 60
CLIENTS = (1, 4, 8, 16)
REPS = 3
WORKLOADS = ("Q4", "Q7")
SET_ORDER = ("A", "B", "C")
OUT_DIR = r"D:\MobileMoneyProject\results"


def request_spec(engine, workload, set_name):
    account, dest, day = lc.SETS[set_name]
    if workload == "Q4":
        if engine == "pg":
            return q.SQL_Q4, {"account": account, "depth": 10}
        return q.CYPHER_Q4.replace("DEPTH", "10"), {"account": account}
    if engine == "pg":
        return SQL_Q7_V2, q7_params(account, dest, 6)
    return q.CYPHER_Q7.replace("BOUND", "6"), {"src": account, "dst": dest}


class Connection:
    def __init__(self, engine):
        self.engine = engine
        if engine == "pg":
            import psycopg
            self.conn = psycopg.connect(host="localhost", dbname="mobile_money", user="postgres",
                                        password=os.environ["PG_PASSWORD"], autocommit=True)
            with self.conn.cursor() as cur:
                cur.execute(f"SET statement_timeout = '{QUERY_TIMEOUT}s'")
        else:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver("bolt://localhost:7687",
                                               auth=("neo4j", os.environ["NEO_PASSWORD"]))
            self.session = self.driver.session(database="neo4j")

    def run(self, text, params):
        if self.engine == "pg":
            with self.conn.cursor() as cur:
                cur.execute(text, params)
                return cur.fetchall()
        tx = self.session.begin_transaction(timeout=QUERY_TIMEOUT)
        try:
            return [r.values() for r in tx.run(text, params)]
        finally:
            try:
                tx.close()
            except Exception:
                pass


def client(engine, workload, index, barrier, start_time, queue):
    try:
        conn = Connection(engine)
        specs = {s: request_spec(engine, workload, s) for s in SET_ORDER}
        for s in SET_ORDER:                                   # one untimed warm-up cycle A-B-C
            try:
                conn.run(*specs[s])
            except Exception:
                pass
        barrier.wait(timeout=120)                             # synchronised start
    except Exception:
        try:
            barrier.abort()                                   # release the others quickly
        except Exception:
            pass
        queue.put([])
        return
    if index == 0:
        with start_time.get_lock():
            start_time.value = time.time()                    # common start time (barrier release)
    while start_time.value == 0.0:
        time.sleep(0.0005)
    deadline = start_time.value + DURATION                    # common deadline, 15 s after release
    log = []
    while time.time() < deadline:                             # start a cycle only before the deadline
        for s in SET_ORDER:                                   # a started cycle is always finished
            t0 = time.perf_counter()
            try:
                rows = conn.run(*specs[s])
                status, dg = "OK", lc.digest(rows)
            except Exception as exc:
                text = str(exc).lower()
                status = "TIMEOUT" if any(w in text for w in ("cancel", "timeout", "timed out")) else "ERROR"
                dg = None
            t1 = time.perf_counter()
            log.append((index, s, status, (t1 - t0) * 1000, time.time(), dg))
    queue.put(log)


def run_once(engine, workload, n_clients, reference):
    ctx = mp.get_context("spawn")
    start_time = ctx.Value("d", 0.0)
    barrier = ctx.Barrier(n_clients)
    queue = ctx.Queue()
    procs = [ctx.Process(target=client, args=(engine, workload, i, barrier, start_time, queue))
             for i in range(n_clients)]
    for p in procs:
        p.start()
    logs = []
    for _ in procs:
        try:
            logs.append(queue.get(timeout=DURATION + 170))
        except Exception:
            break
    for p in procs:
        p.join(timeout=10)
        if p.is_alive():
            p.terminate()
    failed_clients = (n_clients - len(logs)) + sum(1 for l in logs if not l)
    start = start_time.value
    records = [r for log in logs for r in log]
    ok = [r for r in records if r[2] == "OK" and r[5] == reference[r[1]]]
    wrong = [r for r in records if r[2] == "OK" and r[5] != reference[r[1]]]
    lat = sorted(r[3] for r in ok)
    end = max((r[4] for r in records), default=start)
    elapsed = max(end - start, 1e-9)
    p95 = lat[math.ceil(0.95 * len(lat)) - 1] if lat else None
    return {"throughput": len(ok) / elapsed, "median_ms": median(lat) if lat else None, "p95_ms": p95,
            "completed": len(ok), "wrong": len(wrong),
            "errors": sum(r[2] == "ERROR" for r in records) + failed_clients,
            "timeouts": sum(r[2] == "TIMEOUT" for r in records), "elapsed": elapsed,
            "requests": [list(r[:5]) for r in records]}


def main():
    engine = sys.argv[1] if len(sys.argv) > 1 else ""
    if engine not in ("pg", "neo"):
        raise SystemExit("usage: python load_test.py pg|neo")
    out = rf"{OUT_DIR}\load_{engine}.jsonl"
    done = set()
    if os.path.exists(out):
        done = {(r["workload"], r["clients"], r["rep"]) for r in map(json.loads, open(out))}
    probe = Connection(engine)
    log = open(out, "a", buffering=1)
    print(f"{'workload':<9}{'clients':>8}{'rep':>4}{'req/s':>9}{'median ms':>11}{'p95 ms':>10}"
          f"{'done':>7}{'wrong':>7}{'err':>5}{'t/o':>5}", flush=True)
    for workload in WORKLOADS:
        reference = {s: lc.digest(probe.run(*request_spec(engine, workload, s))) for s in SET_ORDER}
        for n in CLIENTS:
            for rep in range(1, REPS + 1):
                if (workload, n, rep) in done:
                    continue
                r = run_once(engine, workload, n, reference)
                rec = {"engine": engine, "workload": workload, "clients": n, "rep": rep,
                       **{k: v for k, v in r.items() if k != "requests"}, "requests": r["requests"]}
                log.write(json.dumps(rec) + "\n")
                fmt = lambda x: "-" if x is None else f"{x:.1f}"
                print(f"{workload:<9}{n:>8}{rep:>4}{r['throughput']:>9.2f}{fmt(r['median_ms']):>11}"
                      f"{fmt(r['p95_ms']):>10}{r['completed']:>7}{r['wrong']:>7}{r['errors']:>5}"
                      f"{r['timeouts']:>5}", flush=True)
                time.sleep(3)
    print("All combinations finished for engine", engine, flush=True)


if __name__ == "__main__":
    main()
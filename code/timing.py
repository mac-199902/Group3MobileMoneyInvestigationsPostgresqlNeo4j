"""timing.py - time 21 cases on ONE engine: 3 untimed warm-ups + 5 measured runs each.

Usage: python timing.py pg     (PostgreSQL running, Neo4j stopped)
       python timing.py neo    (Neo4j running, PostgreSQL service stopped)
Resumable: cases already finished are skipped if the script is started again.
"""
import hashlib
import json
import os
import sys
from datetime import datetime
from time import perf_counter

import mm_common as m
import queries as q

WARMUPS, RUNS = 3, 5
WARM_TIMEOUT, RUN_TIMEOUT = 180, 60

engine = sys.argv[1] if len(sys.argv) > 1 else ""
if engine not in ("pg", "neo"):
    raise SystemExit("usage: python timing.py pg|neo")
OUT = rf"D:\MobileMoneyProject\results\timing_{engine}.jsonl"


def build_cases():
    cases = []
    for question in ("Q1", "Q3", "Q5", "Q6"):
        for s in ("B", "E"):
            cases.append((f"{question}-{s}", question, s, {}))
    cases.append(("Q2-month", "Q2", None, {}))
    for s in ("B", "E"):
        for depth in (4, 6, 8, 10):
            cases.append((f"Q4-{s}-d{depth}", "Q4", s, {"depth": depth}))
    for s in ("B", "E"):
        for bound in (4, 6):
            cases.append((f"Q7-{s}-b{bound}", "Q7", s, {"bound": bound}))
    return cases


def query_for(question, set_name, extra):
    """Return (query text for this engine, parameters)."""
    pg = engine == "pg"
    if set_name:
        account, dest, day = m.SETS[set_name]
        start, end = m.hour_window(day)
    if question == "Q1":
        return (q.SQL_Q1 if pg else q.CYPHER_Q1), {"account": account, "start": start, "end": end}
    if question == "Q2":
        return (q.SQL_Q2 if pg else q.CYPHER_Q2), {}
    if question == "Q3":
        return (q.SQL_Q3 if pg else q.CYPHER_Q3), {"account": account}
    if question == "Q4":
        text = q.SQL_Q4 if pg else q.CYPHER_Q4.replace("DEPTH", str(extra["depth"]))
        return text, {"account": account, "depth": extra["depth"]}
    if question == "Q5":
        return (q.SQL_Q5 if pg else q.CYPHER_Q5), {"account": account, "start": start, "end": end}
    if question == "Q6":
        return (q.SQL_Q6 if pg else q.CYPHER_Q6), {"account": account, "start": start, "end": end}
    if question == "Q7":
        text = q.SQL_Q7 if pg else q.CYPHER_Q7.replace("BOUND", str(extra["bound"]))
        return text, {"src": account, "dst": dest, "bound": extra["bound"]}
    raise ValueError(question)


class PgRunner:
    def __init__(self):
        self.conn = m.pg()            # one persistent connection, autocommit

    def set_timeout(self, seconds):
        with self.conn.cursor() as cur:
            cur.execute(f"SET statement_timeout = '{seconds}s'")

    def run(self, text, params, seconds):
        start = perf_counter()
        with self.conn.cursor() as cur:
            cur.execute(text, params)
            rows = cur.fetchall()
        return perf_counter() - start, rows


class NeoRunner:
    def __init__(self):
        self.session = m.neo().session(database="neo4j")   # one persistent driver and session

    def set_timeout(self, seconds):
        pass

    def run(self, text, params, seconds):
        start = perf_counter()
        tx = self.session.begin_transaction(timeout=seconds)
        try:
            rows = [r.values() for r in tx.run(text, params)]
            elapsed = perf_counter() - start
        finally:
            try:
                tx.close()
            except Exception:
                pass
        return elapsed, rows


def classify(exc):
    text = f"{type(exc).__name__} {exc}".lower()
    if any(w in text for w in ("querycanceled", "timeout", "timed out", "terminated")):
        return "TIMEOUT"
    return "ERROR"


def digest(rows):
    return hashlib.md5(repr(m.norm_rows(rows)).encode()).hexdigest()


done = set()
if os.path.exists(OUT):
    for line in open(OUT):
        rec = json.loads(line)
        if rec["phase"] == "case_done":
            done.add(rec["case"])

runner = PgRunner() if engine == "pg" else NeoRunner()
log = open(OUT, "a", buffering=1)
print(f"Engine: {engine} | warm-ups {WARMUPS} ({WARM_TIMEOUT}s) | runs {RUNS} ({RUN_TIMEOUT}s) | "
      f"output {OUT}", flush=True)

for case, question, set_name, extra in build_cases():
    if case in done:
        print(f"{case:<14} already finished, skipped", flush=True)
        continue
    text, params = query_for(question, set_name, extra)
    aborted = None
    for phase, count, limit in (("warmup", WARMUPS, WARM_TIMEOUT), ("measured", RUNS, RUN_TIMEOUT)):
        if aborted:
            break
        runner.set_timeout(limit)
        for i in range(1, count + 1):
            rec = {"case": case, "question": question, "engine": engine,
                   "params": {k: v for k, v in params.items()}, "phase": phase, "run": i,
                   "start_cat": datetime.now(m.CAT).strftime("%Y-%m-%d %H:%M:%S")}
            try:
                seconds, rows = runner.run(text, params, limit)       # timed inside run()
                rec.update(status="OK", seconds=round(seconds, 4), rows=len(rows),
                           digest=digest(rows))                       # compared outside the timer
            except Exception as exc:
                rec.update(status=classify(exc), seconds=None, rows=None, digest=None,
                           error=str(exc)[:200])
            log.write(json.dumps(rec) + "\n")
            log.flush()
            shown = f"{rec['seconds']:.3f} s, {rec['rows']} rows" if rec["status"] == "OK" else rec["status"]
            print(f"{case:<14} {phase:<8} {i}/{count}  {shown}", flush=True)
            if rec["status"] != "OK":
                aborted = f"{rec['status']}-{phase}"
                break
    log.write(json.dumps({"case": case, "phase": "case_done", "status": aborted or "OK"}) + "\n")
    log.flush()

print("All cases finished for engine", engine, flush=True)
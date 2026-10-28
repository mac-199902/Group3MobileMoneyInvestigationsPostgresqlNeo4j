"""q7_v2.py - improved Q7 SQL (search from both ends). Original SQL_Q7 stays in queries.py.

python q7_v2.py check     recheck all 12 cases against the stored original + Neo4j lengths
python q7_v2.py time      time B and E at bounds 4 and 6 (PostgreSQL only, Neo4j stopped)
python q7_v2.py plan      EXPLAIN (ANALYZE, BUFFERS) for set B bound 6, with the old plan beside it
python q7_v2.py summary   before/after medians and the version selected for Section 7
"""
import hashlib
import json
import os
import sys
from datetime import datetime
from statistics import median
from time import perf_counter

import mm_common as m

RES = r"D:\MobileMoneyProject\results"
SQL_Q7_V2 = """
WITH RECURSIVE fwd(account_id, depth) AS (
    SELECT account_id, 0 FROM accounts WHERE account_id = %(src)s AND role = 'person'
  UNION
    SELECT r.account_id, w.depth + 1
    FROM fwd w
    CROSS JOIN LATERAL (SELECT DISTINCT receiver_id FROM transfers
                        WHERE sender_id = w.account_id) n
    JOIN accounts r ON r.account_id = n.receiver_id AND r.role = 'person'
    WHERE w.depth < %(fwd)s
), bwd(account_id, depth) AS (
    SELECT account_id, 0 FROM accounts WHERE account_id = %(dst)s AND role = 'person'
  UNION
    SELECT r.account_id, w.depth + 1
    FROM bwd w
    CROSS JOIN LATERAL (SELECT DISTINCT sender_id FROM transfers
                        WHERE receiver_id = w.account_id) n
    JOIN accounts r ON r.account_id = n.sender_id AND r.role = 'person'
    WHERE w.depth < %(bwd)s
)
SELECT MIN(f.depth + b.depth)
FROM (SELECT account_id, MIN(depth) AS depth FROM fwd GROUP BY account_id) f
JOIN (SELECT account_id, MIN(depth) AS depth FROM bwd GROUP BY account_id) b USING (account_id)
WHERE f.depth + b.depth > 0
"""


def params(src, dst, bound):
    return {"src": src, "dst": dst, "fwd": (bound + 1) // 2, "bwd": bound // 2}


def check():
    store = json.load(open(rf"{RES}\q7_results.json"))
    print(f"{'bound':>5} {'set':<4}{'V2 len':>8}{'orig PG':>9}{'Neo4j':>7}  status   seconds")
    ok = True
    for key in sorted(store, key=lambda k: (store[k]["bound"], store[k]["set"])):
        v = store[key]
        t0 = perf_counter()
        got = m.run_pg(SQL_Q7_V2, params(v["source"], v["dest"], v["bound"]))[0][0]
        sec = perf_counter() - t0
        same = got == v["pg_length"] == v["neo_length"]
        ok &= same
        fmt = lambda x: "none" if x is None else x
        print(f"{v['bound']:>5} {v['set']:<4}{fmt(got):>8}{fmt(v['pg_length']):>9}"
              f"{fmt(v['neo_length']):>7}  {'MATCH' if same else 'MISMATCH':<8} {sec:>6.2f}")
    print(f"All 12 cases match the original SQL and Neo4j: {ok}")


def time_cases():
    out = rf"{RES}\timing_pg_v2.jsonl"
    done = set()
    if os.path.exists(out):
        done = {json.loads(l)["case"] for l in open(out) if json.loads(l)["phase"] == "case_done"}
    log = open(out, "a", buffering=1)
    conn = m.pg()
    for s in ("B", "E"):
        for bound in (4, 6):
            case = f"Q7-{s}-b{bound}"
            if case in done:
                print(case, "already finished, skipped")
                continue
            src, dst, _ = m.SETS[s]
            p = params(src, dst, bound)
            aborted = None
            for phase, count, limit in (("warmup", 3, 180), ("measured", 5, 60)):
                if aborted:
                    break
                with conn.cursor() as cur:
                    cur.execute(f"SET statement_timeout = '{limit}s'")
                for i in range(1, count + 1):
                    rec = {"case": case, "engine": "pg_v2", "phase": phase, "run": i,
                           "start_cat": datetime.now(m.CAT).strftime("%Y-%m-%d %H:%M:%S")}
                    try:
                        t0 = perf_counter()
                        with conn.cursor() as cur:
                            cur.execute(SQL_Q7_V2, p)
                            rows = cur.fetchall()
                        sec = perf_counter() - t0
                        rec.update(status="OK", seconds=round(sec, 4), rows=len(rows),
                                   digest=hashlib.md5(repr(m.norm_rows(rows)).encode()).hexdigest())
                    except Exception as exc:
                        rec.update(status="TIMEOUT" if "cancel" in str(exc).lower() else "ERROR",
                                   seconds=None, rows=None, digest=None, error=str(exc)[:200])
                    log.write(json.dumps(rec) + "\n")
                    print(f"{case:<10} {phase:<8} {i}/{count}  "
                          f"{rec['seconds'] if rec['status'] == 'OK' else rec['status']}")
                    if rec["status"] != "OK":
                        aborted = rec["status"]
                        break
            log.write(json.dumps({"case": case, "phase": "case_done", "status": aborted or "OK"}) + "\n")
    print("All four revised cases finished")


def plan():
    src, dst, _ = m.SETS["B"]
    with m.pg().cursor() as cur:
        cur.execute("EXPLAIN (ANALYZE, BUFFERS) " + SQL_Q7_V2, params(src, dst, 6))
        lines = [r[0] for r in cur.fetchall()]
    open(r"D:\MobileMoneyProject\plans\pg_plan_q7_v2.txt", "w", encoding="utf-8").write("\n".join(lines))
    old = open(r"D:\MobileMoneyProject\plans\pg_plans.txt", encoding="utf-8").read()
    old = old[old.index("===== Q7 set B bound 6"):].splitlines()
    keys = ("Recursive Union", "WorkTable", "HashAggregate", "Index Only Scan", "Index Scan",
            "Execution Time", "Planning Time")
    print("===== BEFORE: original Q7 set B bound 6 =====")
    print("\n".join(l[:140] for l in old if any(k in l for k in keys)))
    print(f"top-level Buffers: {old[2].strip()[:60]}")
    print("\n===== AFTER: both-ends Q7 set B bound 6 =====")
    print("\n".join(l[:140] for l in lines if any(k in l for k in keys)))
    print("top-level Buffers:", next(l.strip() for l in lines if "Buffers" in l)[:60])


def load(path):
    cases = {}
    for line in open(path):
        r = json.loads(line)
        c = cases.setdefault(r["case"], {"ms": [], "status": "OK"})
        if r["phase"] == "case_done":
            c["status"] = r["status"]
        elif r["phase"] == "measured" and r["status"] == "OK":
            c["ms"].append(r["seconds"] * 1000)
    return cases


def summary():
    old, new = load(rf"{RES}\timing_pg.jsonl"), load(rf"{RES}\timing_pg_v2.jsonl")
    print(f"{'case':<10}{'original ms':>13}{'both-ends ms':>14}{'speed-up':>10}")
    meds = {}
    for case in ("Q7-B-b4", "Q7-B-b6", "Q7-E-b4", "Q7-E-b6"):
        o, n = median(old[case]["ms"]), median(new[case]["ms"])
        meds[case] = (o, n)
        print(f"{case:<10}{o:>13.1f}{n:>14.1f}{o / n:>9.1f}x")
    chosen = "both-ends (V2)" if meds["Q7-B-b6"][1] < meds["Q7-B-b6"][0] else "original"
    print(f"Selected for Section 7 (by B bound-6 median, after the 12-case check): {chosen}")
    open(rf"{RES}\q7_selected.txt", "w").write(chosen)


if __name__ == "__main__":
    {"check": check, "time": time_cases, "plan": plan, "summary": summary}[sys.argv[1]]()
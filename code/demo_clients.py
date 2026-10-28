"""demo_clients.py - start 16 light client processes for 25 s so the process list can be captured.
Writes nothing to the results folder."""
import sys

for _name in ("numpy", "pandas", "pyarrow"):
    sys.modules[_name] = None

import multiprocessing as mp
import os
import time


def worker(n):
    import psycopg
    conn = psycopg.connect(host="localhost", dbname="mobile_money", user="postgres",
                           password=os.environ["PG_PASSWORD"], autocommit=True)
    end = time.time() + 25
    while time.time() < end:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM transfers WHERE sender_id = %s", (998 + n,))
            cur.fetchall()


if __name__ == "__main__":
    ctx = mp.get_context("spawn")
    procs = [ctx.Process(target=worker, args=(i,)) for i in range(16)]
    for p in procs:
        p.start()
    print("16 client processes started; capture the process list now", flush=True)
    for p in procs:
        p.join()
    print("done")
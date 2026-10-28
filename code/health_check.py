"""health_check.py - confirm both databases are up and hold the expected data."""
import os

import psycopg
from neo4j import GraphDatabase

pg = psycopg.connect(host="localhost", dbname="mobile_money", user="postgres",
                     password=os.environ["PG_PASSWORD"])
cur = pg.cursor()
cur.execute("SELECT (SELECT count(*) FROM customers), (SELECT count(*) FROM accounts), "
            "(SELECT count(*) FROM devices), (SELECT count(*) FROM account_devices), "
            "(SELECT count(*) FROM transfers)")
got = cur.fetchone()
want = (228000, 248000, 228600, 285600, 20003300)
print("PostgreSQL tables:", got, "OK" if got == want else f"MISMATCH, expected {want}")

drv = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.environ["NEO_PASSWORD"]))
with drv.session(database="neo4j") as s:
    nodes = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
    rels = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
print("Neo4j nodes:", nodes, "OK" if nodes == 704600 else "MISMATCH, expected 704600")
print("Neo4j relationships:", rels, "OK" if rels == 20536900 else "MISMATCH, expected 20536900")
import os
import psycopg
import neo4j as neo4j_pkg
from neo4j import GraphDatabase

# PostgreSQL
with psycopg.connect(host="localhost", dbname="mobile_money", user="postgres",
                     password=os.environ["PG_PASSWORD"]) as pg:
    cur = pg.cursor()
    cur.execute("SELECT current_database(), current_setting('TimeZone'), "
                "split_part(version(), ',', 1)")
    db, tz, ver = cur.fetchone()
    print("PostgreSQL connected:", ver)
    print("  database:", db, "| time zone:", tz, "| psycopg", psycopg.__version__)

# Neo4j
drv = GraphDatabase.driver("bolt://localhost:7687",
                           auth=("neo4j", os.environ["NEO_PASSWORD"]))
drv.verify_connectivity()
with drv.session(database="neo4j") as s:
    rec = s.run("CALL dbms.components() YIELD name, versions, edition "
                "WHERE name = 'Neo4j Kernel' "
                "RETURN name, versions[0] AS version, edition").single()
    print("Neo4j connected:", rec["name"], rec["version"], rec["edition"])
    print("  database: neo4j | driver", neo4j_pkg.__version__)
drv.close()
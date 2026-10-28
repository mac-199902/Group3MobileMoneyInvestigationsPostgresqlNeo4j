"""mm_common.py - shared helpers: review sets, CAT time windows, run_pg, run_neo."""
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import psycopg
from neo4j import GraphDatabase

CAT = timezone(timedelta(hours=2))  # Africa/Kigali is UTC+02:00 all year

# set: (review account, destination, September date)
SETS = {
    "A": (998, 24755, 6),
    "B": (147228, 186823, 13),
    "C": (206978, 6573, 8),
    "D": (237998, 21755, 6),
    "E": (144228, 183823, 13),
    "F": (203978, 3573, 8),
}


def hour_window(day):
    """09:45:00 inclusive to 10:45:00 exclusive CAT on the given September day."""
    start = datetime(2026, 9, day, 9, 45, 0, tzinfo=CAT)
    end = datetime(2026, 9, day, 10, 45, 0, tzinfo=CAT)
    return int(start.timestamp()), int(end.timestamp())


def cat_text(epoch):
    return datetime.fromtimestamp(epoch, CAT).strftime("%Y-%m-%d %H:%M:%S")


_pg = None
_neo = None


def pg():
    global _pg
    if _pg is None or _pg.closed:
        _pg = psycopg.connect(host="localhost", dbname="mobile_money", user="postgres",
                              password=os.environ["PG_PASSWORD"], autocommit=True)
    return _pg


def neo():
    global _neo
    if _neo is None:
        _neo = GraphDatabase.driver("bolt://localhost:7687",
                                    auth=("neo4j", os.environ["NEO_PASSWORD"]))
    return _neo


def _norm_value(v):
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, (list, tuple)):
        return tuple(_norm_value(x) for x in v)
    return v


def _sort_key(row):
    return [(v is None, v if v is not None else 0) for v in row]


def norm_rows(rows):
    return sorted((tuple(_norm_value(v) for v in r) for r in rows), key=_sort_key)


def run_pg(query, params):
    with pg().cursor() as cur:
        cur.execute(query, params)
        return norm_rows(cur.fetchall())


def run_neo(query, params):
    with neo().session(database="neo4j") as session:
        result = session.run(query, params)
        return norm_rows([record.values() for record in result])
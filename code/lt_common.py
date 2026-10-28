"""lt_common.py - dependency-light helpers for the load-test client processes."""
import hashlib

SETS = {"A": (998, 24755, 6), "B": (147228, 186823, 13), "C": (206978, 6573, 8)}

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


def q7_params(src, dst, bound):
    return {"src": src, "dst": dst, "fwd": (bound + 1) // 2, "bwd": bound // 2}


def norm(v):
    if isinstance(v, (list, tuple)):
        return tuple(norm(x) for x in v)
    try:
        if v == int(v):
            return int(v)
    except (TypeError, ValueError):
        pass
    return v


def digest(rows):
    key = lambda row: [(v is None, v if v is not None else 0) for v in row]
    rows = sorted((tuple(norm(v) for v in r) for r in rows), key=key)
    return hashlib.md5(repr(rows).encode()).hexdigest()
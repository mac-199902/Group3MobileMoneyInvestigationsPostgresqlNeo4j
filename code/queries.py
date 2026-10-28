"""queries.py - the SQL/Cypher pairs for Q1 to Q7 in one place (parameterised)."""

SQL_Q1 = """
SELECT COUNT(*), COALESCE(SUM(amount_rwf), 0)
FROM transfers
WHERE sender_id = %(account)s
  AND occurred_at >= %(start)s AND occurred_at < %(end)s
"""
CYPHER_Q1 = """
MATCH (a:Account {account_id: $account})-[t:TRANSFER]->()
WHERE t.occurred_at >= $start AND t.occurred_at < $end
RETURN count(t) AS outgoing_count, coalesce(sum(t.amount_rwf), 0) AS total_rwf
"""

SQL_Q2 = """
SELECT to_char(to_timestamp(occurred_at) AT TIME ZONE 'Africa/Kigali', 'YYYY-MM-DD') AS day,
       COUNT(*) AS transfers, SUM(amount_rwf)::bigint AS total_rwf
FROM transfers
GROUP BY 1
ORDER BY 1
"""
CYPHER_Q2 = """
MATCH ()-[t:TRANSFER]->()
WITH datetime({epochSeconds: t.occurred_at, timezone: 'Africa/Kigali'}) AS dt, t
WITH toString(date(dt)) AS day, t
RETURN day, count(t) AS transfers, sum(t.amount_rwf) AS total_rwf
ORDER BY day
"""

SQL_Q3 = """
SELECT b.account_id, b.device_id, d.access_type,
       GREATEST(a.first_day, b.first_day) AS overlap_start,
       LEAST(a.last_day, b.last_day) AS overlap_end
FROM account_devices a
JOIN account_devices b ON b.device_id = a.device_id AND b.account_id <> a.account_id
JOIN devices d ON d.device_id = a.device_id
WHERE a.account_id = %(account)s
  AND GREATEST(a.first_day, b.first_day) <= LEAST(a.last_day, b.last_day)
ORDER BY b.account_id, b.device_id
"""
CYPHER_Q3 = """
MATCH (a:Account {account_id: $account})-[u1:USED_DEVICE]->(d:Device)<-[u2:USED_DEVICE]-(b:Account)
WHERE b <> a
WITH b, d, u1, u2,
     CASE WHEN u1.first_day > u2.first_day THEN u1.first_day ELSE u2.first_day END AS overlap_start,
     CASE WHEN u1.last_day < u2.last_day THEN u1.last_day ELSE u2.last_day END AS overlap_end
WHERE overlap_start <= overlap_end
RETURN b.account_id AS other_account, d.device_id AS device_id, d.access_type AS access_type,
       overlap_start, overlap_end
ORDER BY other_account, device_id
"""

SQL_Q4 = """
WITH RECURSIVE edges(sk, si, dk, di) AS (
    SELECT 'Customer', customer_id, 'Account', account_id FROM accounts
    UNION ALL
    SELECT 'Account', account_id, 'Customer', customer_id FROM accounts
    UNION ALL
    SELECT 'Account', account_id, 'Device', device_id FROM account_devices
    UNION ALL
    SELECT 'Device', device_id, 'Account', account_id FROM account_devices
), walk(kind, id, depth) AS (
    SELECT 'Account', %(account)s::integer, 0
    UNION
    SELECT e.dk, e.di, w.depth + 1
    FROM walk w JOIN edges e ON e.sk = w.kind AND e.si = w.id
    WHERE w.depth < %(depth)s
)
SELECT c.region, COUNT(*) AS accounts
FROM (SELECT DISTINCT id FROM walk WHERE kind = 'Account' AND id <> %(account)s) r
JOIN accounts a ON a.account_id = r.id
JOIN customers c ON c.customer_id = a.customer_id
GROUP BY c.region
ORDER BY c.region
"""
CYPHER_Q4 = """
MATCH (a:Account {account_id: $account})
MATCH (a)-[:OWNS|USED_DEVICE*1..DEPTH]-(b:Account)
WHERE b <> a
WITH DISTINCT b
MATCH (c:Customer)-[:OWNS]->(b)
RETURN c.region AS region, count(b) AS accounts
ORDER BY region
"""

SQL_Q5 = """
SELECT t1.transfer_id, t2.transfer_id, t3.transfer_id, t3.receiver_id
FROM transfers t1
JOIN transfers t2 ON t2.sender_id = t1.receiver_id
JOIN transfers t3 ON t3.sender_id = t2.receiver_id
WHERE t1.sender_id = %(account)s
  AND t1.occurred_at >= %(start)s AND t1.occurred_at < %(end)s
  AND t2.occurred_at > t1.occurred_at AND t2.occurred_at <= t1.occurred_at + 600
  AND t3.occurred_at > t2.occurred_at AND t3.occurred_at <= t2.occurred_at + 600
  AND 90::bigint * t1.amount_rwf <= 100::bigint * t2.amount_rwf
  AND 100::bigint * t2.amount_rwf <= 105::bigint * t1.amount_rwf
  AND 90::bigint * t2.amount_rwf <= 100::bigint * t3.amount_rwf
  AND 100::bigint * t3.amount_rwf <= 105::bigint * t2.amount_rwf
  AND t1.sender_id <> t1.receiver_id AND t1.sender_id <> t2.receiver_id
  AND t1.sender_id <> t3.receiver_id AND t1.receiver_id <> t2.receiver_id
  AND t1.receiver_id <> t3.receiver_id AND t2.receiver_id <> t3.receiver_id
ORDER BY t1.transfer_id, t2.transfer_id, t3.transfer_id
"""
CYPHER_Q5 = """
MATCH (a:Account {account_id: $account})-[t1:TRANSFER]->(b:Account)
      -[t2:TRANSFER]->(c:Account)-[t3:TRANSFER]->(d:Account)
WHERE t1.occurred_at >= $start AND t1.occurred_at < $end
  AND t2.occurred_at > t1.occurred_at AND t2.occurred_at <= t1.occurred_at + 600
  AND t3.occurred_at > t2.occurred_at AND t3.occurred_at <= t2.occurred_at + 600
  AND 90 * t1.amount_rwf <= 100 * t2.amount_rwf AND 100 * t2.amount_rwf <= 105 * t1.amount_rwf
  AND 90 * t2.amount_rwf <= 100 * t3.amount_rwf AND 100 * t3.amount_rwf <= 105 * t2.amount_rwf
  AND a <> b AND a <> c AND a <> d AND b <> c AND b <> d AND c <> d
RETURN t1.transfer_id AS t1_id, t2.transfer_id AS t2_id, t3.transfer_id AS t3_id,
       d.account_id AS final_receiver
ORDER BY t1_id, t2_id, t3_id
"""

SQL_Q6 = """
WITH RECURSIVE walk(current_account, ids, first_time, last_time, last_amount, len) AS (
    SELECT receiver_id, ARRAY[transfer_id], occurred_at, occurred_at, amount_rwf, 1
    FROM transfers
    WHERE sender_id = %(account)s
      AND occurred_at >= %(start)s AND occurred_at < %(end)s
  UNION ALL
    SELECT t.receiver_id, w.ids || t.transfer_id, w.first_time, t.occurred_at,
           t.amount_rwf, w.len + 1
    FROM walk w
    JOIN transfers t ON t.sender_id = w.current_account
    WHERE w.current_account <> %(account)s
      AND w.len < 8
      AND t.occurred_at > w.last_time
      AND t.occurred_at >= %(start)s AND t.occurred_at < %(end)s
      AND t.occurred_at - w.first_time <= 1800
      AND 90::bigint * w.last_amount <= 100::bigint * t.amount_rwf
      AND 100::bigint * t.amount_rwf <= 105::bigint * w.last_amount
)
SELECT ids, len FROM walk
WHERE current_account = %(account)s AND len BETWEEN 3 AND 8
ORDER BY ids
"""
CYPHER_Q6 = """
MATCH p = (a:Account {account_id: $account})-[ts:TRANSFER*3..8]->(a)
WHERE all(r IN ts WHERE r.occurred_at >= $start AND r.occurred_at < $end)
  AND none(n IN nodes(p)[1..-1] WHERE n = a)
  AND all(i IN range(0, size(ts) - 2) WHERE ts[i].occurred_at < ts[i + 1].occurred_at)
  AND ts[size(ts) - 1].occurred_at - ts[0].occurred_at <= 1800
  AND all(i IN range(0, size(ts) - 2) WHERE
          90 * ts[i].amount_rwf <= 100 * ts[i + 1].amount_rwf
          AND 100 * ts[i + 1].amount_rwf <= 105 * ts[i].amount_rwf)
RETURN [r IN ts | r.transfer_id] AS ids, size(ts) AS len
ORDER BY ids
"""

SQL_Q7 = """
WITH RECURSIVE walk(account_id, depth) AS (
    SELECT account_id, 0 FROM accounts
    WHERE account_id = %(src)s AND role = 'person'
  UNION
    SELECT r.account_id, w.depth + 1
    FROM walk w
    CROSS JOIN LATERAL (SELECT DISTINCT receiver_id FROM transfers
                        WHERE sender_id = w.account_id) n
    JOIN accounts r ON r.account_id = n.receiver_id AND r.role = 'person'
    WHERE w.depth < %(bound)s
)
SELECT MIN(depth) FROM walk WHERE account_id = %(dst)s AND depth > 0
"""
CYPHER_Q7 = """
CYPHER 25
OPTIONAL MATCH p = SHORTEST 1
  (a:Account {account_id: $src, role: 'person'})
  (()-[:TRANSFER]->(:Account {role: 'person'})){1,BOUND}
  (b:Account {account_id: $dst, role: 'person'})
RETURN length(p) AS links
"""
MATCH (c:Customer)-[:OWNS]->(a:Account {account_id: 998})-[u:USED_DEVICE]->(d:Device)
MATCH (a)-[t:TRANSFER]->(:Account)
WITH c, a, u, d, t ORDER BY t.occurred_at, t.transfer_id
WITH c, a, u, d, collect(t)[0] AS t
RETURN a.account_id AS account_id, a.role AS role,
       c.customer_id AS customer_id, c.region AS region,
       d.device_id AS device_id, d.access_type AS access_type,
       u.first_day AS first_day, u.last_day AS last_day, u.observations AS observations,
       t.transfer_id AS transfer_id, endNode(t).account_id AS receiver_id,
       t.occurred_at AS occurred_at, t.amount_rwf AS amount_rwf
ORDER BY device_id;
MATCH p = (a:Account {account_id: 998})-[:OWNS|USED_DEVICE*4]-(b:Account)
WHERE b <> a
RETURN [n IN nodes(p) | labels(n)[0] + ' ' + toString(coalesce(n.account_id, n.customer_id, n.device_id))] AS path,
       [r IN relationships(p) | type(r)] AS link_types,
       length(p) AS links
LIMIT 1;
MATCH (c:Customer) WITH count(c) AS customers
MATCH (a:Account) WITH customers, count(a) AS accounts
MATCH (d:Device) WITH customers, accounts, count(d) AS devices
RETURN customers, accounts, devices, customers + accounts + devices AS total_nodes,
       customers = 228000 AS customers_ok, accounts = 248000 AS accounts_ok,
       devices = 228600 AS devices_ok, customers + accounts + devices = 704600 AS total_ok;

MATCH ()-[o:OWNS]->() WITH count(o) AS owns
MATCH ()-[u:USED_DEVICE]->() WITH owns, count(u) AS used_device
MATCH ()-[t:TRANSFER]->() WITH owns, used_device, count(t) AS transfer
RETURN owns, used_device, transfer, owns + used_device + transfer AS total_relationships,
       owns = 248000 AS owns_ok, used_device = 285600 AS used_device_ok,
       transfer = 20003300 AS transfer_ok,
       owns + used_device + transfer = 20536900 AS total_ok;

MATCH (a:Account)
RETURN a.role AS role, count(*) AS accounts,
       CASE a.role WHEN 'person' THEN 240000 WHEN 'merchant' THEN 6000
                   WHEN 'agent' THEN 2000 END AS expected
ORDER BY role;

MATCH (a:Account)
OPTIONAL MATCH (c:Customer)-[:OWNS]->(a)
WITH a, count(c) AS owners
RETURN count(a) AS accounts,
       sum(CASE WHEN owners = 1 THEN 1 ELSE 0 END) AS with_exactly_one_owner,
       sum(CASE WHEN owners <> 1 THEN 1 ELSE 0 END) AS not_one_owner;

MATCH ()-[t:TRANSFER]->()
RETURN count(t) AS transfers, sum(t.amount_rwf) AS sum_amount_rwf,
       min(t.occurred_at) AS earliest, max(t.occurred_at) AS latest,
       count(t) = 20003300 AS count_ok,
       sum(t.amount_rwf) = 231482327870 AS sum_ok,
       min(t.occurred_at) = 1788235200 AS earliest_ok,
       max(t.occurred_at) = 1790798399 AS latest_ok;

MATCH ()-[t:TRANSFER]->()
RETURN count(t) AS transfers, count(DISTINCT t.transfer_id) AS distinct_transfer_ids,
       count(DISTINCT t.transfer_id) = count(t) AS transfer_ids_unique;
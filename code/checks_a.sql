\echo === ROW COUNTS vs CAPTURE ===
WITH c AS (
  SELECT 'customers' AS t, count(*) AS n FROM customers
  UNION ALL SELECT 'accounts', count(*) FROM accounts
  UNION ALL SELECT 'devices', count(*) FROM devices
  UNION ALL SELECT 'account_devices', count(*) FROM account_devices
  UNION ALL SELECT 'transfers', count(*) FROM transfers),
e(t, expected) AS (VALUES ('customers',228000),('accounts',248000),
  ('devices',228600),('account_devices',285600),('transfers',20003300))
SELECT c.t AS table_name, c.n AS loaded, e.expected, (c.n = e.expected) AS match
FROM c JOIN e USING (t) ORDER BY c.n;

\echo === TRANSFER AUDIT TOTALS vs capture_audit.json ===
SELECT count(*) AS transfers, sum(amount_rwf) AS sum_amount_rwf,
       min(occurred_at) AS earliest, max(occurred_at) AS latest,
       (count(*) = 20003300) AS count_match,
       (sum(amount_rwf) = 231482327870) AS sum_match,
       (min(occurred_at) = 1788235200) AS earliest_match,
       (max(occurred_at) = 1790798399) AS latest_match
FROM transfers;

\echo === ACCOUNT ROLES (expected person 240000, merchant 6000, agent 2000) ===
SELECT role, count(*) AS accounts,
       CASE role WHEN 'person' THEN 240000 WHEN 'merchant' THEN 6000
                 WHEN 'agent' THEN 2000 END AS expected
FROM accounts GROUP BY role ORDER BY role;
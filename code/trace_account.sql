SELECT a.account_id, a.role, c.customer_id, c.region,
       d.device_id, d.access_type, ad.first_day, ad.last_day, ad.observations,
       t.transfer_id, t.receiver_id, t.occurred_at,
       to_char(to_timestamp(t.occurred_at), 'YYYY-MM-DD HH24:MI:SS') AS cat_time,
       t.amount_rwf
FROM accounts a
JOIN customers c ON c.customer_id = a.customer_id
JOIN account_devices ad ON ad.account_id = a.account_id
JOIN devices d ON d.device_id = ad.device_id
JOIN LATERAL (SELECT * FROM transfers x WHERE x.sender_id = a.account_id
              ORDER BY x.occurred_at, x.transfer_id LIMIT 1) t ON true
WHERE a.account_id = 998
ORDER BY d.device_id;
\timing off
ALTER TABLE transfers DROP CONSTRAINT IF EXISTS fk_transfers_sender;
ALTER TABLE transfers DROP CONSTRAINT IF EXISTS fk_transfers_receiver;
DROP INDEX IF EXISTS ix_accounts_customer, ix_account_devices_device,
    ix_transfers_sender_time, ix_transfers_receiver_time, ix_transfers_time_brin;
\timing on
\echo === CONSTRAINT SETUP ===
ALTER TABLE transfers ADD CONSTRAINT fk_transfers_sender
    FOREIGN KEY (sender_id) REFERENCES accounts (account_id);
ALTER TABLE transfers ADD CONSTRAINT fk_transfers_receiver
    FOREIGN KEY (receiver_id) REFERENCES accounts (account_id);
\echo === INDEX SETUP ===
CREATE INDEX ix_accounts_customer ON accounts (customer_id, account_id);
CREATE INDEX ix_account_devices_device ON account_devices (device_id, account_id);
CREATE INDEX ix_transfers_sender_time ON transfers (sender_id, occurred_at)
    INCLUDE (receiver_id, amount_rwf, transfer_id);
CREATE INDEX ix_transfers_receiver_time ON transfers (receiver_id, occurred_at)
    INCLUDE (sender_id, amount_rwf, transfer_id);
CREATE INDEX ix_transfers_time_brin ON transfers USING BRIN (occurred_at);
\echo === ANALYZE ===
ANALYZE;
\echo === SETUP DONE ===
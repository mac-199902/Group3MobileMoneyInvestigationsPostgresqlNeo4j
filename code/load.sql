\timing on
\echo === LOAD PHASE ===
TRUNCATE transfers, account_devices, accounts, devices, customers;
ALTER TABLE transfers DROP CONSTRAINT IF EXISTS fk_transfers_sender;
ALTER TABLE transfers DROP CONSTRAINT IF EXISTS fk_transfers_receiver;
\copy customers FROM 'D:/MobileMoneyProject/csv/customers.csv' CSV HEADER
\copy devices FROM 'D:/MobileMoneyProject/csv/devices.csv' CSV HEADER
\copy accounts FROM 'D:/MobileMoneyProject/csv/accounts.csv' CSV HEADER
\copy account_devices FROM 'D:/MobileMoneyProject/csv/account_devices.csv' CSV HEADER
\copy transfers FROM 'D:/MobileMoneyProject/csv/transfers.csv' CSV HEADER
\echo === LOAD DONE ===
-- schema.sql : five tables for the mobile money project
-- WARNING: the DROP line is only for re-running before data is loaded.
DROP TABLE IF EXISTS transfers, account_devices, accounts, devices, customers CASCADE;

CREATE TABLE customers (
    customer_id INTEGER NOT NULL,
    region      TEXT    NOT NULL,
    CONSTRAINT pk_customers PRIMARY KEY (customer_id)
);

CREATE TABLE devices (
    device_id   INTEGER NOT NULL,
    access_type TEXT    NOT NULL,
    CONSTRAINT pk_devices PRIMARY KEY (device_id)
);

CREATE TABLE accounts (
    account_id  INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    role        TEXT    NOT NULL,
    CONSTRAINT pk_accounts PRIMARY KEY (account_id),
    CONSTRAINT fk_accounts_customer
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

CREATE TABLE account_devices (
    account_id   INTEGER  NOT NULL,
    device_id    INTEGER  NOT NULL,
    first_day    SMALLINT NOT NULL,
    last_day     SMALLINT NOT NULL,
    observations INTEGER  NOT NULL,
    CONSTRAINT pk_account_devices PRIMARY KEY (account_id, device_id),
    CONSTRAINT fk_ad_account FOREIGN KEY (account_id) REFERENCES accounts (account_id),
    CONSTRAINT fk_ad_device  FOREIGN KEY (device_id)  REFERENCES devices (device_id),
    CONSTRAINT ck_ad_observations_positive CHECK (observations > 0),
    CONSTRAINT ck_ad_day_range CHECK (0 <= first_day AND first_day <= last_day AND last_day <= 29)
);

CREATE TABLE transfers (
    transfer_id BIGINT  NOT NULL,
    sender_id   INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    occurred_at BIGINT  NOT NULL,
    amount_rwf  INTEGER NOT NULL,
    CONSTRAINT pk_transfers PRIMARY KEY (transfer_id),
    CONSTRAINT fk_transfers_sender   FOREIGN KEY (sender_id)   REFERENCES accounts (account_id),
    CONSTRAINT fk_transfers_receiver FOREIGN KEY (receiver_id) REFERENCES accounts (account_id),
    CONSTRAINT ck_transfers_amount_positive CHECK (amount_rwf > 0)
);
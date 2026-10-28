\echo === CONSTRAINTS (convalidated = t means validated) ===
SELECT conrelid::regclass AS table_name, conname, contype, convalidated
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace AND contype IN ('p','f','c')
ORDER BY conrelid::regclass::text, contype, conname;

\echo === INDEXES ===
SELECT tablename, indexname,
       substring(indexdef from 'USING (\w+)') AS method,
       pg_relation_size(format('public.%I', indexname)::regclass) AS bytes
FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname;

\echo === SIZES (1 GB = 1,000,000,000 bytes) ===
SELECT c.relname AS table_name,
       round(pg_table_size(c.oid) / 1e9, 3) AS data_gb,
       round(pg_indexes_size(c.oid) / 1e9, 3) AS index_gb
FROM pg_class c WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'r'
ORDER BY c.relname;
SELECT round(pg_database_size('mobile_money') / 1e9, 3) AS database_total_gb;
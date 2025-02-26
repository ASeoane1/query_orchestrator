SELECT
    c.conname,
    c.conrelid::regclass AS table_name,
    c.confrelid::regclass AS referenced_table,
    a.attname AS table_column,
    a2.attname AS referenced_column
FROM pg_constraint c
JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) ON true
JOIN pg_attribute a 
    ON a.attrelid = c.conrelid AND a.attnum = u.attnum
JOIN LATERAL unnest(c.confkey) WITH ORDINALITY AS u2(attnum, ord2) ON u.ord = u2.ord2
JOIN pg_attribute a2 
    ON a2.attrelid = c.confrelid AND a2.attnum = u2.attnum
WHERE c.contype = 'f'
  AND c.connamespace = (SELECT oid FROM pg_namespace WHERE nspname = '{$schema}')
  AND c.conrelid = '{$schema}.{$table}'::regclass;
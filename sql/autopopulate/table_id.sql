SELECT 
    kcu.column_name,
    CASE 
        WHEN c.column_default LIKE 'nextval(%' THEN true
        ELSE false
    END AS is_serial
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.columns AS c
  ON c.table_schema = kcu.table_schema
  AND c.table_name = kcu.table_name
  AND c.column_name = kcu.column_name
WHERE tc.constraint_type = 'PRIMARY KEY'
  AND tc.table_name = '{$table}'
  AND tc.table_schema = '{$schema}';
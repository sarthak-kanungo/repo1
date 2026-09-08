/* HRS_SPARES -> every foreign key, one row per column pair (composite keys keep their order). */
SET NOCOUNT ON;

SELECT
    fk.name                                 AS fk_name,
    cs.name                                 AS child_schema,
    ct.name                                 AS child_table,
    cc.name                                 AS child_column,
    ps.name                                 AS parent_schema,
    pt.name                                 AS parent_table,
    pc.name                                 AS parent_column,
    fkc.constraint_column_id                AS key_ordinal,
    fk.delete_referential_action_desc       AS on_delete,
    fk.update_referential_action_desc       AS on_update,
    CASE WHEN fk.is_disabled = 1 THEN 1 ELSE 0 END AS is_disabled
FROM sys.foreign_keys        AS fk
JOIN sys.foreign_key_columns AS fkc ON fkc.constraint_object_id = fk.object_id
JOIN sys.tables   AS ct ON ct.object_id  = fk.parent_object_id
JOIN sys.schemas  AS cs ON cs.schema_id  = ct.schema_id
JOIN sys.columns  AS cc ON cc.object_id  = fkc.parent_object_id
                       AND cc.column_id  = fkc.parent_column_id
JOIN sys.tables   AS pt ON pt.object_id  = fk.referenced_object_id
JOIN sys.schemas  AS ps ON ps.schema_id  = pt.schema_id
JOIN sys.columns  AS pc ON pc.object_id  = fkc.referenced_object_id
                       AND pc.column_id  = fkc.referenced_column_id
ORDER BY cs.name, ct.name, fk.name, fkc.constraint_column_id;

/* HRS_SPARES -> RELATIONAL columns only.
   A column is "relational" when it takes part in a relationship:
     - it belongs to the PRIMARY KEY,
     - or it is a FOREIGN KEY column (child side),
     - or it is referenced by a foreign key (parent side),
     - or it backs a UNIQUE constraint that a foreign key can point at.
   Plain descriptive columns (Description, Qty, Rate, CreatedOn, ...) are deliberately excluded. */
SET NOCOUNT ON;

WITH pk AS (
    SELECT ic.object_id, ic.column_id, ic.key_ordinal
    FROM sys.indexes AS i
    JOIN sys.index_columns AS ic
      ON ic.object_id = i.object_id AND ic.index_id = i.index_id
    WHERE i.is_primary_key = 1
),
uq AS (
    SELECT DISTINCT ic.object_id, ic.column_id
    FROM sys.indexes AS i
    JOIN sys.index_columns AS ic
      ON ic.object_id = i.object_id AND ic.index_id = i.index_id
    WHERE i.is_unique_constraint = 1
),
fkc AS (
    SELECT DISTINCT parent_object_id AS object_id, parent_column_id AS column_id
    FROM sys.foreign_key_columns
),
refc AS (
    SELECT DISTINCT referenced_object_id AS object_id, referenced_column_id AS column_id
    FROM sys.foreign_key_columns
)
SELECT
    s.name                                          AS schema_name,
    t.name                                          AS table_name,
    c.name                                          AS column_name,
    CASE
        WHEN ty.name IN ('varchar','char','varbinary','binary')
            THEN ty.name + '(' + CASE WHEN c.max_length = -1 THEN 'max'
                                      ELSE CAST(c.max_length AS varchar(10)) END + ')'
        WHEN ty.name IN ('nvarchar','nchar')
            THEN ty.name + '(' + CASE WHEN c.max_length = -1 THEN 'max'
                                      ELSE CAST(c.max_length / 2 AS varchar(10)) END + ')'
        WHEN ty.name IN ('decimal','numeric')
            THEN ty.name + '(' + CAST(c.precision AS varchar(10)) + ','
                               + CAST(c.scale     AS varchar(10)) + ')'
        ELSE ty.name
    END                                             AS data_type,
    CASE WHEN pk.column_id   IS NULL THEN 0 ELSE 1 END AS is_pk,
    CASE WHEN fkc.column_id  IS NULL THEN 0 ELSE 1 END AS is_fk,
    CASE WHEN refc.column_id IS NULL THEN 0 ELSE 1 END AS is_referenced,
    CASE WHEN uq.column_id   IS NULL THEN 0 ELSE 1 END AS is_unique,
    CASE WHEN c.is_nullable  = 0    THEN 0 ELSE 1 END AS is_nullable,
    ISNULL(pk.key_ordinal, 0)                       AS pk_ordinal,
    c.column_id                                     AS column_ordinal
FROM sys.tables   AS t
JOIN sys.schemas  AS s    ON s.schema_id     = t.schema_id
JOIN sys.columns  AS c    ON c.object_id     = t.object_id
JOIN sys.types    AS ty   ON ty.user_type_id = c.user_type_id
LEFT JOIN pk    ON pk.object_id   = c.object_id AND pk.column_id   = c.column_id
LEFT JOIN uq    ON uq.object_id   = c.object_id AND uq.column_id   = c.column_id
LEFT JOIN fkc   ON fkc.object_id  = c.object_id AND fkc.column_id  = c.column_id
LEFT JOIN refc  ON refc.object_id = c.object_id AND refc.column_id = c.column_id
WHERE t.is_ms_shipped = 0
  AND t.type = 'U'
  AND (pk.column_id IS NOT NULL
    OR fkc.column_id IS NOT NULL
    OR refc.column_id IS NOT NULL
    OR uq.column_id IS NOT NULL)
ORDER BY s.name, t.name,
         CASE WHEN pk.column_id IS NOT NULL THEN 0 ELSE 1 END,
         ISNULL(pk.key_ordinal, 0),
         c.column_id;

/*
    HRS_SERVICES - relational schema extract
    ----------------------------------------
    Emits one flat, pipe-delimited record set that gen_drawio.py turns into a
    draw.io ER diagram.

    Record types
      T|schema|table
      C|schema|table|column|ordinal|datatype|is_pk|is_fk|is_referenced|is_uniq|is_nullable
      R|fk_name|child_schema|child_table|child_col|parent_schema|parent_table|parent_col|col_ordinal|delete_rule|update_rule

    Only RELATIONAL columns are emitted: primary keys, foreign keys, columns on
    the referenced side of a foreign key, and unique keys. Everything else is
    deliberately left out.

    Run with:  sqlcmd ... -h -1 -W -w 65535 -i extract_schema.sql -o schema.txt
*/
SET NOCOUNT ON;

WITH pkcols AS (
    SELECT ic.object_id, ic.column_id
    FROM sys.indexes i
    JOIN sys.index_columns ic
      ON ic.object_id = i.object_id AND ic.index_id = i.index_id
    WHERE i.is_primary_key = 1
),
ukcols AS (
    SELECT ic.object_id, ic.column_id
    FROM sys.indexes i
    JOIN sys.index_columns ic
      ON ic.object_id = i.object_id AND ic.index_id = i.index_id
    WHERE i.is_unique_constraint = 1
       OR (i.is_unique = 1 AND i.is_primary_key = 0)
),
fkchild AS (
    SELECT DISTINCT parent_object_id AS object_id, parent_column_id AS column_id
    FROM sys.foreign_key_columns
),
fkparent AS (
    SELECT DISTINCT referenced_object_id AS object_id, referenced_column_id AS column_id
    FROM sys.foreign_key_columns
),
tbl AS (
    SELECT t.object_id, s.name AS sch, t.name AS tbl
    FROM sys.tables t
    JOIN sys.schemas s ON s.schema_id = t.schema_id
    WHERE t.is_ms_shipped = 0
)
SELECT line
FROM (
    /* ---- tables ---------------------------------------------------- */
    SELECT 1 AS grp,
           t.sch + N'.' + t.tbl AS k1,
           0 AS k2,
           CAST(N'T|' + t.sch + N'|' + t.tbl AS nvarchar(4000)) AS line
    FROM tbl t

    UNION ALL

    /* ---- relational columns only ------------------------------------ */
    SELECT 2,
           t.sch + N'.' + t.tbl,
           c.column_id,
           CAST(
             N'C|' + t.sch + N'|' + t.tbl + N'|' + c.name + N'|'
           + CAST(c.column_id AS nvarchar(10)) + N'|'
           + ty.name
           + CASE
               WHEN ty.name IN (N'varchar', N'char', N'varbinary', N'binary')
                    THEN N'(' + CASE WHEN c.max_length = -1 THEN N'max'
                                     ELSE CAST(c.max_length AS nvarchar(10)) END + N')'
               WHEN ty.name IN (N'nvarchar', N'nchar')
                    THEN N'(' + CASE WHEN c.max_length = -1 THEN N'max'
                                     ELSE CAST(c.max_length / 2 AS nvarchar(10)) END + N')'
               WHEN ty.name IN (N'decimal', N'numeric')
                    THEN N'(' + CAST(c.precision AS nvarchar(10)) + N','
                              + CAST(c.scale AS nvarchar(10)) + N')'
               ELSE N''
             END + N'|'
           + CASE WHEN pk.column_id IS NOT NULL THEN N'1' ELSE N'0' END + N'|'
           + CASE WHEN fc.column_id IS NOT NULL THEN N'1' ELSE N'0' END + N'|'
           + CASE WHEN fp.column_id IS NOT NULL THEN N'1' ELSE N'0' END + N'|'
           + CASE WHEN uk.column_id IS NOT NULL THEN N'1' ELSE N'0' END + N'|'
           + CASE WHEN c.is_nullable = 1        THEN N'1' ELSE N'0' END
           AS nvarchar(4000))
    FROM tbl t
    JOIN sys.columns c   ON c.object_id = t.object_id
    JOIN sys.types  ty   ON ty.user_type_id = c.user_type_id
    LEFT JOIN (SELECT DISTINCT object_id, column_id FROM pkcols) pk
           ON pk.object_id = c.object_id AND pk.column_id = c.column_id
    LEFT JOIN (SELECT DISTINCT object_id, column_id FROM ukcols) uk
           ON uk.object_id = c.object_id AND uk.column_id = c.column_id
    LEFT JOIN fkchild fc ON fc.object_id = c.object_id AND fc.column_id = c.column_id
    LEFT JOIN fkparent fp ON fp.object_id = c.object_id AND fp.column_id = c.column_id
    WHERE pk.column_id IS NOT NULL
       OR uk.column_id IS NOT NULL
       OR fc.column_id IS NOT NULL
       OR fp.column_id IS NOT NULL

    UNION ALL

    /* ---- foreign keys ------------------------------------------------ */
    SELECT 3,
           cs.name + N'.' + ct.name + N'.' + fk.name,
           fkc.constraint_column_id,
           CAST(
             N'R|' + fk.name + N'|'
           + cs.name + N'|' + ct.name + N'|' + cc.name + N'|'
           + ps.name + N'|' + pt.name + N'|' + pc.name + N'|'
           + CAST(fkc.constraint_column_id AS nvarchar(10)) + N'|'
           + fk.delete_referential_action_desc + N'|'
           + fk.update_referential_action_desc
           AS nvarchar(4000))
    FROM sys.foreign_keys fk
    JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
    JOIN sys.tables  ct ON ct.object_id  = fkc.parent_object_id
    JOIN sys.schemas cs ON cs.schema_id  = ct.schema_id
    JOIN sys.columns cc ON cc.object_id  = fkc.parent_object_id
                       AND cc.column_id  = fkc.parent_column_id
    JOIN sys.tables  pt ON pt.object_id  = fkc.referenced_object_id
    JOIN sys.schemas ps ON ps.schema_id  = pt.schema_id
    JOIN sys.columns pc ON pc.object_id  = fkc.referenced_object_id
                       AND pc.column_id  = fkc.referenced_column_id
) x
ORDER BY grp, k1, k2;

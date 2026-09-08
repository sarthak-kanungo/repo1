/* HRS_SPARES -> all base tables (so isolated tables still appear on the diagram) */
SET NOCOUNT ON;

SELECT
    s.name                                  AS schema_name,
    t.name                                  AS table_name
FROM sys.tables AS t
JOIN sys.schemas AS s ON s.schema_id = t.schema_id
WHERE t.is_ms_shipped = 0
  AND t.type = 'U'
ORDER BY s.name, t.name;

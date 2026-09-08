# HRS_SPARES relational diagram

Generates a draw.io ER diagram of the `HRS_SPARES` database showing **only
relational columns** for **all tables**, with every relationship numbered in
**dependency sequence** (parents before children).

The generator does not connect to the database itself: `sqlcmd` dumps the
metadata, the Python script turns that dump into a `.drawio` file. Both steps
run on a machine that can reach the SQL Server.

## Run it

```bash
export SQLCMDPASSWORD='<the sa/admin password>'   # keep it out of the repo
./scripts/extract.sh                              # defaults: 192.168.17.1,1433 / HRS_SPARES / admin
python3 scripts/build_drawio.py --input extract --output HRS_SPARES.drawio
```

Open `HRS_SPARES.drawio` at <https://app.diagrams.net> (File > Open) or in the
draw.io desktop app / VS Code extension.

Different server or credentials:

```bash
./scripts/extract.sh -S host,1433 -d HRS_SPARES -U admin -o extract
```

No `sqlcmd`? Install `mssql-tools18` (Linux/macOS) or the SQL Server command
line utilities (Windows), or run the three files in `sql/` from SSMS and save
each result set as a tab-separated file named `tables.tsv`, `columns.tsv`,
`foreign_keys.tsv` (no header row).

## What lands on the diagram

Every base table appears. Within each table only **relational columns** are
drawn — the ones that actually form relationships:

| Badge | Meaning |
|-------|---------|
| `PK` | primary key column |
| `FK` | foreign key column |
| `PK/FK` | key of a link / detail table |
| `UQ` | unique constraint a foreign key can target |
| `REF` | referenced by a foreign key |
| `*` after a name | column is nullable |

Descriptive columns (`Description`, `Qty`, `Rate`, `CreatedOn`, …) are left out
by design, so the shape of the schema stays readable.

## Sequence of relation

Tables are placed in columns by dependency depth: level 0 on the left holds
tables that reference nothing, each level to the right depends on the one
before it. Every relationship carries a number, ordered parent-first — which is
also a valid insert / load order.

Page 2 of the file, **Relationship Sequence**, lists the same numbering as a
table: sequence, parent (1 side), child (N side), the column pairs, and the
constraint name. Hovering an edge on page 1 shows the constraint name, the
column pairs and its `ON DELETE` / `ON UPDATE` rules.

Crow's foot notation: `ERone` at the parent, `ERmany` at the child.

## Options

| Flag | Effect |
|------|--------|
| `--schema dbo` | restrict to one schema |
| `--no-isolated` | drop tables that take part in no relationship |
| `--infer` | derive relationships from column names and types |

`--infer` matters if `HRS_SPARES` turns out to enforce integrity in the
application rather than with declared constraints. If the extract reports
`relationships: 0`, that is the case — re-run with `--infer` and the guessed
relationships are drawn as dashed amber edges, marked `[inferred]` in the
sequence list. They are guesses; confirm them before treating them as truth.

## Checking it without the database

`samples/demo_extract/` holds a small **synthetic** spares-style schema — it is
invented to exercise the generator, and is not the real `HRS_SPARES` layout:

```bash
python3 scripts/build_drawio.py --input samples/demo_extract --output samples/demo.drawio
```

## Files

| Path | Purpose |
|------|---------|
| `sql/01_tables.sql` | every base table |
| `sql/02_relational_columns.sql` | PK / FK / referenced / unique columns |
| `sql/03_foreign_keys.sql` | every FK, one row per column pair |
| `scripts/extract.sh` | runs the three queries through `sqlcmd` |
| `scripts/build_drawio.py` | builds the `.drawio` file |
| `samples/demo_extract/` | synthetic fixture |

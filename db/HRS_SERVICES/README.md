# HRS_SERVICES — relational diagram (draw.io)

Generates a draw.io ER diagram of `HRS_SERVICES` that shows **every table**, but
**only the relational columns** (primary keys, foreign keys, unique keys, and
columns on the referenced side of an FK), with the relations **numbered and laid
out in dependency sequence**.

> The database lives at `192.168.17.1,1433` — a private LAN address. It is not
> reachable from a cloud session, so the diagram has to be generated from a
> machine that can see that server. That is what `extract.sh` is for.

## Quick start

```bash
cd db/HRS_SERVICES
export HRS_PASSWORD='...'          # keeps the password out of the repo and history
./extract.sh                       # -> schema.txt -> HRS_SERVICES.drawio
```

Open `HRS_SERVICES.drawio` at <https://app.diagrams.net> (File → Open From →
Device) or with the **Draw.io Integration** extension in VS Code.

Run it by hand if you prefer:

```bash
sqlcmd -S 192.168.17.1,1433 -d HRS_SERVICES -U admin -P "$HRS_PASSWORD" \
       -C -b -h -1 -W -w 65535 -i extract_schema.sql -o schema.txt

python3 gen_drawio.py schema.txt -o HRS_SERVICES.drawio
```

`-C` trusts the server certificate (sqlcmd 18+ encrypts by default and will
otherwise fail on a self-signed cert). `-h -1 -W -w 65535` strips headers,
padding, and line wrapping so the dump parses cleanly. Nothing but Python 3
stdlib is needed for the second step — no drivers, no pip install.

## What the diagram shows

| Element | Meaning |
| --- | --- |
| `PK` / `FK` / `U` / `REF` | primary key, foreign key, unique key, referenced by an FK |
| Crow's foot ⟶ bar | many (child) to one (parent) |
| Edge number `1. FK_…` | relation sequence, in dependency order |
| Small grey edge label | the actual column pair(s), plus `ON DELETE` when not `NO_ACTION` |
| Dashed red edge | an FK that closes a cycle (drawn, but not used for levelling) |
| Left→right colour bands | FK dependency levels |

**Sequence of relation** is expressed two ways. Tables are levelled by
longest-path from the roots: level 0 holds tables with no outgoing FK (lookups
and masters), and each further level holds tables whose foreign keys reach back
into an earlier one — so reading left to right is the order you would have to
populate the database. Relations are then numbered `1..N` in that same order,
and the number is the first thing on each edge label.

Composite foreign keys become a single edge whose label lists every column pair.
Self-references (`Employee.ManagerId → Employee.EmployeeId`) and FK cycles are
handled: a depth-first pass finds the edges that close each cycle, cuts them out
of the levelling graph, and draws them dashed and red instead. Without that, a
two-table cycle alone inflates the diagram to a dozen half-empty bands.

## Files

| File | Purpose |
| --- | --- |
| `extract_schema.sql` | Reads `sys.tables` / `sys.columns` / `sys.foreign_keys` and emits a flat `T` / `C` / `R` record set. Filters to relational columns in SQL, so nothing else leaves the server. |
| `gen_drawio.py` | Parses that dump, levels and numbers the relations, writes the `.drawio` XML. Python 3 stdlib only. |
| `extract.sh` | Runs both steps. Server/db/user/output are all overridable via env vars. |
| `sample_schema.txt` | A representative HR-services schema used to exercise the generator. |
| `HRS_SERVICES.sample.drawio` | Built from that sample — open it to see the output format before running against the real database. |

## Options

```
python3 gen_drawio.py schema.txt -o out.drawio \
    -t "HRS_SERVICES — relational diagram" \
    --schema dbo --schema hr        # restrict to named schemas, repeatable
```

Pass `-` as the input to read the dump from stdin, so the two steps can be
piped together.

## Notes

- The password is never read from a file in the repo: `extract.sh` takes it from
  `HRS_PASSWORD` or prompts for it silently.
- `schema.txt` is an intermediate dump. It contains table and column names only
  — no row data — but there is no need to commit it.
- If a table has no primary key and no foreign keys it still appears, with a
  `(no relational columns)` placeholder row, so the table inventory stays complete.

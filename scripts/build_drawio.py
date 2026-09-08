#!/usr/bin/env python3
"""
Build a draw.io (diagrams.net) relational / ER diagram from HRS_SPARES metadata.

Design rules implemented here:
  * ALL base tables appear, including ones with no relationships.
  * ONLY relational columns are drawn: primary keys, foreign keys, columns
    referenced by a foreign key, and unique-constraint columns. Descriptive
    columns are left out on purpose.
  * Relationships carry a SEQUENCE number derived from the dependency order of
    the schema, so the diagram reads parent-first, left to right.

Usage:
    python3 scripts/build_drawio.py --input extract --output HRS_SPARES.drawio
    python3 scripts/build_drawio.py --input extract --infer     # also guess undeclared FKs
"""
from __future__ import annotations

import argparse
import csv
import html
import os
import sys
from collections import defaultdict

# ---------------------------------------------------------------- geometry --
HEADER_H = 30
ROW_H = 26
TABLE_W = 320
COL_KEY_W = 46
COL_TYPE_W = 96
H_GAP = 190          # horizontal gap between dependency levels
V_GAP = 40           # vertical gap between tables in the same level
MARGIN = 40

# ------------------------------------------------------------------ colours --
C_HEADER = "#1F4E79"
C_HEADER_ISO = "#6B6B6B"
C_PK = "#FFF3CD"
C_FK = "#E3F0FB"
C_BOTH = "#E6F4EA"
C_PLAIN = "#FFFFFF"
C_EDGE = "#2F5D8A"
C_EDGE_INFERRED = "#B06A00"


# ------------------------------------------------------------------ models --
class Column:
    __slots__ = ("name", "dtype", "is_pk", "is_fk", "is_ref", "is_uq",
                 "nullable", "pk_ord", "ordinal")

    def __init__(self, name, dtype, is_pk, is_fk, is_ref, is_uq, nullable,
                 pk_ord, ordinal):
        self.name, self.dtype = name, dtype
        self.is_pk, self.is_fk, self.is_ref, self.is_uq = is_pk, is_fk, is_ref, is_uq
        self.nullable, self.pk_ord, self.ordinal = nullable, pk_ord, ordinal

    @property
    def badge(self):
        tags = []
        if self.is_pk:
            tags.append("PK")
        if self.is_fk:
            tags.append("FK")
        if not tags and self.is_uq:
            tags.append("UQ")
        if not tags and self.is_ref:
            tags.append("REF")
        return "/".join(tags)

    @property
    def fill(self):
        if self.is_pk and self.is_fk:
            return C_BOTH
        if self.is_pk:
            return C_PK
        if self.is_fk:
            return C_FK
        return C_PLAIN


class Table:
    __slots__ = ("schema", "name", "columns", "level", "cell_id", "row_ids",
                 "x", "y")

    def __init__(self, schema, name):
        self.schema, self.name = schema, name
        self.columns: list[Column] = []
        self.level = 0
        self.cell_id = ""
        self.row_ids: dict[str, str] = {}
        self.x = self.y = 0

    @property
    def key(self):
        return (self.schema, self.name)

    @property
    def label(self):
        return f"{self.schema}.{self.name}"

    @property
    def height(self):
        return HEADER_H + ROW_H * max(len(self.columns), 1)


class Relation:
    __slots__ = ("name", "child", "parent", "pairs", "on_delete", "on_update",
                 "disabled", "inferred", "seq")

    def __init__(self, name, child, parent, pairs, on_delete="", on_update="",
                 disabled=False, inferred=False):
        self.name, self.child, self.parent = name, child, parent
        self.pairs = pairs                     # [(child_col, parent_col), ...]
        self.on_delete, self.on_update = on_delete, on_update
        self.disabled, self.inferred = disabled, inferred
        self.seq = 0


# ------------------------------------------------------------------- input --
def read_tsv(path, expected):
    """Read a sqlcmd -W -s\\t dump; skip blanks, separator rules and footers."""
    if not os.path.exists(path):
        sys.exit(f"ERROR: missing input file {path} (run scripts/extract.sh first)")
    out = []
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\r\n")
            if not line.strip():
                continue
            if set(line.strip()) <= {"-", "\t", " "}:          # sqlcmd rule line
                continue
            if line.lstrip().startswith("(") and "rows affected" in line:
                continue
            parts = line.split("\t")
            if len(parts) < expected:
                continue
            out.append([p.strip() for p in parts[:expected]])
    return out


def load(indir):
    tables: dict[tuple, Table] = {}

    for schema, name in read_tsv(os.path.join(indir, "tables.tsv"), 2):
        tables[(schema, name)] = Table(schema, name)

    for row in read_tsv(os.path.join(indir, "columns.tsv"), 10):
        (schema, tname, cname, dtype, is_pk, is_fk, is_ref, is_uq,
         nullable, pk_ord) = row[:10]
        t = tables.setdefault((schema, tname), Table(schema, tname))
        t.columns.append(Column(cname, dtype, is_pk == "1", is_fk == "1",
                                is_ref == "1", is_uq == "1", nullable == "1",
                                int(pk_ord or 0), len(t.columns)))

    grouped: dict[tuple, Relation] = {}
    for row in read_tsv(os.path.join(indir, "foreign_keys.tsv"), 11):
        (fk, cs, ct, cc, ps, pt, pc, _ord, on_del, on_upd, disabled) = row[:11]
        gkey = (cs, ct, fk)
        rel = grouped.get(gkey)
        if rel is None:
            rel = Relation(fk, (cs, ct), (ps, pt), [], on_del, on_upd,
                           disabled == "1")
            grouped[gkey] = rel
        rel.pairs.append((cc, pc))
        for k in ((cs, ct), (ps, pt)):
            tables.setdefault(k, Table(*k))

    return tables, list(grouped.values())


def infer_relations(tables, relations):
    """Guess undeclared relationships by column name + type, for schemas whose
    integrity is enforced in the application rather than by FK constraints."""
    declared = {(r.child, r.parent, tuple(r.pairs)) for r in relations}
    pk_index = {}
    for t in tables.values():
        pks = [c for c in t.columns if c.is_pk]
        if len(pks) == 1:
            pk_index[t.key] = pks[0]

    found = []
    for t in tables.values():
        for c in t.columns:
            if c.is_pk or c.is_fk:
                continue
            for pkey, pcol in pk_index.items():
                if pkey == t.key or pcol.dtype != c.dtype:
                    continue
                generic = pcol.name.lower() in {"id", "code", "no", "srno"}
                exact = c.name.lower() == pcol.name.lower()
                prefixed = c.name.lower() == (pkey[1] + pcol.name).lower()
                if (exact and not generic) or prefixed:
                    sig = (t.key, pkey, ((c.name, pcol.name),))
                    if sig in declared:
                        continue
                    declared.add(sig)
                    c.is_fk = True
                    found.append(Relation(f"(inferred) {t.name}.{c.name}",
                                          t.key, pkey, [(c.name, pcol.name)],
                                          inferred=True))
                    break
    return found


# ------------------------------------------------------- sequence + layout --
def assign_levels(tables, relations):
    """Longest-path depth: parents first. Cycles are relaxed, not fatal."""
    parents = defaultdict(set)
    for r in relations:
        if r.child != r.parent:
            parents[r.child].add(r.parent)

    level = {k: 0 for k in tables}
    for _ in range(len(tables) + 1):
        changed = False
        for k in tables:
            want = max((level[p] + 1 for p in parents.get(k, ()) if p in level),
                       default=0)
            if want > level[k]:
                level[k], changed = want, True
        if not changed:
            break
    for k, t in tables.items():
        t.level = level[k]
    return level


def sequence_relations(relations, tables):
    """Number every relationship in the order the schema must be populated."""
    def sort_key(r):
        p, c = tables[r.parent], tables[r.child]
        return (p.level, p.label.lower(), c.level, c.label.lower(), r.name.lower())

    for i, r in enumerate(sorted(relations, key=sort_key), start=1):
        r.seq = i
    return sorted(relations, key=lambda r: r.seq)


def layout(tables):
    by_level = defaultdict(list)
    for t in tables.values():
        by_level[t.level].append(t)

    for lvl in sorted(by_level):
        y = MARGIN
        for t in sorted(by_level[lvl], key=lambda x: x.label.lower()):
            t.x = MARGIN + lvl * (TABLE_W + H_GAP)
            t.y = y
            y += t.height + V_GAP
    return by_level


# --------------------------------------------------------------- xml output --
def esc(s):
    return html.escape(str(s), quote=True)


def geom(x=None, y=None, w=None, h=None, alt=False):
    bits = "".join(f' {k}="{v}"' for k, v in
                   (("x", x), ("y", y), ("width", w), ("height", h)) if v is not None)
    if alt:
        return (f'<mxGeometry{bits} as="geometry">'
                f'<mxRectangle width="{w}" height="{h}" as="alternateBounds"/>'
                f"</mxGeometry>")
    return f'<mxGeometry{bits} as="geometry"/>'


ROW_STYLE = ("shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;"
             "fillColor=none;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];"
             "portConstraint=eastwest;top=0;left=0;right=0;bottom=0;")


def cell_style(fill, align="left", bold=False):
    return ("shape=partialRectangle;connectable=0;overflow=hidden;html=1;"
            "whiteSpace=wrap;top=0;left=0;bottom=0;right=0;"
            f"align={align};spacingLeft=6;spacingRight=6;fillColor={fill};"
            + ("fontStyle=1;" if bold else ""))


def emit_grid(uid, title, x, y, widths, rows, header_fill=C_HEADER,
              row_ids=None, tooltip=""):
    """One draw.io table shape: a title bar plus fixed-width cells per row."""
    w = sum(widths)
    h = HEADER_H + ROW_H * max(len(rows), 1)
    tip = f' tooltip="{esc(tooltip)}"' if tooltip else ""
    out = [
        f'<mxCell id="{uid}" value="{esc(title)}"{tip} style="shape=table;startSize={HEADER_H};'
        f"container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;"
        f"columnLines=1;html=1;whiteSpace=wrap;align=center;fontStyle=1;fontColor=#FFFFFF;"
        f'fontSize=13;fillColor={header_fill};strokeColor=#0B2C4A;resizeLast=1;" '
        f'vertex="1" parent="1">{geom(x, y, w, h)}</mxCell>'
    ]
    if not rows:
        rows = [[("(no relational columns)", C_PLAIN, "left", False)]]
        widths = [w]

    for ri, cells in enumerate(rows):
        rid = f"{uid}-r{ri}"
        out.append(f'<mxCell id="{rid}" value="" style="{ROW_STYLE}" vertex="1" '
                   f'parent="{uid}">{geom(y=HEADER_H + ri * ROW_H, w=w, h=ROW_H)}</mxCell>')
        cx = 0
        for ci, cell in enumerate(cells):
            text, fill, align, bold = cell
            cw = widths[ci] if ci < len(widths) else w - cx
            out.append(
                f'<mxCell id="{rid}-c{ci}" value="{esc(text)}" '
                f'style="{cell_style(fill, align, bold)}" vertex="1" parent="{rid}">'
                f"{geom(cx if ci else None, None, cw, ROW_H, alt=True)}</mxCell>")
            cx += cw
        if row_ids is not None and ri < len(row_ids):
            row_ids[ri] = rid
    return out, h


def build_diagram(tables, relations, by_level):
    cells = []
    name_w = TABLE_W - COL_KEY_W - COL_TYPE_W

    for i, t in enumerate(sorted(tables.values(), key=lambda x: (x.level, x.label.lower()))):
        t.cell_id = f"T{i}"
        rows, ids = [], []
        for c in t.columns:
            nm = c.name + ("" if c.nullable else " *")
            rows.append([(c.badge, c.fill, "center", True),
                         (nm, c.fill, "left", c.is_pk),
                         (c.dtype, c.fill, "left", False)])
            ids.append(c.name)
        row_slots = [""] * len(rows)
        isolated = not any(c.is_pk or c.is_fk or c.is_ref for c in t.columns)
        xml, _ = emit_grid(t.cell_id, t.label, t.x, t.y,
                           [COL_KEY_W, name_w, COL_TYPE_W], rows,
                           header_fill=C_HEADER_ISO if isolated else C_HEADER,
                           row_ids=row_slots,
                           tooltip=f"dependency level {t.level}")
        cells += xml
        t.row_ids = {ids[k]: row_slots[k] for k in range(len(ids))}

    for r in relations:
        child, parent = tables[r.child], tables[r.parent]
        ccol, pcol = r.pairs[0]
        src = parent.row_ids.get(pcol, parent.cell_id)
        dst = child.row_ids.get(ccol, child.cell_id)
        cols = ", ".join(f"{c} → {p}" for c, p in r.pairs)
        label = f"{r.seq}"
        dashed = "dashed=1;" if (r.inferred or r.disabled) else ""
        stroke = C_EDGE_INFERRED if r.inferred else C_EDGE
        tip = (f"[{r.seq}] {r.name}\n{child.label} → {parent.label}\n{cols}"
               + (f"\nON DELETE {r.on_delete}" if r.on_delete else "")
               + (f"  ON UPDATE {r.on_update}" if r.on_update else "")
               + ("\nINFERRED - not a declared constraint" if r.inferred else "")
               + ("\nCONSTRAINT DISABLED" if r.disabled else ""))
        style = (f"edgeStyle=entityRelationEdgeStyle;rounded=0;html=1;fontSize=11;"
                 f"fontStyle=1;fontColor={stroke};startArrow=ERone;startFill=0;"
                 f"endArrow=ERmany;endFill=0;strokeColor={stroke};strokeWidth=1.5;"
                 f"{dashed}labelBackgroundColor=#FFFFFF;")
        cells.append(
            f'<mxCell id="E{r.seq}" value="{esc(label)}" tooltip="{esc(tip)}" '
            f'style="{style}" edge="1" parent="1" source="{src}" target="{dst}">'
            f'<mxGeometry relative="1" as="geometry"/></mxCell>')

    # legend
    lx = MARGIN
    ly = MARGIN + max((sum(t.height + V_GAP for t in v) for v in by_level.values()),
                      default=0) + 30
    legend = [
        [("PK", C_PK, "center", True), ("primary key column", C_PLAIN, "left", False)],
        [("FK", C_FK, "center", True), ("foreign key column", C_PLAIN, "left", False)],
        [("PK/FK", C_BOTH, "center", True), ("key of a link table", C_PLAIN, "left", False)],
        [("UQ", C_PLAIN, "center", True), ("unique constraint column", C_PLAIN, "left", False)],
        [("n", C_PLAIN, "center", True), ("relation sequence, parents first", C_PLAIN, "left", False)],
        [("*", C_PLAIN, "center", True), ("column is nullable", C_PLAIN, "left", False)],
        [("- -", C_PLAIN, "center", True), ("inferred / disabled constraint", C_PLAIN, "left", False)],
    ]
    xml, _ = emit_grid("LEGEND", "Legend", lx, ly, [70, 250], legend)
    return cells + xml


def build_sequence_page(tables, relations):
    rows = []
    for r in relations:
        rows.append([
            (str(r.seq), C_PLAIN, "center", True),
            (f"{tables[r.parent].label}  (1)", C_PK, "left", False),
            (f"{tables[r.child].label}  (N)", C_FK, "left", False),
            (", ".join(f"{c} → {p}" for c, p in r.pairs), C_PLAIN, "left", False),
            (r.name + (" [inferred]" if r.inferred else ""), C_PLAIN, "left", False),
        ])
    widths = [50, 230, 230, 300, 300]
    if not rows:
        return emit_grid("SEQ", "Relationship sequence - none found", MARGIN,
                         MARGIN, widths, [])[0]
    return emit_grid("SEQ", "Relationship sequence (populate parents first)",
                     MARGIN, MARGIN, widths, rows)[0]


def wrap(pages):
    out = ['<mxfile host="app.diagrams.net" type="device">']
    for i, (name, cells) in enumerate(pages):
        out.append(f'<diagram id="page{i}" name="{esc(name)}">')
        out.append('<mxGraphModel dx="1440" dy="900" grid="1" gridSize="10" guides="1" '
                   'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
                   'pageWidth="1600" pageHeight="1200" math="0" shadow="0"><root>'
                   '<mxCell id="0"/><mxCell id="1" parent="0"/>')
        out += cells
        out.append("</root></mxGraphModel></diagram>")
    out.append("</mxfile>")
    return "\n".join(out)


# -------------------------------------------------------------------- main --
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default="extract", help="dir holding the .tsv dumps")
    ap.add_argument("--output", default="HRS_SPARES.drawio")
    ap.add_argument("--schema", help="restrict to one schema, e.g. dbo")
    ap.add_argument("--infer", action="store_true",
                    help="also derive relationships from column names when the "
                         "database declares no foreign keys")
    ap.add_argument("--no-isolated", action="store_true",
                    help="drop tables that take part in no relationship")
    args = ap.parse_args()

    tables, relations = load(args.input)

    if args.schema:
        tables = {k: v for k, v in tables.items() if k[0] == args.schema}
        relations = [r for r in relations
                     if r.child in tables and r.parent in tables]

    if args.infer:
        relations += infer_relations(tables, relations)

    relations = [r for r in relations if r.child in tables and r.parent in tables]

    if args.no_isolated:
        keep = {r.child for r in relations} | {r.parent for r in relations}
        tables = {k: v for k, v in tables.items() if k in keep}

    if not tables:
        sys.exit("ERROR: no tables found in the extract - check the .tsv files.")

    assign_levels(tables, relations)
    relations = sequence_relations(relations, tables)
    by_level = layout(tables)

    pages = [("HRS_SPARES - Relational Model",
              build_diagram(tables, relations, by_level)),
             ("Relationship Sequence",
              build_sequence_page(tables, relations))]

    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(wrap(pages))

    rel_cols = sum(len(t.columns) for t in tables.values())
    inferred = sum(1 for r in relations if r.inferred)
    print(f"{args.output}")
    print(f"  tables            : {len(tables)}")
    print(f"  relational columns: {rel_cols}")
    print(f"  relationships     : {len(relations)}"
          + (f" ({inferred} inferred)" if inferred else ""))
    print(f"  dependency levels : {max(by_level) + 1 if by_level else 0}")
    if not relations:
        print("  NOTE: no foreign keys declared - re-run with --infer")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Turn an extract_schema.sql dump into a draw.io ER diagram.

Only relational columns (PK / FK / referenced / unique) are drawn, every table
is included, and the relations are laid out and numbered in dependency
sequence: level 0 holds tables nothing points away from, each following level
holds tables whose foreign keys reach back into an earlier level.

    python3 gen_drawio.py schema.txt -o HRS_SERVICES.drawio
"""

import argparse
import re
import sys
from collections import defaultdict
from xml.sax.saxutils import escape, quoteattr

# ---------------------------------------------------------------- geometry
HEADER_H = 34
ROW_H = 26
KEY_W = 40
TABLE_W = 300
COL_GAP = 190          # horizontal gap between dependency levels
ROW_GAP = 46           # vertical gap between tables in a level
MARGIN_X = 60
MARGIN_Y = 140
BAND_LABEL_H = 40

PALETTE = [
    ("#dae8fc", "#6c8ebf"),
    ("#d5e8d4", "#82b366"),
    ("#ffe6cc", "#d79b00"),
    ("#e1d5e7", "#9673a6"),
    ("#fff2cc", "#d6b656"),
    ("#f8cecc", "#b85450"),
    ("#d0f0f0", "#4d9999"),
]

# sqlcmd chrome we never want to parse
NOISE = re.compile(
    r"^\s*$|^\(\d+ rows? affected\)|^-+$|^Changed database context|^Changed language",
    re.I,
)


# ---------------------------------------------------------------- model
class Column:
    def __init__(self, name, ordinal, dtype, pk, fk, ref, uq, nullable):
        self.name = name
        self.ordinal = ordinal
        self.dtype = dtype
        self.pk = pk
        self.fk = fk
        self.ref = ref
        self.uq = uq
        self.nullable = nullable

    @property
    def badge(self):
        marks = []
        if self.pk:
            marks.append("PK")
        if self.fk:
            marks.append("FK")
        if self.uq and not self.pk:
            marks.append("U")
        if not marks and self.ref:
            marks.append("REF")
        return ",".join(marks)

    @property
    def is_relational(self):
        return self.pk or self.fk or self.ref or self.uq


class Table:
    def __init__(self, schema, name):
        self.schema = schema
        self.name = name
        self.columns = []
        self.level = 0
        self.x = 0
        self.y = 0
        self.cell_id = ""
        self.row_ids = {}

    @property
    def key(self):
        return f"{self.schema}.{self.name}"

    @property
    def height(self):
        return HEADER_H + ROW_H * max(len(self.columns), 1)


class Relation:
    """One foreign key constraint (possibly over several column pairs)."""

    def __init__(self, name, child, parent):
        self.name = name
        self.child = child          # "schema.table"
        self.parent = parent        # "schema.table"
        self.pairs = []             # [(child_col, parent_col, ordinal)]
        self.delete_rule = ""
        self.update_rule = ""
        self.seq = 0
        self.back_edge = False

    @property
    def child_col(self):
        return self.pairs[0][0] if self.pairs else ""

    @property
    def parent_col(self):
        return self.pairs[0][1] if self.pairs else ""

    @property
    def composite(self):
        return len(self.pairs) > 1


# ---------------------------------------------------------------- parsing
def parse(stream):
    tables, relations, order = {}, {}, []

    for raw in stream:
        line = raw.rstrip("\r\n").strip()
        if NOISE.match(line):
            continue
        parts = line.split("|")
        kind = parts[0].strip()

        if kind == "T" and len(parts) >= 3:
            t = Table(parts[1].strip(), parts[2].strip())
            if t.key not in tables:
                tables[t.key] = t
                order.append(t.key)

        elif kind == "C" and len(parts) >= 11:
            key = f"{parts[1].strip()}.{parts[2].strip()}"
            t = tables.get(key)
            if t is None:
                t = Table(parts[1].strip(), parts[2].strip())
                tables[key] = t
                order.append(key)
            t.columns.append(
                Column(
                    parts[3].strip(),
                    int(parts[4]) if parts[4].strip().isdigit() else len(t.columns),
                    parts[5].strip(),
                    parts[6].strip() == "1",
                    parts[7].strip() == "1",
                    parts[8].strip() == "1",
                    parts[9].strip() == "1",
                    parts[10].strip() == "1",
                )
            )

        elif kind == "R" and len(parts) >= 9:
            name = parts[1].strip()
            child = f"{parts[2].strip()}.{parts[3].strip()}"
            parent = f"{parts[5].strip()}.{parts[6].strip()}"
            rel = relations.setdefault(
                (name, child, parent), Relation(name, child, parent)
            )
            ordinal = int(parts[8]) if parts[8].strip().isdigit() else len(rel.pairs) + 1
            rel.pairs.append((parts[4].strip(), parts[7].strip(), ordinal))
            if len(parts) >= 11:
                rel.delete_rule = parts[9].strip()
                rel.update_rule = parts[10].strip()

    for t in tables.values():
        t.columns = [c for c in t.columns if c.is_relational]
        t.columns.sort(key=lambda c: (not c.pk, c.ordinal))
    for r in relations.values():
        r.pairs.sort(key=lambda p: p[2])

    # drop relations whose endpoints were never declared
    rels = [r for r in relations.values() if r.child in tables and r.parent in tables]
    return [tables[k] for k in order], rels


# ---------------------------------------------------------------- sequencing
def _back_edges(nodes, edges):
    """Depth-first back-edge detection, so an FK cycle is broken at exactly one
    edge instead of inflating the level count."""
    adj = defaultdict(list)
    for parent, child in edges:
        adj[parent].append(child)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}
    back = set()

    for start in sorted(nodes):
        if color[start] != WHITE:
            continue
        color[start] = GRAY
        stack = [(start, iter(sorted(adj[start])))]
        while stack:
            node, it = stack[-1]
            descended = False
            for nxt in it:
                if color[nxt] == GRAY:
                    back.add((node, nxt))          # edge closes a cycle
                elif color[nxt] == WHITE:
                    color[nxt] = GRAY
                    stack.append((nxt, iter(sorted(adj[nxt]))))
                    descended = True
                    break
            if not descended:
                color[node] = BLACK
                stack.pop()
    return back


def assign_levels(tables, relations):
    """Longest-path levelling over the FK graph with cycles broken first, so
    parents always sit left of the children that reference them."""
    by_key = {t.key: t for t in tables}

    # dependency edges point parent -> child; self-references never level
    edges = [
        (r.parent, r.child)
        for r in relations
        if r.child != r.parent and r.child in by_key and r.parent in by_key
    ]
    back = _back_edges(set(by_key), edges)
    for r in relations:
        r.back_edge = (r.parent, r.child) in back

    parents = defaultdict(set)
    children = defaultdict(set)
    for parent, child in edges:
        if (parent, child) in back:
            continue
        parents[child].add(parent)
        children[parent].add(child)

    # Kahn topological order over the acyclic remainder
    indeg = {k: len(parents[k]) for k in by_key}
    queue = sorted(k for k in by_key if indeg[k] == 0)
    level = {k: 0 for k in by_key}
    seen = 0
    while queue:
        node = queue.pop(0)
        seen += 1
        for child in sorted(children[node]):
            level[child] = max(level[child], level[node] + 1)
            indeg[child] -= 1
            if indeg[child] == 0:
                queue.append(child)
        queue.sort()

    if seen != len(by_key):  # defensive: should not happen once cycles are cut
        for _ in range(len(by_key)):
            for k in by_key:
                want = max((level[p] + 1 for p in parents[k]), default=0)
                level[k] = max(level[k], want)

    for k, t in by_key.items():
        t.level = level[k]
    return max(level.values(), default=0)


def sequence_relations(relations, tables):
    """Number the relations in the order the levels imply: a relation is
    numbered once both of its endpoints exist, parents first."""
    lv = {t.key: t.level for t in tables}
    ordered = sorted(
        relations,
        key=lambda r: (lv.get(r.child, 0), r.child, lv.get(r.parent, 0), r.parent, r.name),
    )
    for i, r in enumerate(ordered, 1):
        r.seq = i
    return ordered


def layout(tables, max_level):
    """Place tables in one vertical band per dependency level."""
    bands = defaultdict(list)
    for t in tables:
        bands[t.level].append(t)

    x = MARGIN_X
    band_x = {}
    for lvl in range(max_level + 1):
        group = sorted(bands[lvl], key=lambda t: t.key)
        band_x[lvl] = x
        y = MARGIN_Y
        for t in group:
            t.x, t.y = x, y
            y += t.height + ROW_GAP
        x += TABLE_W + COL_GAP
    return band_x, bands


# ---------------------------------------------------------------- rendering
def esc(s):
    return escape(str(s))


def attr(s):
    return quoteattr(str(s))


TABLE_STYLE = (
    "shape=table;startSize={hdr};container=1;collapsible=0;childLayout=tableLayout;"
    "fixedRows=1;rowLines=1;fontStyle=1;align=center;resizeLast=1;html=1;"
    "fillColor={fill};strokeColor={stroke};swimlaneFillColor=#ffffff;"
    "verticalAlign=middle;fontSize=13;"
)
ROW_STYLE = (
    "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;"
    "fillColor=none;collapsible=0;dropTarget=0;points=[[0,0.5,0,0,0],[1,0.5,0,0,0]];"
    "portConstraint=eastwest;top=0;left=0;right=0;bottom=0;html=1;"
)
CELL_STYLE = (
    "shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;"
    "right=0;overflow=hidden;html=1;fontSize=11;{extra}"
)


def render(tables, relations, band_x, bands, max_level, title):
    out = []
    add = out.append

    add('<mxfile host="app.diagrams.net" type="device">')
    add(f'  <diagram id="hrs-services-er" name={attr(title)}>')
    add(
        '    <mxGraphModel dx="1420" dy="820" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        'pageWidth="1600" pageHeight="1200" math="0" shadow="0">'
    )
    add("      <root>")
    add('        <mxCell id="0" />')
    add('        <mxCell id="1" parent="0" />')

    # ---- diagram title
    add(
        f'        <mxCell id="title" value={attr(title)} '
        'style="text;html=1;fontSize=22;fontStyle=1;align=left;verticalAlign=middle;" '
        'vertex="1" parent="1">'
    )
    add(f'          <mxGeometry x="{MARGIN_X}" y="24" width="900" height="34" as="geometry" />')
    add("        </mxCell>")

    # ---- dependency-level band headers
    for lvl in range(max_level + 1):
        if not bands[lvl]:
            continue
        label = (
            f"Level {lvl} — referenced only (no outgoing FK)"
            if lvl == 0
            else f"Level {lvl} — depends on level {lvl - 1}"
        )
        add(
            f'        <mxCell id="band{lvl}" value={attr(label)} '
            'style="text;html=1;fontSize=13;fontStyle=1;align=center;verticalAlign=middle;'
            'fillColor=#f5f5f5;strokeColor=#b3b3b3;rounded=1;" vertex="1" parent="1">'
        )
        add(
            f'          <mxGeometry x="{band_x[lvl]}" y="{MARGIN_Y - BAND_LABEL_H - 14}" '
            f'width="{TABLE_W}" height="{BAND_LABEL_H}" as="geometry" />'
        )
        add("        </mxCell>")

    # ---- tables
    for i, t in enumerate(tables):
        fill, stroke = PALETTE[t.level % len(PALETTE)]
        t.cell_id = f"t{i}"
        style = TABLE_STYLE.format(hdr=HEADER_H, fill=fill, stroke=stroke)
        add(
            f'        <mxCell id="{t.cell_id}" value={attr(t.key)} '
            f'style={attr(style)} vertex="1" parent="1">'
        )
        add(
            f'          <mxGeometry x="{t.x}" y="{t.y}" width="{TABLE_W}" '
            f'height="{t.height}" as="geometry" />'
        )
        add("        </mxCell>")

        if not t.columns:
            rid = f"{t.cell_id}r0"
            add(
                f'        <mxCell id="{rid}" value="" style={attr(ROW_STYLE)} '
                f'vertex="1" parent="{t.cell_id}">'
            )
            add(
                f'          <mxGeometry y="{HEADER_H}" width="{TABLE_W}" '
                f'height="{ROW_H}" as="geometry" />'
            )
            add("        </mxCell>")
            _cell(add, f"{rid}c0", rid, "", 0, KEY_W, "align=center;fontStyle=1;")
            _cell(
                add, f"{rid}c1", rid, "(no relational columns)", KEY_W,
                TABLE_W - KEY_W, "align=left;spacingLeft=6;fontStyle=2;fontColor=#999999;",
            )
            continue

        for j, c in enumerate(t.columns):
            rid = f"{t.cell_id}r{j}"
            t.row_ids[c.name] = rid
            add(
                f'        <mxCell id="{rid}" value="" style={attr(ROW_STYLE)} '
                f'vertex="1" parent="{t.cell_id}">'
            )
            add(
                f'          <mxGeometry y="{HEADER_H + j * ROW_H}" width="{TABLE_W}" '
                f'height="{ROW_H}" as="geometry" />'
            )
            add("        </mxCell>")

            badge_color = "#b85450" if c.pk else ("#6c8ebf" if c.fk else "#666666")
            _cell(
                add, f"{rid}c0", rid, c.badge, 0, KEY_W,
                f"align=center;fontStyle=1;fontColor={badge_color};fontSize=10;",
            )
            label = f"{c.name}  :  {c.dtype}" + ("" if c.nullable else "  NOT NULL")
            _cell(
                add, f"{rid}c1", rid, label, KEY_W, TABLE_W - KEY_W,
                "align=left;spacingLeft=6;",
            )

    # ---- relations
    by_key = {t.key: t for t in tables}
    for r in relations:
        child, parent = by_key[r.child], by_key[r.parent]
        src = child.row_ids.get(r.child_col, child.cell_id)
        dst = parent.row_ids.get(r.parent_col, parent.cell_id)

        if child.x > parent.x:
            ports = "exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;"
        elif child.x < parent.x:
            ports = "exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
        else:  # same band (self-reference or cycle)
            ports = "exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;"

        cycle = ";dashed=1;strokeColor=#b85450;" if r.back_edge else ";strokeColor=#4d4d4d;"
        style = (
            "edgeStyle=entityRelationEdgeStyle;rounded=1;html=1;fontSize=11;"
            "startArrow=ERmany;startFill=0;endArrow=ERone;endFill=0" + cycle + ports
        )
        pair_txt = ", ".join(f"{a} → {b}" for a, b, _ in r.pairs)
        label = f"{r.seq}. {r.name}" + ("  (cycle)" if r.back_edge else "")
        add(
            f'        <mxCell id="e{r.seq}" value={attr(label)} style={attr(style)} '
            f'edge="1" parent="1" source="{src}" target="{dst}">'
        )
        add('          <mxGeometry relative="1" as="geometry" />')
        add("        </mxCell>")

        tip = pair_txt + (
            f"  [ON DELETE {r.delete_rule}]" if r.delete_rule and r.delete_rule != "NO_ACTION" else ""
        )
        add(
            f'        <mxCell id="e{r.seq}l" value={attr(tip)} '
            'style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;'
            'fontSize=9;fontColor=#666666;labelBackgroundColor=#ffffff;" '
            f'vertex="1" connectable="0" parent="e{r.seq}">'
            "\n          <mxGeometry x=\"0.25\" y=\"10\" relative=\"1\" as=\"geometry\">"
            "\n            <mxPoint as=\"offset\" />"
            "\n          </mxGeometry>"
            "\n        </mxCell>"
        )

    # ---- legend
    legend = (
        "&lt;b&gt;Legend&lt;/b&gt;&#10;"
        "PK = primary key&#10;FK = foreign key&#10;U = unique key&#10;"
        "REF = referenced by an FK&#10;&#10;"
        "Crow&#39;s foot = many (child) &#183; bar = one (parent)&#10;"
        "Edge number = relation sequence, in dependency order&#10;"
        "Bands left&#8594;right = FK dependency levels&#10;"
        "Dashed red edge = FK that closes a cycle&#10;"
        "Only relational columns are shown."
    )
    lx = MARGIN_X + (max_level + 1) * (TABLE_W + COL_GAP)
    add(
        f'        <mxCell id="legend" value="{legend}" '
        'style="text;html=1;align=left;verticalAlign=top;fontSize=12;spacing=8;'
        'fillColor=#ffffff;strokeColor=#999999;rounded=1;whiteSpace=wrap;" '
        'vertex="1" parent="1">'
    )
    add(f'          <mxGeometry x="{lx}" y="{MARGIN_Y}" width="290" height="210" as="geometry" />')
    add("        </mxCell>")

    add("      </root>")
    add("    </mxGraphModel>")
    add("  </diagram>")
    add("</mxfile>")
    return "\n".join(out) + "\n"


def _cell(add, cid, parent, value, x, w, extra):
    style = CELL_STYLE.format(extra=extra)
    add(
        f'        <mxCell id="{cid}" value={attr(value)} style={attr(style)} '
        f'vertex="1" parent="{parent}">'
    )
    add(f'          <mxGeometry x="{x}" width="{w}" height="{ROW_H}" as="geometry">')
    add(f'            <mxRectangle width="{w}" height="{ROW_H}" as="alternateBounds" />')
    add("          </mxGeometry>")
    add("        </mxCell>")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", nargs="?", default="-", help="dump from extract_schema.sql ('-' = stdin)")
    ap.add_argument("-o", "--output", default="HRS_SERVICES.drawio")
    ap.add_argument("-t", "--title", default="HRS_SERVICES — relational diagram")
    ap.add_argument("--schema", action="append", help="restrict to these schemas (repeatable)")
    args = ap.parse_args()

    if args.input == "-":
        tables, relations = parse(sys.stdin)
    else:
        with open(args.input, "r", encoding="utf-8-sig", errors="replace") as fh:
            tables, relations = parse(fh)

    if args.schema:
        keep = set(args.schema)
        tables = [t for t in tables if t.schema in keep]
        alive = {t.key for t in tables}
        relations = [r for r in relations if r.child in alive and r.parent in alive]

    if not tables:
        sys.exit("no tables parsed - is the dump empty or in another format?")

    max_level = assign_levels(tables, relations)
    relations = sequence_relations(relations, tables)
    band_x, bands = layout(tables, max_level)
    xml = render(tables, relations, band_x, bands, max_level, args.title)

    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(xml)

    rel_cols = sum(len(t.columns) for t in tables)
    print(
        f"{args.output}: {len(tables)} tables, {rel_cols} relational columns, "
        f"{len(relations)} relations, {max_level + 1} dependency levels",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()

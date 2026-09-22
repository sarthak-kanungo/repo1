# -*- coding: utf-8 -*-
"""Emit callout boxes, leader arrows and target outlines as VML shapes.

VML - not the newer DrawingML `wps` shapes - because Word 2007 has no idea what
`wps` is: it refuses to open a document containing them, and when they arrive
wrapped in an mc:AlternateContent it draws the fallback as empty slivers. VML is
Word 2007's own shape format and is still fully editable in later versions, so
every box can be retyped, resized or deleted and every arrow removed on its own.

All coordinates are in points, measured from the left margin and from the top of
the anchoring paragraph."""
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, nsmap

# python-docx does not know the VML prefixes, so register them before use
nsmap.setdefault("v", "urn:schemas-microsoft-com:vml")
nsmap.setdefault("w10", "urn:schemas-microsoft-com:office:word")
nsmap.setdefault("o", "urn:schemas-microsoft-com:office:office")

NSD = nsdecls("w", "v", "w10", "o", "r")
_next = [0]

ANCHOR = ("position:absolute;mso-position-horizontal-relative:margin;"
          "mso-position-vertical-relative:text")


def _uid(kind):
    _next[0] += 1
    return f"{kind}{_next[0]}"


def _esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def _pict(par, shape):
    par._p.append(parse_xml(f"<w:r {NSD}><w:pict>{shape}</w:pict></w:r>"))


def _f(v):
    return f"{v:.2f}"


def textbox(par, x, y, w, h, text, pt=7.5, font="Arial", line_pt=1.0, z=20):
    """A white callout box with a black border whose text can be edited."""
    style = (f"{ANCHOR};margin-left:{_f(x)}pt;margin-top:{_f(y)}pt;"
             f"width:{_f(w)}pt;height:{_f(h)}pt;z-index:{z}")
    sz = int(round(pt * 2))
    shape = (
      f'<v:rect id="{_uid("cb")}" style="{style}" fillcolor="#ffffff"'
      f' strokecolor="#000000" strokeweight="{_f(line_pt)}pt">'
      '<v:textbox inset="2pt,1pt,2pt,1pt"><w:txbxContent><w:p><w:pPr>'
      '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
      '<w:jc w:val="left"/></w:pPr><w:r><w:rPr>'
      f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/><w:b/>'
      f'<w:color w:val="000000"/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
      f'</w:rPr><w:t xml:space="preserve">{_esc(text)}</w:t></w:r></w:p>'
      '</w:txbxContent></v:textbox><w10:wrap type="none"/></v:rect>')
    _pict(par, shape)


def outline(par, x, y, w, h, line_pt=1.0, z=15):
    """An unfilled rectangle marking the control a callout names."""
    style = (f"{ANCHOR};margin-left:{_f(x)}pt;margin-top:{_f(y)}pt;"
             f"width:{_f(w)}pt;height:{_f(h)}pt;z-index:{z}")
    shape = (f'<v:rect id="{_uid("tg")}" style="{style}" filled="f"'
             f' strokecolor="#000000" strokeweight="{_f(line_pt)}pt">'
             '<w10:wrap type="none"/></v:rect>')
    _pict(par, shape)


def arrow(par, x1, y1, x2, y2, line_pt=0.75, z=18):
    """A straight leader line with an arrow head at (x2, y2).

    `from` is always the left-most end: a v:line that runs right-to-left has a
    negative width and is dropped on import, so a leftward arrow is written
    left-to-right with the head on its start instead."""
    head = "endarrow"
    if (x2, y2) < (x1, y1):
        x1, y1, x2, y2 = x2, y2, x1, y1
        head = "startarrow"
    style = f"{ANCHOR};z-index:{z}"
    shape = (f'<v:line id="{_uid("ld")}" style="{style}"'
             f' from="{_f(x1)}pt,{_f(y1)}pt" to="{_f(x2)}pt,{_f(y2)}pt"'
             f' strokecolor="#000000" strokeweight="{_f(line_pt)}pt">'
             f'<v:stroke {head}="block" {head}width="medium" {head}length="medium"/>'
             '<w10:wrap type="none"/></v:line>')
    _pict(par, shape)

# -*- coding: utf-8 -*-
"""Emit callout boxes, leader arrows and target outlines as native Word shapes,
so their text stays editable and each shape can be moved, resized or deleted."""
from docx.oxml import parse_xml
from docx.oxml.ns import nsmap, nsdecls

nsmap.setdefault("wps", "http://schemas.microsoft.com/office/word/2010/wordprocessingShape")
NSD = nsdecls("w", "wp", "a", "wps", "r")

EMU = 914400
_next = [5000]


def _id():
    _next[0] += 1
    return _next[0]


def _esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


_ANCHOR = """<w:r {nsd}><w:drawing>
<wp:anchor distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="{z}"
 behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1">
<wp:simplePos x="0" y="0"/>
<wp:positionH relativeFrom="column"><wp:posOffset>{x}</wp:posOffset></wp:positionH>
<wp:positionV relativeFrom="paragraph"><wp:posOffset>{y}</wp:posOffset></wp:positionV>
<wp:extent cx="{cx}" cy="{cy}"/>
<wp:effectExtent l="0" t="0" r="0" b="0"/>
<wp:wrapNone/>
<wp:docPr id="{id}" name="{name}"/>
<wp:cNvGraphicFramePr/>
<a:graphic><a:graphicData
 uri="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">{shape}</a:graphicData></a:graphic>
</wp:anchor></w:drawing></w:r>"""


def _anchor(x, y, cx, cy, shape, name, z):
    return parse_xml(_ANCHOR.format(nsd=NSD, x=int(x), y=int(y), cx=max(1, int(cx)),
                                    cy=max(1, int(cy)), shape=shape, name=name,
                                    id=_id(), z=z))


def textbox(par, x, y, cx, cy, text, pt=7.5, font="Arial", line_pt=1.0, z=20):
    """A white callout box with a black border whose text can be edited."""
    shape = (
      '<wps:wsp><wps:cNvSpPr txBox="1"/><wps:spPr>'
      f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{max(1,int(cx))}" cy="{max(1,int(cy))}"/></a:xfrm>'
      '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
      '<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'
      f'<a:ln w="{int(line_pt*12700)}"><a:solidFill><a:srgbClr val="000000"/></a:solidFill></a:ln>'
      '</wps:spPr><wps:txbx><w:txbxContent><w:p><w:pPr>'
      '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
      '<w:jc w:val="left"/></w:pPr><w:r><w:rPr>'
      f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/><w:b/>'
      f'<w:color w:val="000000"/><w:sz w:val="{int(round(pt*2))}"/>'
      f'<w:szCs w:val="{int(round(pt*2))}"/></w:rPr>'
      f'<w:t xml:space="preserve">{_esc(text)}</w:t></w:r></w:p></w:txbxContent></wps:txbx>'
      '<wps:bodyPr rot="0" vert="horz" wrap="square" lIns="25400" tIns="12700"'
      ' rIns="25400" bIns="12700" anchor="ctr" anchorCtr="0"><a:noAutofit/></wps:bodyPr>'
      '</wps:wsp>')
    par._p.append(_anchor(x, y, cx, cy, shape, "Callout", z))


def outline(par, x, y, cx, cy, line_pt=1.0, z=15):
    """An unfilled rectangle marking the control a callout names."""
    shape = (
      '<wps:wsp><wps:cNvSpPr/><wps:spPr>'
      f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{max(1,int(cx))}" cy="{max(1,int(cy))}"/></a:xfrm>'
      '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/>'
      f'<a:ln w="{int(line_pt*12700)}"><a:solidFill><a:srgbClr val="000000"/></a:solidFill></a:ln>'
      '</wps:spPr><wps:bodyPr/></wps:wsp>')
    par._p.append(_anchor(x, y, cx, cy, shape, "Target", z))


def arrow(par, x1, y1, x2, y2, line_pt=0.75, z=18):
    """A straight leader line with an arrow head at (x2, y2)."""
    x, y = min(x1, x2), min(y1, y2)
    cx, cy = abs(x2 - x1), abs(y2 - y1)
    flip = ""
    if x2 < x1:
        flip += ' flipH="1"'
    if y2 < y1:
        flip += ' flipV="1"'
    shape = (
      '<wps:wsp><wps:cNvCnPr/><wps:spPr>'
      f'<a:xfrm{flip}><a:off x="0" y="0"/><a:ext cx="{max(1,int(cx))}" cy="{max(1,int(cy))}"/></a:xfrm>'
      '<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
      f'<a:ln w="{int(line_pt*12700)}"><a:solidFill><a:srgbClr val="000000"/></a:solidFill>'
      '<a:tailEnd type="triangle" w="med" len="med"/></a:ln>'
      '</wps:spPr><wps:bodyPr/></wps:wsp>')
    par._p.append(_anchor(x, y, cx, cy, shape, "Leader", z))

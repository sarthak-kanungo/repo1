"""Render fig1-style annotated screenshots: white callout boxes, black leader
arrows and a black outline around the control each callout names."""
import re, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pytesseract

BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

GUTTER   = 660          # px of white space each side of the phone
PAD_TOP  = 40
PAD_BOT  = 40
FS       = 38           # callout font size
BOXPAD   = 14
MAXTXT   = 560          # max text width inside a callout box
LINE_W   = 4
TARGET_W = 5
GAP      = 22           # min vertical gap between stacked callouts

_ocr_cache = {}

# --- device frame ----------------------------------------------------------
BEZEL    = 36          # chassis thickness around the screen
BTN_OUT  = 9           # how far the side buttons stand proud of the chassis
R_OUT    = 168         # outer chassis corner radius
R_IN     = 132         # screen corner radius
CHASSIS  = (18, 22, 31)
RIM      = (86, 94, 110)
BTN      = (52, 58, 70)


def frame_phone(img):
    """Wrap a raw screen capture in a mobile device frame.

    Returns (framed_image, dx, dy) where dx/dy is where the screen's own
    (0, 0) now sits inside the framed image."""
    W, H = img.size
    dx, dy = BTN_OUT + BEZEL, BEZEL
    FW, FH = W + 2 * BEZEL + 2 * BTN_OUT, H + 2 * BEZEL
    out = Image.new("RGB", (FW, FH), "white")
    d = ImageDraw.Draw(out)
    cx0, cx1 = BTN_OUT, FW - BTN_OUT - 1

    # side buttons first, so the chassis overlaps their inner half
    for y0, y1 in ((int(H * 0.20), int(H * 0.27)), (int(H * 0.30), int(H * 0.41))):
        d.rounded_rectangle([0, y0, cx0 + 16, y1], radius=9, fill=BTN)          # volume
    y0, y1 = int(H * 0.26), int(H * 0.38)
    d.rounded_rectangle([cx1 - 16, y0, FW - 1, y1], radius=9, fill=BTN)         # power

    d.rounded_rectangle([cx0, 0, cx1, FH - 1], radius=R_OUT, fill=CHASSIS)
    d.rounded_rectangle([cx0 + 5, 5, cx1 - 5, FH - 6], radius=R_OUT - 5, outline=RIM, width=3)

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W - 1, H - 1], radius=R_IN, fill=255)
    out.paste(img.convert("RGB"), (dx, dy), mask)
    return out, dx, dy


def ocr_lines(path):
    if path in _ocr_cache:
        return _ocr_cache[path]
    d = pytesseract.image_to_data(Image.open(path), output_type=pytesseract.Output.DICT,
                                  config="--psm 11")
    lines = {}
    for i in range(len(d["text"])):
        t = d["text"][i].strip()
        if not t or int(d["conf"][i]) < 35:
            continue
        k = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        lines.setdefault(k, []).append((d["left"][i], d["top"][i], d["width"][i], d["height"][i], t))
    out = []
    for ws in lines.values():
        x0 = min(w[0] for w in ws); y0 = min(w[1] for w in ws)
        x1 = max(w[0] + w[2] for w in ws); y1 = max(w[1] + w[3] for w in ws)
        out.append((x0, y0, x1 - x0, y1 - y0, " ".join(w[4] for w in ws)))
    _ocr_cache[path] = out
    return out


def find(path, pattern, nth=0, pad=10):
    """Bounding box of the nth OCR line matching `pattern` (case-insensitive)."""
    hits = [l for l in ocr_lines(path) if re.search(pattern, l[4], re.I)]
    if not hits:
        raise KeyError(f"{pattern!r} not found in {path}")
    x, y, w, h, _ = sorted(hits, key=lambda l: (l[1], l[0]))[nth]
    return (x - pad, y - pad, w + 2 * pad, h + 2 * pad)


def _wrap(draw, text, font):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= MAXTXT or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def _place(items, top, bottom):
    """Stack callout boxes on one side without overlapping, near their targets."""
    items.sort(key=lambda it: it["ty"])
    total = sum(it["bh"] for it in items) + GAP * max(0, len(items) - 1)
    span = bottom - top
    if total > span:                      # squeeze: distribute evenly
        step = (span - sum(it["bh"] for it in items)) / max(1, len(items) - 1) if len(items) > 1 else 0
        y = top
        for it in items:
            it["by"] = y
            y += it["bh"] + max(0, step)
        return
    y = top
    for it in items:
        want = it["ty"] - it["bh"] / 2
        it["by"] = max(y, min(want, bottom - it["bh"]))
        y = it["by"] + it["bh"] + GAP
    # pull the stack up if it overflowed the bottom
    over = items[-1]["by"] + items[-1]["bh"] - bottom
    if over > 0:
        for it in reversed(items):
            it["by"] -= over
            over = max(0, top - it["by"]) if it["by"] < top else 0
            if over == 0:
                break


def render(screen, callouts, out, crop_top=0, crop_bottom=0, device=True):
    """callouts: list of dicts {label, rect=(x,y,w,h), side='L'|'R'}"""
    ph = Image.open(screen).convert("RGB")
    if crop_top or crop_bottom:
        ph = ph.crop((0, crop_top, ph.width, ph.height - crop_bottom))
    SW, SH = ph.size                      # the screen itself
    if device:
        ph, dx, dy = frame_phone(ph)
    else:
        dx = dy = 0
    PW, PH = ph.size
    CW, CH = PW + 2 * GUTTER, PH + PAD_TOP + PAD_BOT
    canvas = Image.new("RGB", (CW, CH), "white")
    canvas.paste(ph, (GUTTER, PAD_TOP))
    d = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(BOLD, FS)

    prepared = {"L": [], "R": []}
    for c in callouts:
        x, y, w, h = c["rect"]
        y -= crop_top
        # clamp to the screen, then shift into the device frame
        x, y = max(2, x), max(2, y)
        w, h = min(w, SW - x - 2), min(h, SH - y - 2)
        x, y = x + dx, y + dy
        tx, ty = GUTTER + x, PAD_TOP + y
        lines = _wrap(d, c["label"], font)
        lh = FS + 10
        bw = int(max(d.textlength(l, font=font) for l in lines)) + 2 * BOXPAD
        bh = lh * len(lines) + 2 * BOXPAD - 6
        prepared[c.get("side", "R")].append(dict(
            lines=lines, bw=bw, bh=bh, lh=lh,
            tx=tx, ty=ty + h / 2, trect=(tx, ty, w, h), side=c.get("side", "R")))

    _place(prepared["L"], PAD_TOP + 10, CH - PAD_BOT - 10)
    _place(prepared["R"], PAD_TOP + 10, CH - PAD_BOT - 10)

    for side in ("L", "R"):
        for it in prepared[side]:
            bx = GUTTER - 30 - it["bw"] if side == "L" else GUTTER + PW + 30
            by = it["by"]
            tx, ty, tw, th = it["trect"]
            # outline the control being named
            d.rectangle([tx, ty, tx + tw, ty + th], outline="black", width=TARGET_W)
            # leader line from the box to the nearest edge of the control
            ax = bx + it["bw"] if side == "L" else bx
            ay = by + it["bh"] / 2
            px = tx if side == "L" else tx + tw
            py = ty + th / 2
            d.line([ax, ay, px, py], fill="black", width=LINE_W)
            # arrow head
            ang = math.atan2(py - ay, px - ax)
            for s in (+1, -1):
                d.line([px, py,
                        px - 26 * math.cos(ang + s * 0.42),
                        py - 26 * math.sin(ang + s * 0.42)], fill="black", width=LINE_W)
            # the callout box itself
            d.rectangle([bx, by, bx + it["bw"], by + it["bh"]], fill="white", outline="black", width=3)
            for i, ln in enumerate(it["lines"]):
                d.text((bx + BOXPAD, by + BOXPAD - 4 + i * it["lh"]), ln, fill="black", font=font)
    canvas.save(out)
    return out


def at(path, pattern, nth=0, pad=12):
    return find(path, pattern, nth, pad)


def below(path, pattern, w=None, h=128, gap=20, nth=0):
    """Rect of the control sitting directly under a field label."""
    x, y, lw, lh = find(path, pattern, nth, pad=0)
    return (x - 4, y + lh + gap, (w or lw) + 8, h)


def resolve(path, r):
    """A spec rect: a 4-tuple, or ('at'|'below', pattern, ...)."""
    if isinstance(r, tuple) and len(r) == 4 and all(isinstance(v, int) for v in r):
        return r
    kind = r[0]
    if kind == "at":
        return at(path, *r[1:])
    if kind == "below":
        return below(path, *r[1:])
    raise ValueError(r)

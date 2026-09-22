"""Detect form controls (input boxes, dropdowns, buttons, section bands) on JBM DMS app screenshots."""
import cv2, numpy as np
from PIL import Image

SLATE   = (241, 245, 249)
BORDERS = [(203, 213, 225), (226, 232, 240)]


def _mask(a, rgb, tol=6):
    d = np.abs(a.astype(np.int16) - np.array(rgb, np.int16)).max(axis=2)
    return (d <= tol).astype(np.uint8) * 255


def _interior_light(a, x, y, w, h, inset=10):
    p = a[y + inset:y + h - inset, x + inset:x + w - inset]
    if p.size == 0:
        return 0.0
    return float((p.min(axis=2) > 200).mean())


def detect(path):
    a = np.array(Image.open(path).convert("RGB"))
    H, W = a.shape[:2]
    minw, out = int(W * 0.14), []

    # 1. slate-filled controls
    m = cv2.morphologyEx(_mask(a, SLATE, 5), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    for c, _ in [(c, 0) for c in cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]]:
        x, y, w, h = cv2.boundingRect(c)
        if w >= minw and 45 <= h <= 210 and cv2.contourArea(c) / (w * h) > 0.75:
            out.append((y, x, w, h, "field"))

    # 2. white controls drawn with a grey outline
    bm = np.zeros((H, W), np.uint8)
    for b in BORDERS:
        bm |= _mask(a, b, 10)
    bm = cv2.dilate(bm, np.ones((3, 3), np.uint8))
    for c in cv2.findContours(bm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(c)
        if w >= minw and 45 <= h <= 210 and _interior_light(a, x, y, w, h) > 0.80:
            out.append((y, x, w, h, "field"))

    # 3. blue section bands and primary buttons
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
    bl = cv2.inRange(hsv, np.array([95, 120, 80]), np.array([120, 255, 255]))
    bl = cv2.morphologyEx(bl, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    for c in cv2.findContours(bl, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(c)
        if w >= minw and 45 <= h <= 260 and cv2.contourArea(c) / (w * h) > 0.75 and y > H * 0.10:
            out.append((y, x, w, h, "blue"))

    # de-duplicate overlapping detections, keeping the first (largest-priority) one
    out.sort()
    keep = []
    for b in out:
        y, x, w, h, k = b
        if any(abs(y - y2) < 25 and abs(x - x2) < 25 and abs(w - w2) < 40 for y2, x2, w2, h2, _ in keep):
            continue
        keep.append(b)
    return keep


def debug(path, out):
    a = np.array(Image.open(path).convert("RGB"))
    boxes = detect(path)
    for i, (y, x, w, h, k) in enumerate(boxes, 1):
        col = (255, 0, 0) if k == "field" else (255, 0, 255)
        cv2.rectangle(a, (x, y), (x + w, y + h), col, 4)
        cv2.putText(a, str(i), (x + 8, y + 46), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (230, 0, 0), 5)
    Image.fromarray(a).save(out)
    return boxes


if __name__ == "__main__":
    import sys
    for i, (y, x, w, h, k) in enumerate(debug(sys.argv[1], sys.argv[2]), 1):
        print(i, k, (x, y, w, h))


# --- labelling -------------------------------------------------------------
import pytesseract, re


def _ocr(img, psm=7):
    t = pytesseract.image_to_string(img, config=f"--psm {psm}")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _clean(t):
    t = t.replace("|", "I").replace("“", '"').replace("”", '"')
    t = re.sub(r"[^A-Za-z0-9 ./%&#*()+,:'\-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" .-:")
    return t


def label_for(a, box, W):
    """Read the caption printed immediately above a control."""
    y, x, w, h, kind = box
    if kind == "blue":                      # section band: caption is inside
        crop = a[y + 4:y + h - 4, x + 4:x + w - 4]
        txt = _ocr(Image.fromarray(crop), psm=6).split("\n")[0]
        return _clean(txt)
    top = max(0, y - 62)
    crop = a[top:y - 4, max(0, x - 6):min(W, x + w + 6)]
    if crop.size == 0:
        return ""
    big = Image.fromarray(crop).resize((crop.shape[1] * 2, crop.shape[0] * 2), Image.LANCZOS)
    return _clean(_ocr(big))


def value_for(a, box):
    y, x, w, h, kind = box
    if kind == "blue":
        return ""
    crop = a[y + 8:y + h - 8, x + 10:x + w - 46]
    if crop.size == 0:
        return ""
    big = Image.fromarray(crop).resize((crop.shape[1] * 2, crop.shape[0] * 2), Image.LANCZOS)
    return _clean(_ocr(big))


def annotate_list(path):
    a = np.array(Image.open(path).convert("RGB"))
    W = a.shape[1]
    rows = []
    for b in detect(path):
        rows.append((b, label_for(a, b, W), value_for(a, b)))
    return rows


def detect_small(path):
    """Checkboxes and toggle switches, which are too small for detect()."""
    a = np.array(Image.open(path).convert("RGB"))
    H, W = a.shape[:2]
    out = []
    g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    dark = cv2.inRange(g, 0, 90)
    for c in cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(c)
        if 34 <= w <= 70 and 34 <= h <= 70 and 0.8 <= w / h <= 1.25 and y > H * 0.12:
            if _interior_light(a, x, y, w, h, 8) > 0.6:
                out.append((y, x, w, h, "check"))
    return out

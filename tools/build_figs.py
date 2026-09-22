# -*- coding: utf-8 -*-
"""Merge detected controls with the curated spec and render every figure."""
import sys, json, os
sys.path.insert(0, "lib")
import anno
import spec_a, spec_b, spec_c

STEPS = spec_a.STEPS + spec_b.STEPS + spec_c.STEPS
CAT = json.load(open("catalog.json"))
os.makedirs("figs", exist_ok=True)


def callouts_for(step):
    scr = step["screen"]
    path = f"screens/{scr}.png"
    labels = step.get("labels", {})
    drop = step.get("drop", [])
    out = []
    if drop != "all":
        dropset = set(drop)
        for r in CAT[scr]:
            key = (r["x"], r["y"])
            if key in dropset:
                continue
            if key in labels:
                text, side = labels[key]
            else:
                continue          # only keep controls we have curated text for
            out.append(dict(label=text, rect=(r["x"], r["y"], r["w"], r["h"]), side=side))
    for text, rect, side in step.get("extra", []):
        out.append(dict(label=text, rect=anno.resolve(path, rect), side=side))
    return out


def main():
    missing = []
    for i, st in enumerate(STEPS, 1):
        scr = st["screen"]
        co = callouts_for(st)
        if not co:
            missing.append(scr)
        out = f"figs/fig{i:02d}_{scr}.png"
        anno.render(f"screens/{scr}.png", co, out, crop_top=165, crop_bottom=30)
        print(f"{i:2}. {scr}  {len(co):2} callouts  -> {out}", flush=True)
    # sanity: every curated label must have matched a detected control
    for st in STEPS:
        scr = st["screen"]
        keys = {(r["x"], r["y"]) for r in CAT[scr]}
        for k in st.get("labels", {}):
            if k not in keys:
                print("  !! label key not found in catalog:", scr, k)
    if missing:
        print("!! screens with no callouts:", missing)


if __name__ == "__main__":
    main()

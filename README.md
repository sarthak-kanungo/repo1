# JBM DMS — Service Mobile App User Manual

A field-by-field user manual for the JBM DMS Service Mobile App, rebuilt from
`JBM_DMS_Service_Mobile_App_User_Mannual.doc` so that every application screen is
laid out in the JBM screen-guide style: a blue step heading, square-bullet
instructions, a blue section band, and a screenshot — shown in a **mobile device
frame** — in which **every field, button, badge and filter carries its own
callout box and leader arrow**.

The callouts are **native Word shapes, not part of the picture**: the text in
any box can be retyped, the box moved, resized or deleted, and any arrow or
target outline deleted on its own.

## Deliverables

| File | Description |
|---|---|
| `JBM_DMS_Service_Mobile_App_User_Manual.docx` | The manual (Word, A4 portrait, 48 pages) |
| `JBM_DMS_Service_Mobile_App_User_Manual.pdf` | The same manual exported to PDF for review |

## What is inside

- **34 annotated screens**, numbered `i.` to `xxxiv.`, carrying **403 field callouts** in total.
- Each callout is three separate, editable shapes — the white text box, the
  leader arrow, and the outline around the control it names — so a reader can
  reword, rearrange or remove any of them in Word.
- Every screenshot is composited into a mobile device frame (chassis, rounded
  screen corners and side buttons) with the status bar left intact.
- Chapters follow the source manual: Introduction, Login / Logout, User Profile,
  Contact Us, Gate In / Gate Out, Auto Job Cards (Daily / Ten-Day),
  Assign Auto Job Cards, DCR Charging, User Troubleshooting and
  JBM Officials Interviewed.
- Instructions, objectives, notes, the login-validation table and the
  troubleshooting table are carried over from the source manual.
- Running header with the THRSL lockup, footer with `HRSL Confidential` and live
  page numbers.

## How it was produced

`tools/` holds the pipeline used to build the manual:

| Script | Role |
|---|---|
| `detect.py` | Finds form controls on a screenshot (filled inputs, outlined inputs, blue section bands and buttons, checkboxes) and OCRs each control's caption and value |
| `anno.py` | Wraps a screen capture in a mobile device frame and lays out the callouts — box placement, leader arrows and target outlines — exporting the geometry (and a flat PNG preview) |
| `shapes.py` | Emits that geometry as VML shapes: editable text boxes, arrow lines and unfilled outline rectangles |
| `spec_a.py`, `spec_b.py`, `spec_c.py` | The curated step specification: chapter, title, instructions, note and the callout text and side for every control |
| `build_figs.py` | Merges the detected controls with the specification, writes the 34 bare device shots and their callout geometry |
| `build_docx.py` | Lays the figures, instructions and tables out into the Word document |

The screenshots themselves are extracted from the `Data` stream of the source
`.doc`, so the pipeline needs that file present to run end to end.

### Why the callouts are VML and not DrawingML

The callouts are written as VML (`w:pict` / `v:rect` / `v:line`) rather than the
newer DrawingML `wps` shapes, because the manual is opened in **Word 2007**,
which predates `wps`: given those shapes it refuses to open the file at all
("problems with the contents"), and given them wrapped in an
`mc:AlternateContent` it draws the fallback as empty slivers. VML is Word 2007's
own shape format and is still editable in every later version.

One VML quirk worth knowing: a `v:line` whose `from` lies to the right of its
`to` has a negative width and is silently dropped on import, so `shapes.arrow()`
always writes the left-most end first and moves the head to `startarrow` when
the arrow points left.

Requires `python-docx`, `python-pptx`, `Pillow`, `numpy`, `opencv-python-headless`,
`pytesseract` and `tesseract-ocr`.

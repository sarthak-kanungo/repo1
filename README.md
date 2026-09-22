# JBM DMS — Service Mobile App User Manual

A field-by-field user manual for the JBM DMS Service Mobile App, rebuilt from
`JBM_DMS_Service_Mobile_App_User_Mannual.doc` so that every application screen is
laid out in the JBM screen-guide style: a blue step heading, square-bullet
instructions, a blue section band, and a screenshot in which **every field,
button, badge and filter carries its own callout box and leader arrow**.

## Deliverables

| File | Description |
|---|---|
| `JBM_DMS_Service_Mobile_App_User_Manual.docx` | The manual (Word, A4 portrait, 48 pages) |
| `JBM_DMS_Service_Mobile_App_User_Manual.pdf` | The same manual exported to PDF for review |

## What is inside

- **34 annotated screens**, numbered `i.` to `xxxiv.`, carrying **411 field callouts** in total.
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
| `anno.py` | Renders a screenshot in the screen-guide style — white callout boxes, black leader arrows and a black outline around the control each callout names |
| `spec_a.py`, `spec_b.py`, `spec_c.py` | The curated step specification: chapter, title, instructions, note and the callout text and side for every control |
| `build_figs.py` | Merges the detected controls with the specification and renders all 34 figures |
| `build_docx.py` | Lays the figures, instructions and tables out into the Word document |

The screenshots themselves are extracted from the `Data` stream of the source
`.doc`, so the pipeline needs that file present to run end to end.

Requires `python-docx`, `python-pptx`, `Pillow`, `numpy`, `opencv-python-headless`,
`pytesseract` and `tesseract-ocr`.

# Offline OCR of the public Trellis report sample

All 12 pages were rendered at 200 DPI with pdfplumber 0.11.9 / pypdfium2 5.13.0 and OCRed locally with Tesseract.js 7.0.0 and the existing English tessdata_fast model. No embedded non-whitespace text was available. Originals and previous files were preserved; there were no network requests or installs.

The cover names **Hon. Jeffrey Y. Hamilton, Jr.** and gives the literal date **11/05/2021**. This is a publisher marketing sample, separate from the preview page from which it was linked. Its values are not current judge analytics or a new personalized report. No numerical analytics rows were created.

`summary.json` links the combined OCR text. Per-page images, text, TSV, original embedded text, raw PDF hashes, tool versions and model provenance are retained. `validated_pages.json` supplies exact byte hashes. `section_inventory.json` and `.csv` inventory report sections and chart labels only.

OCR completed on all pages but contains recognition errors. Two engine warnings reported a tiny image/line that could not be recognized. Visual checks of pages 7 and 12 also confirmed clipping already present in the source chart and heading. `extraction_gaps.json` preserves these limitations. Engine confidence scores are not correctness probabilities; no chart values or series associations are certified.

The original pre-OCR text file consists of CRLF page separators; its old capture hash matches the LF-normalized string. Both its actual file hash and the old capture hash are retained in the summary, without changing either original.

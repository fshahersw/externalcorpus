"""Local-only rendering and OCR preparation for the fixed public marketing sample."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil

import pdfplumber

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent
ROOT = HERE.parents[4]
PDF = SOURCE / "trellis_judge_report_sample.pdf"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (HERE / "documents.jsonl").exists(), "Prepared inputs are immutable"
    capture = json.loads((SOURCE / "capture.json").read_text(encoding="utf-8-sig"))
    assert sha(PDF) == capture["raw_sha256"]
    before = {p.name: sha(p) for p in SOURCE.iterdir() if p.is_file()}
    model_source = ROOT / "sources/official_courts/ocr/models"
    model = json.loads((model_source / "eng.provenance.json").read_text(encoding="utf-8-sig"))
    assert sha(model_source / "eng.traineddata") == model["sha256"]
    (HERE / "models").mkdir(exist_ok=True)
    shutil.copyfile(model_source / "eng.traineddata", HERE / "models/eng.traineddata")
    shutil.copyfile(model_source / "eng.provenance.json", HERE / "models/eng.provenance.json")
    source_id = "trellis_marketing_sample_" + capture["raw_sha256"][:16]
    rendered = HERE / source_id / "rendered"
    embedded = HERE / source_id / "embedded_text"
    rendered.mkdir(parents=True, exist_ok=True)
    embedded.mkdir(exist_ok=True)
    versions = {n: importlib.metadata.version(n) for n in ("pdfplumber", "pypdfium2", "Pillow")}
    pages, coverage = [], []
    with pdfplumber.open(PDF) as doc:
        assert len(doc.pages) == 12
        for number, page in enumerate(doc.pages, 1):
            text = page.extract_text() or ""
            text_path = embedded / f"page-{number:04d}.txt"
            text_path.write_text(text, encoding="utf-8")
            image_path = rendered / f"page-{number:04d}.png"
            image = page.to_image(resolution=200, antialias=True)
            image.save(image_path, format="PNG")
            pages.append({"source_id": source_id, "page_number": number,
                          "source_pdf_sha256": capture["raw_sha256"], "source_url": capture["source_url"],
                          "image_path": str(image_path), "image_sha256": sha(image_path),
                          "dpi": 200, "render_method": "pdfplumber.Page.to_image via installed pypdfium2; antialias=True",
                          "render_tool_versions": versions, "image_width": image.original.width,
                          "image_height": image.original.height, "image_bytes": image_path.stat().st_size,
                          "document_class": "publisher_marketing_sample", "actual_current_judge_analytics": False})
            coverage.append({**pages[-1], "pdf_width_points": page.width, "pdf_height_points": page.height,
                             "embedded_text_path": str(text_path), "embedded_text_sha256": sha(text_path),
                             "embedded_text_characters": len(text), "embedded_text_nonwhitespace_characters": len("".join(text.split())),
                             "pdf_character_objects": len(page.chars), "pdf_image_objects": len(page.images),
                             "ocr_required": True, "ocr_reason": "image-only marketing report page; no usable embedded text"})
    document = {"source_id": source_id, "source_url": capture["source_url"], "source_pdf_path": str(PDF),
                "source_pdf_relative_path": PDF.relative_to(ROOT).as_posix(), "source_pdf_sha256": capture["raw_sha256"],
                "parent_capture_path": (SOURCE / "capture.json").relative_to(ROOT).as_posix(),
                "parent_capture_sha256": before["capture.json"], "pdf_pages": 12,
                "ocr_pages_needed": 12, "screening_complete": True,
                "label": "Public Trellis judge report marketing sample", "document_class": "publisher_marketing_sample",
                "observed_first_page_subject": "Hon. Jeffrey Y. Hamilton, Jr.",
                "observed_first_page_date_literal": "11/05/2021", "actual_current_judge_analytics": False,
                "language": "eng", "prepared_at": datetime.now(timezone.utc).isoformat()}
    for name, records in (("documents.jsonl", [document]), ("pages.jsonl", pages), ("page_coverage.jsonl", coverage)):
        (HERE / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    summary = {"prepared_at": datetime.now(timezone.utc).isoformat(), "source_pdf_sha256": capture["raw_sha256"],
               "original_file_hashes": before, "documents": 1, "rendered_pages": 12, "queued_pages": 12,
               "embedded_text_nonwhitespace_characters": sum(r["embedded_text_nonwhitespace_characters"] for r in coverage),
               "render_versions": versions, "model_sha256": model["sha256"],
               "model_copied_from": str(model_source / "eng.traineddata"), "language": "eng",
               "network_requests": 0, "source_files_changed": False}
    assert all(sha(SOURCE / name) == value for name, value in before.items())
    (HERE / "preparation.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

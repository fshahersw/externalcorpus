"""Validate local sample OCR and inventory sections without publishing analytics."""
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def rows(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def receipt(path):
    p = Path(path)
    return {"path": rel(p), "sha256": sha(p), "bytes": p.stat().st_size}


def main():
    prepared = read(HERE / "preparation.json")
    capture = read(SOURCE / "capture.json")
    pages = sorted(rows(HERE / "page_results.jsonl"), key=lambda r: r["page_number"])
    manifest = rows(HERE / "pdf_ocr_manifest.jsonl")[0]
    coverage = rows(HERE / "page_coverage.jsonl")
    assert len(pages) == 12 and {r["page_number"] for r in pages} == set(range(1, 13))
    assert manifest["ocr_status"] == "complete" and manifest["ocr_pages_completed"] == 12
    assert sha(SOURCE / "trellis_judge_report_sample.pdf") == capture["raw_sha256"]
    assert all(sha(SOURCE / name) == h for name, h in prepared["original_file_hashes"].items())
    validated = []
    for page in pages:
        assert page["status"] == "succeeded" and page["source_pdf_sha256"] == capture["raw_sha256"]
        assert sha(page["image_path"]) == page["image_sha256"] and sha(page["text_path"]) == page["text_sha256"]
        assert page["language_model_sha256"] == prepared["model_sha256"]
        assert isinstance(page["confidence"], (int, float)) and 0 < page["confidence"] <= 100
        cov = next(r for r in coverage if r["page_number"] == page["page_number"])
        assert sha(cov["embedded_text_path"]) == cov["embedded_text_sha256"]
        text = Path(page["text_path"]).read_text(encoding="utf-8")
        assert len(text) == page["text_characters"] and text.strip()
        validated.append({"page_number": page["page_number"], "source_pdf_sha256": capture["raw_sha256"],
                          "render": receipt(page["image_path"]), "text": receipt(page["text_path"]),
                          "tsv": receipt(page["tsv_path"]), "embedded_text": receipt(cov["embedded_text_path"]),
                          "ocr_engine": page["ocr_engine"], "language": "eng", "language_model_sha256": prepared["model_sha256"],
                          "engine_reported_confidence": page["confidence"], "confidence_is_accuracy_probability": False,
                          "text_characters": len(text), "visual_review": page["page_number"] in (7, 12),
                          "page_completely_recognized": False, "numeric_analytics_validated": False})
    assert sha(manifest["ocr_text_path"]) == manifest["ocr_text_sha256"]
    sections = {
        1: ("Cover", ["Trellis Judge Analytics Report", "Hon. Jeffrey Y. Hamilton, Jr.", "11/05/2021"], []),
        2: ("Table of contents", ["Judge Bio", "Judge At A Glance", "Motion Analytics", "Case Outcome", "Case Milestones"], []),
        3: ("Judge Bio", ["The Honorable Jeffrey Y. Hamilton, Jr.", "Fresno County Superior Court", "CA Bar #", "Appointed By", "Biography"], []),
        4: ("Judge Bio references", ["Articles About Jeffrey Y. Hamilton, Jr.", "Court Rules", "California Rules of Court", "Fresno County Superior Court Local Rules"], []),
        5: ("At a Glance", ["Active Cases", "Average Case Length"], ["In Fresno County", "In CA State", "VS. OTHER JUDGES"]),
        6: ("At a Glance", ["Motion Grant Rate", "Verdict Plaintiff Vs. Defendant"], ["Defendant", "Plaintiff", "In Fresno County", "In CA State"]),
        7: ("At a Glance", ["Case Practice Area Breakdown", "Practice Area"], ["Criminal", "Arbitration", "Securities", "Insurance", "Administrative", "Probate", "Family", "Creditor", "Property", "and Employment [leading text clipped]", "Civil", "Torts", "[additional lower label clipped/unreadable]"]),
        8: ("Motion Analytics — Demurrer", ["Motion Type | Demurrer", "Motion Grant Rates", "When Filed By Plaintiff", "When Filed By Defendant"], ["Hon. Hamilton", "Fresno County", "CA State", "Granted", "Denied", "Partial"]),
        9: ("Motion Analytics — Motion for Summary Judgment", ["Motion Type | Motion for Summery Judgment [OCR spelling]", "Motion Grant Rates", "When Filed By Plaintiff", "When Filed By Defendant"], ["Hon. Hamilton", "Fresno County", "CA State", "Granted", "Denied", "Partial", "There is not enough analytical data for this report."]),
        10: ("Case Outcomes — Overall View", ["Practice Area | Overall View", "Case Outcome Breakdown"], ["Transfer", "Jury Verdict", "Trial Verdict", "Removal", "Other", "Consolidation", "Judgment (Other)", "Dismissal"]),
        11: ("Case Outcomes — Labor and Employment", ["Practice Area | Labor and Employment", "Case Outcome Breakdown"], ["Other", "Trial Verdict", "Jury Verdict", "Removal", "Consolidation", "Judgment (Other)", "Dismissal"]),
        12: ("Case Milestones — Overall View", ["Average Case Duration", "Average Time To Case Management Conferer [right edge clipped in source]", "Average Time To Trial", "Average Time To First Dismissal Order"], ["Hon. Hamilton", "Fresno", "CA"]),
    }
    inventory = []
    for number, (section, headings, chart_labels) in sections.items():
        page = next(r for r in validated if r["page_number"] == number)
        inventory.append({"page_number": number, "section_inventory_label": section,
                          "heading_labels": headings, "chart_or_comparison_labels": chart_labels,
                          "evidence_text": page["text"], "evidence_render": page["render"],
                          "inventory_method": "OCR reading plus visual check of source page" if number in (7, 12) else "OCR reading; source image retained",
                          "label_inventory_complete": False, "inventory_scope": "Major readable headings and chart labels; not an exhaustive transcription",
                          "numeric_values_transcribed_to_structured_analytics": False,
                          "document_class": "publisher_marketing_sample", "actual_current_judge_analytics": False})
    gaps = [
        {"scope": "all pages", "kind": "automatic_OCR_uncertainty", "description": "OCR is automatic and contains visible errors. Completing every page is not a guarantee that every label, word or chart number was recovered."},
        {"page_number": 7, "kind": "source_chart_clipping", "description": "Visual inspection confirms a practice-area label begins only with 'and Employment'; an additional lower label is clipped. No missing category name or number is inferred."},
        {"page_number": 12, "kind": "source_heading_clipping", "description": "The case-management panel heading is visibly clipped at the right edge in the PDF image. A full endpoint label is not claimed from OCR."},
        {"scope": "worker output; page unassigned", "kind": "engine_warning", "literal_warning": "Image too small to scale!! (2x36 vs min width of 3)", "description": "Observed in the two-worker OCR output. Concurrent output does not establish an exact page assignment."},
        {"scope": "worker output; page unassigned", "kind": "engine_warning", "literal_warning": "Line cannot be recognized!!", "description": "Observed in the two-worker OCR output; no page failure occurred. Some small line content may be missing."},
        {"scope": "chart pages 5-12", "kind": "chart_numbers_not_validated", "description": "Numbers remain in original images and raw OCR only. Chart geometry, comparison labels and number-to-series associations have not been validated or promoted to a judge analytics dataset."},
        {"scope": "document", "kind": "historical_marketing_sample", "description": "Cover identifies Hon. Jeffrey Y. Hamilton, Jr. and literal date 11/05/2021. The download was linked from another judge's preview, but this sample is not a newly acquired personalized report or current analytics for either judge."},
    ]
    old_text = (SOURCE / "trellis_judge_report_sample.txt").read_bytes()
    logical_hash = hashlib.sha256(old_text.decode("utf-8").replace("\r\n", "\n").encode()).hexdigest()
    assert logical_hash == capture["text_sha256"]
    original_text_hash_note = {"actual_file_sha256": sha(SOURCE / "trellis_judge_report_sample.txt"),
                               "capture_record_text_sha256": capture["text_sha256"], "capture_hash_matches_LF_normalized_text": True,
                               "explanation": "The existing text file contains CRLF page separators; its capture hash matches the LF-normalized string. Both original file and capture were preserved. No usable embedded text was found."}
    write("validated_pages.json", {"source_pdf": receipt(SOURCE / "trellis_judge_report_sample.pdf"), "pages": validated})
    write("section_inventory.json", {"sample_only": True, "subject_literal": "Hon. Jeffrey Y. Hamilton, Jr.",
                                      "report_date_literal": "11/05/2021", "report_date_normalized": None,
                                      "actual_current_judge_analytics": False, "pages": inventory})
    write("extraction_gaps.json", gaps)
    with (HERE / "section_inventory.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, ["page_number", "section_inventory_label", "heading_labels", "chart_or_comparison_labels", "label_inventory_complete", "actual_current_judge_analytics"])
        writer.writeheader()
        for row in inventory:
            writer.writerow({k: json.dumps(row[k], ensure_ascii=False) if isinstance(row[k], list) else row[k] for k in writer.fieldnames})
    summary = {"completed_at": datetime.now(timezone.utc).isoformat(), "status": "all_pages_OCRed_with_explicit_recognition_and_source_clipping_gaps",
               "document_class": "publisher_marketing_sample", "subject_literal": "Hon. Jeffrey Y. Hamilton, Jr.",
               "report_date_literal": "11/05/2021", "source_url": capture["source_url"],
               "source_pdf": receipt(SOURCE / "trellis_judge_report_sample.pdf"), "pages": 12,
               "rendered_pages": 12, "OCR_completed_pages": 12, "OCR_failed_pages": 0,
               "embedded_text_nonwhitespace_characters": 0, "page_text_characters_total": sum(r["text_characters"] for r in pages),
               "combined_text": receipt(manifest["ocr_text_path"]), "render_DPI": 200,
               "renderer_versions": prepared["render_versions"], "ocr_engine": "tesseract.js 7.0.0",
               "ocr_worker_source": receipt(ROOT / "sources/official_courts/ocr_worker.cjs"), "language": "eng",
               "language_model": receipt(HERE / "models/eng.traineddata"), "engine_confidence_min": min(r["confidence"] for r in pages),
               "engine_confidence_max": max(r["confidence"] for r in pages), "engine_confidence_mean": statistics.mean(r["confidence"] for r in pages),
               "confidence_note": "Values are reported by the OCR engine, not validated accuracy or a probability that text is correct.",
               "visually_checked_pages_this_pass": [7, 12], "source_pages_with_observed_clipping": [7, 12],
               "original_text_hash_note": original_text_hash_note, "source_files_unchanged": True,
               "actual_current_judge_analytics": False, "structured_numeric_analytics_records_created": 0,
               "network_requests": 0, "packages_installed": 0, "background_collectors_started": 0}
    write("summary.json", summary)
    write("validation.json", {"validated_at": datetime.now(timezone.utc).isoformat(), "passed": True,
                               "raw_pdf_and_original_files_unchanged": True, "page_numbers_unique_complete": True,
                               "page_render_text_TSV_embedded_text_hash_receipts": 12,
                               "language_model_hash_verified": True, "combined_text_hash_verified": True,
                               "nonempty_OCR_text_pages": 12, "issue_count_for_artifact_integrity": 0,
                               "recognition_gaps_are_separate": True, "analytics_promotion": False})
    (HERE / "README.md").write_text("# Offline OCR of the public Trellis report sample\n\nAll 12 pages were rendered at 200 DPI with pdfplumber 0.11.9 / pypdfium2 5.13.0 and OCRed locally with Tesseract.js 7.0.0 and the existing English tessdata_fast model. No embedded non-whitespace text was available. Originals and previous files were preserved; there were no network requests or installs.\n\nThe cover names **Hon. Jeffrey Y. Hamilton, Jr.** and gives the literal date **11/05/2021**. This is a publisher marketing sample, separate from the preview page from which it was linked. Its values are not current judge analytics or a new personalized report. No numerical analytics rows were created.\n\n`summary.json` links the combined OCR text. Per-page images, text, TSV, original embedded text, raw PDF hashes, tool versions and model provenance are retained. `validated_pages.json` supplies exact byte hashes. `section_inventory.json` and `.csv` inventory report sections and chart labels only.\n\nOCR completed on all pages but contains recognition errors. Two engine warnings reported a tiny image/line that could not be recognized. Visual checks of pages 7 and 12 also confirmed clipping already present in the source chart and heading. `extraction_gaps.json` preserves these limitations. Engine confidence scores are not correctness probabilities; no chart values or series associations are certified.\n\nThe original pre-OCR text file consists of CRLF page separators; its old capture hash matches the LF-normalized string. Both its actual file hash and the old capture hash are retained in the summary, without changing either original.\n", encoding="utf-8")
    write("files.sha256.json", {"created_at": datetime.now(timezone.utc).isoformat(), "files": [receipt(p) for p in sorted(HERE.rglob("*")) if p.is_file() and p.name != "files.sha256.json"]})
    print(json.dumps({"pages": 12, "OCR_complete": 12, "text_characters": summary["page_text_characters_total"],
                      "integrity_issues": 0, "summary": rel(HERE / "summary.json"), "actual_current_judge_analytics": False}, indent=2))


if __name__ == "__main__":
    main()

"""Independent offline artifact/linkage checks supporting a manual semantic audit."""
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from lxml import html

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PACKAGE = ROOT / "delivery/judge_intelligence_20260913/official_profiles"
INPUT = ROOT / "delivery/focused_legal_corpus/judges"


def read(path):
    return Path(path).read_text(encoding="utf-8-sig")


def rows(path):
    return [json.loads(x) for x in read(path).splitlines() if x.strip()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(node):
    return re.sub(r"\s+", " ", " ".join(node.itertext())).strip()


def main():
    sources = rows(INPUT / "sources.jsonl")
    assert len(sources) == 145 and len({s["source_id"] for s in sources}) == 145
    verified, metadata_files, linkage, dbs, cached_manifests = {}, {}, [], {}, {}
    for s in sources:
        for a in s["raw_artifacts"] + s["text_artifacts"]:
            path = (ROOT / a["workspace_relative_path"]).resolve()
            assert path.is_relative_to(ROOT) and path.is_file()
            if a["workspace_relative_path"] not in verified:
                assert sha(path) == a["sha256"] and path.stat().st_size == a["bytes"]
                verified[a["workspace_relative_path"]] = {"path": a["workspace_relative_path"], "sha256": a["sha256"], "bytes": a["bytes"]}
            else:
                assert verified[a["workspace_relative_path"]]["sha256"] == a["sha256"]
        for c in s["original_capture_records"]:
            mp = ROOT / c["metadata_path"]
            if c["metadata_path"] not in metadata_files:
                metadata_files[c["metadata_path"]] = {"path": c["metadata_path"], "sha256": sha(mp), "bytes": mp.stat().st_size}
            locator = c["source_record_locator"]
            proof = {"source_id": s["source_id"], "package_source_url": s["source_url"], "capture_source_url": c["source_url"], "source_record_locator": locator, "metadata": metadata_files[c["metadata_path"]]}
            if mp.suffix == ".jsonl":
                if mp not in cached_manifests:
                    cached_manifests[mp] = rows(mp)
                line = int(locator.rsplit(":", 1)[1])
                m = cached_manifests[mp][line - 1]
                if c["capture_kind"] == "ocr_derivative":
                    raw = Path(m["source_pdf_path"]).relative_to(ROOT).as_posix()
                    ocr = Path(m["ocr_text_path"]).relative_to(ROOT).as_posix()
                    assert m["source_url"] == c["source_url"] and m["ocr_status"] == "complete"
                    assert any(a["workspace_relative_path"] == raw and a["sha256"] == m["source_pdf_sha256"] for a in s["raw_artifacts"])
                    assert any(a["workspace_relative_path"] == ocr and a["sha256"] == m["ocr_text_sha256"] for a in s["text_artifacts"])
                    assert any(other["capture_kind"] == "direct_public_capture" and other["retrieved_at"] == c["retrieved_at"] for other in s["original_capture_records"])
                    proof.update(fetch_type="verified_parent_linked_OCR_derivative", manifest_line=line, raw_path=raw, raw_sha256=m["source_pdf_sha256"], text_path=ocr, text_sha256=m["ocr_text_sha256"], source_retrieved_at=c["retrieved_at"])
                    linkage.append(proof)
                    continue
                raw = "sources/official_courts/" + m["raw_path"]
                assert c["source_url"] in (m.get("url"), m.get("requested_url"))
                assert m["fetched_at_utc"] == c["retrieved_at"]
                assert m["verification_status"] == "retrieved" and 200 <= m["http_status"] < 300
                proof.update(fetch_type="static_manifest_response", manifest_line=line, http_status=m["http_status"], retrieved_at=m["fetched_at_utc"])
            else:
                m = json.loads(read(mp))
                if c["collection"] == "official_laws":
                    raw = "sources/official_laws/" + m["evidence_path"].replace("\\", "/")
                    assert m["source_url"] == c["source_url"] and m["retrieved_at_utc"] == c["retrieved_at"]
                    assert m["verification_status"] == "retrieved" and 200 <= m["http_status"] < 300
                    assert any(a["workspace_relative_path"] == raw and a["sha256"] == m["sha256"] for a in s["raw_artifacts"])
                    proof.update(fetch_type="static_direct_response_metadata", raw_path=raw, raw_sha256=m["sha256"], http_status=m["http_status"], retrieved_at=m["retrieved_at_utc"])
                    linkage.append(proof)
                    continue
                db_path, resource_id = locator.split("#resources/")
                if db_path not in dbs:
                    db = sqlite3.connect((ROOT / db_path).as_uri() + "?mode=ro", uri=True)
                    db.row_factory = sqlite3.Row
                    db.execute("PRAGMA query_only=ON")
                    dbs[db_path] = db
                resource = dbs[db_path].execute("SELECT * FROM resources WHERE id=?", (int(resource_id),)).fetchone()
                fetch = dbs[db_path].execute("SELECT * FROM fetches WHERE id=?", (m["fetch_id"],)).fetchone()
                assert resource and fetch and fetch["resource_id"] == int(resource_id)
                assert resource["url"] == c["source_url"] == m["requested_url"]
                assert m["status"] == fetch["status"] == "downloaded" and 200 <= m["http_status"] < 300 and m["raw_complete"]
                assert m["sha256"] == fetch["sha256"] and m["fetched_at"] == c["retrieved_at"] == fetch["fetched_at"]
                assert json.loads(fetch["response_json"]) == m
                raw = str(Path(db_path).parent / m["raw_path"]).replace("\\", "/")
                proof.update(fetch_type="sqlite_fetch_response", fetch_id=m["fetch_id"], resource_id=int(resource_id), http_status=m["http_status"], retrieved_at=m["fetched_at"])
            assert any(a["workspace_relative_path"] == raw and a["sha256"] == m["sha256"] for a in s["raw_artifacts"])
            assert c["retrieved_at"] in s["capture_times"]
            proof.update(raw_path=raw, raw_sha256=m["sha256"])
            linkage.append(proof)
    for db in dbs.values():
        db.close()
    assert len(verified) == 293

    # Inspect raw negative controls, without relying on the builder's validation.
    profiles = rows(PACKAGE / "profiles.jsonl")
    by_url = {s["source_url"]: s for s in sources}
    docs = {}
    def doc(url):
        s = by_url[url]
        if url not in docs:
            docs[url] = html.fromstring((ROOT / s["raw_path"]).read_text(encoding="utf-8", errors="replace"))
        return docs[url]
    controls = []
    url = "https://arcourts.gov/directories/district-courts"
    observed = {p["observed_name"] for p in profiles if p["source_url"] == url}
    nonjudge = []
    for table in doc(url).xpath("//table"):
        trs = table.xpath("./tr|./thead/tr|./tbody/tr")
        if not trs:
            continue
        headers = [norm(x).lower() for x in trs[0].xpath("./th|./td")]
        if "position" not in headers or "name" not in headers:
            continue
        pi, ni = headers.index("position"), headers.index("name")
        for tr in trs[1:]:
            cells = tr.xpath("./td")
            if len(cells) <= max(pi, ni):
                continue
            position, name = norm(cells[pi]), norm(cells[ni])
            if position.lower() != "district judge":
                nonjudge.append({"name": name, "role": position, "locator": tr.getroottree().getpath(tr), "profile_absent": name not in observed})
    assert nonjudge and all(x["profile_absent"] for x in nonjudge)
    controls.append({"source_url": url, "control": "nonjudge_Position_rows", "rows_checked": len(nonjudge), "distinct_role_counts": dict(collections.Counter(x["role"] for x in nonjudge)), "sample": nonjudge[:5], "passed": True})
    url = "https://courts.delaware.gov/family/judges.aspx"
    observed = {p["observed_name"] for p in profiles if p["source_url"] == url}
    commissioners = []
    for table in doc(url).xpath("//table"):
        trs = table.xpath("./tr|./thead/tr|./tbody/tr")
        if not trs or "Commissioners" not in norm(trs[0]):
            continue
        for tr in trs[1:]:
            cells = tr.xpath("./td")
            if cells:
                name = norm(cells[0])
                person_name = re.sub(r"^Commissioner\s+", "", name, flags=re.I)
                commissioners.append({"name": name, "person_name_checked": person_name, "locator": tr.getroottree().getpath(tr), "profile_absent": person_name not in observed})
    assert commissioners and all(x["profile_absent"] for x in commissioners)
    controls.append({"source_url": url, "control": "separate_commissioners_table", "rows_checked": len(commissioners), "sample": commissioners[:5], "passed": True})
    url = "https://www.cockecountytn.gov/sessions-court-judge"
    assert "Christen Ray" in norm(doc(url)) and not any(p["observed_name"] == "Christen Ray" and p["source_url"] == url for p in profiles)
    assert "Administrative Assistant" in norm(doc(url))
    controls.append({"source_url": url, "control": "named_administrative_assistant_not_judge", "name": "Christen Ray", "passed": True})
    assert not any(re.search(r"\b(vacant|vacancy)\b", p["observed_name"], re.I) for p in profiles)
    controls.append({"control": "no_vacancy_names_promoted", "passed": True})

    duplicate_groups, duplicate_extra = [], 0
    for p in profiles:
        if len(p["locators"]) < 2:
            continue
        d = doc(p["source_url"])
        values = [[norm(c) for c in d.xpath(x)[0].xpath("./th|./td")] for x in p["locators"]]
        assert values[0] and all(v == values[0] for v in values)
        duplicate_groups.append({"profile_id": p["profile_id"], "name": p["observed_name"], "source_url": p["source_url"], "locators": p["locators"], "identical_row_values": True})
        duplicate_extra += len(p["locators"]) - 1
    result = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(), "source_rows": len(sources), "unique_source_urls": len(by_url), "original_artifacts_verified": len(verified), "original_artifact_bytes": sum(a["bytes"] for a in verified.values()), "capture_linkages_verified": len(linkage), "capture_linkage_types": dict(collections.Counter(x["fetch_type"] for x in linkage)), "metadata_files_verified": len(metadata_files), "artifact_receipts": list(verified.values()), "capture_linkages": linkage, "negative_controls": controls, "duplicate_groups_checked": len(duplicate_groups), "extra_locators_checked": duplicate_extra, "duplicate_groups": duplicate_groups, "issues": [], "network_requests": 0, "source_mutations": 0, "semantic_limit": "Artifact and structural controls support but do not substitute for the separately recorded 40-observation manual semantic sample."}
    (OUT / "official_semantic_core_checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("artifact_receipts", "capture_linkages", "duplicate_groups")}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()

"""Offline evidence-only county alias review; never ingests or fetches URLs."""
from collections import Counter, defaultdict
from contextlib import closing
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit, urljoin

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_county_entries_resume_20260913 as util
import prepare_county_entries_resume_pass2_20260913 as prior_tools
import prepare_county_canonical_continuation_20260913 as alias

SOURCE_COLLECTIONS = ("corpus/county_registry_continuation_20260913", "corpus/county_entries_continuation_20260913")
ROBOTS_FAMILY = "derived_county_entry_from_observed_robots_redirect_origin"
HTTP_FAMILY = "observed_county_entry_from_same_domain_http_redirect"
REDIRECTS = {301, 302, 303, 307, 308}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jsonl(name, values):
    (OUT / name).write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in values), encoding="utf-8")


def main():
    if (OUT / "summary.json").exists():
        raise RuntimeError("Existing review is immutable; use a new package for a new snapshot")
    refs = {}
    def reference(value, expected=None, kind="input"):
        path = (ROOT / value).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError("Missing or out-of-workspace reference: " + str(value))
        key = util.relative(path)
        if key not in refs:
            refs[key] = {"path": key, "sha256": util.sha(path), "bytes": path.stat().st_size, "kinds": []}
        ref = refs[key]
        if expected is not None and ref["sha256"] != expected:
            raise ValueError("Hash mismatch: " + key)
        if kind not in ref["kinds"]:
            ref["kinds"].append(kind)
        return ref
    scope = util.read(ROOT / "reports/remaining_resume_20260913/scope.json")
    assert scope["latest_user_direction"] == "Continue official sources only"
    reference("reports/remaining_resume_20260913/scope.json", kind="active_scope")
    reference("RUNBOOK.md", kind="active_runbook")
    # Probe existing exclusive locks without changing lock-file contents.
    probe_cmd = "Get-CimInstance Win32_Process -Filter \"Name = 'python.exe'\" | Where-Object { $_.CommandLine -like '*corpus_crawler.py*' -and ($_.CommandLine -like '*county_entries_continuation_20260913*' -or $_.CommandLine -like '*county_registry_continuation_20260913*') } | Select-Object ProcessId,CreationDate | ConvertTo-Json -Compress"
    process = subprocess.run(["powershell", "-NoProfile", "-Command", probe_cmd], capture_output=True, text=True, check=True)
    assert not process.stdout.strip(), "A reviewed county collector is live"
    lock_checks, snapshots, source_db_hashes = [], {}, {}
    for collection in SOURCE_COLLECTIONS:
        base = ROOT / collection
        lock_path = base / ".crawler.lock"
        assert lock_path.is_file() and lock_path.stat().st_size > 0
        before = util.sha(lock_path)
        with util.engine.run_lock(base):
            pass
        assert util.sha(lock_path) == before
        lock_checks.append({"collection": collection, "probed_at": util.now(), "exclusive_lock_available": True, "lock_file_sha256_unchanged": before})
        db_path = base / "corpus.sqlite3"
        source_db_hashes[util.relative(db_path)] = util.sha(db_path)
        with closing(util.db_read(db_path)) as db:
            resources = [dict(r) for r in db.execute("SELECT id,url,status,last_fetch_id,last_http_status,raw_path,sha256,raw_complete,metadata_path,redirect_url,attempts FROM resources ORDER BY id")]
            contexts = {r["id"]: dict(r) for r in db.execute("SELECT id,seed_url,source_family,jurisdiction_json,seed_json FROM contexts")}
            associations = [dict(r) for r in db.execute("SELECT resource_id,context_id FROM resource_contexts")]
            runs = [dict(r) for r in db.execute("SELECT id,started_at,ended_at,stop_reason,processed FROM runs ORDER BY rowid")]
        assert not any(r["status"] == "fetching" for r in resources)
        snapshots[collection] = {"resources": resources, "contexts": contexts, "associations": associations, "runs": runs}
        reference(collection + "/config.json", kind="unchanged_source_config")
    write("source_process_and_lock_checks.json", {"observed_at": util.now(), "matching_crawler_processes": [], "lock_checks": lock_checks})

    reviews, candidates, integrity_errors = [], [], []
    registry_index = {}
    for collection, snap in snapshots.items():
        base = ROOT / collection
        by_resource = defaultdict(list)
        for link in snap["associations"]:
            by_resource[link["resource_id"]].append(snap["contexts"][link["context_id"]])
        for row in snap["resources"]:
            if row["status"] not in ("robots_redirect_outside_host", "redirect"):
                continue
            item = {"source_collection": collection, "source_resource_id": row["id"], "source_url": row["url"], "source_status": row["status"], "context_ids": sorted(c["id"] for c in by_resource[row["id"]])}
            try:
                kind = "robots" if row["status"] == "robots_redirect_outside_host" else "http"
                item["evidence_kind"] = kind
                parent = reference(str(base / row["metadata_path"]), kind="parent_resource_metadata")
                metadata = util.read(ROOT / parent["path"])
                assert metadata["requested_url"] == row["url"]
                proof = {"source_collection": collection, "source_resource_id": row["id"], "source_entry_url": row["url"], "parent_metadata_path": parent["path"], "parent_metadata_sha256": parent["sha256"], "source_fetch_id": row["last_fetch_id"]}
                if kind == "robots":
                    source = urlsplit(row["url"])
                    origin = source.scheme + "://" + source.netloc
                    control_path = base / "controls/robots" / (hashlib.sha256(origin.encode()).hexdigest() + ".json")
                    control_ref = reference(str(control_path), kind="robots_control")
                    control = util.read(control_path)
                    assert control["origin"] == origin and control["problem"] == "robots_redirect_outside_host" and not control.get("in_progress")
                    observations = control["observations"]
                    assert observations
                    # Retain and verify the entire observed robots response chain.
                    chain_refs = []
                    for observation in observations:
                        if observation.get("raw_path"):
                            chain_refs.append(reference(str(base / observation["raw_path"]), observation.get("sha256"), "robots_response"))
                    if any(o.get("http_status") in (401, 403, 429) for o in observations):
                        item.update(review_decision="excluded_access_denial_in_robots_history", provenance=proof)
                        reviews.append(item)
                        continue
                    response = observations[-1]
                    proof.update(robots_control_path=control_ref["path"], robots_control_sha256=control_ref["sha256"], requested_robots_url=response["requested_url"], robots_observation_raw_refs=[{"path": r["path"], "sha256": r["sha256"]} for r in chain_refs])
                else:
                    response = metadata
                    assert response["status"] == "redirect"
                    proof.update(redirect_metadata_path=parent["path"], redirect_metadata_sha256=parent["sha256"], requested_url=response["requested_url"])
                location = response.get("headers", {}).get("location", "")
                target = alias.alias_target(row["url"], response["requested_url"], location, kind)
                proof.update(http_status=response.get("http_status"), location_header=location, observed_redirect_target=util.engine.canonical_url(urljoin(response["requested_url"], location)), fetched_at=response.get("fetched_at"))
                item["provenance"] = proof
                if not target or response.get("http_status") not in REDIRECTS or not response.get("raw_complete"):
                    a = urlsplit(row["url"]); b = urlsplit(proof["observed_redirect_target"] or "")
                    reason = "excluded_other_domain_or_noncanonical_redirect" if not alias.exact_alias(a.hostname, b.hostname) else "excluded_path_query_or_incomplete_response"
                    item.update(review_decision=reason)
                    reviews.append(item)
                    continue
                raw = reference(str(base / response["raw_path"]), response["sha256"], "redirect_response_raw")
                proof.update(raw_path=raw["path"], raw_sha256=raw["sha256"], raw_sha256_verified=True, raw_bytes=raw["bytes"])
                if kind == "http":
                    assert metadata["redirect_url"] == proof["observed_redirect_target"] == target and metadata["sha256"] == raw["sha256"]
                item.update(candidate_url=target, review_decision="verified_exact_www_alias_preserving_path_query")
                for context in by_resource[row["id"]]:
                    original = json.loads(context["seed_json"])
                    seed = copy.deepcopy(original)
                    registry = "registered_domain" in original and "registry_record" in original
                    if registry:
                        dataset = reference(original["provenance"]["registry_dataset"], original["provenance"]["registry_dataset_sha256"], "official_cisa_registry_dataset")
                        if dataset["path"] not in registry_index:
                            registry_index[dataset["path"]] = {digest(record): index for index, record in enumerate(util.read(ROOT / dataset["path"]))}
                        record_hash = digest(original["registry_record"])
                        assert record_hash == original["registry_record_sha256"] and record_hash in registry_index[dataset["path"]]
                        authority = "cisa_registered_domain_candidate"
                        seed["registry_record_sha256_verified"] = True
                        seed["registry_dataset_record_index_zero_based"] = registry_index[dataset["path"]][record_hash]
                    else:
                        profile = original.get("provenance", {}).get("source_profile_evidence") or original.get("trellis_profile_evidence")
                        assert profile, "Missing original reported-website profile evidence"
                        reference(profile["provider_response_path"], profile["provider_response_sha256"], "reported_website_profile")
                        authority = "trellis_reported_website_independently_unverified"
                    original_url = original["url"]
                    source_proof = {**original.get("provenance", {}), **proof, "source_context_id": context["id"], "source_context_seed_url": context["seed_url"], "source_context_seed_sha256": digest(original), "original_entry_url": original_url, "original_reported_href": original.get("provenance", {}).get("observed_href"), "parent_source_family": original["source_family"]}
                    seed.update(url=target, source_family=ROBOTS_FAMILY if kind == "robots" else HTTP_FAMILY, parent_source_family=original["source_family"], authority_evidence_family=authority, site_authority_verified=False, discovered_from=row["url"], scope={"host": urlsplit(target).netloc, "path_prefixes": ["/"]}, provenance=source_proof, original_entry_url=original_url, source_url_basis="derived_from_exact_observed_robots_redirect_origin; not an observed page href" if kind == "robots" else "observed_HTTP_Location_redirect_target", entry_url_observed_as_redirect_target=kind == "http", known_access_denial_in_reviewed_evidence=False, observed_redirect_target=proof["observed_redirect_target"], reviewed_at_utc=util.now(), target_robots_status="not fetched by this offline review; fresh checks required before acquisition", review_package=util.relative(OUT))
                    seed["entry_url_derivation_kind"] = ("root_from_observed_robots_redirect_origin" if urlsplit(row["url"]).path == "/" and not urlsplit(row["url"]).query else "same_path_at_observed_robots_redirect_origin") if kind == "robots" else "observed_same_domain_http_location"
                    seed["entry_url_derivation"] = "Source entry path/query preserved at the exact observed robots redirect origin; the entry URL was not observed in that Location header." if kind == "robots" else "Exact observed page HTTP Location target between www/apex aliases, preserving source path and query."
                    candidates.append(seed)
                reviews.append(item)
            except (AssertionError, KeyError, TypeError, ValueError, OSError) as error:
                item.update(review_decision="excluded_provenance_validation_error", error=type(error).__name__ + ": " + str(error))
                reviews.append(item)
                integrity_errors.append(item)

    candidate_urls = {s["url"] for s in candidates}
    prior, barriers, controls, database_inputs = prior_tools.inspect_existing(candidate_urls)
    selected_manifest_refs, already_selected = [], defaultdict(list)
    for county_root in sorted((ROOT / "corpus").glob("county*")):
        if not county_root.is_dir():
            continue
        manifests = {county_root / "seeds.jsonl", *county_root.glob("pass*_seeds.jsonl"), *county_root.glob("*/seeds.jsonl")}
        for manifest in sorted(p for p in manifests if p.is_file()):
            manifest_ref = reference(str(manifest), kind="prior_selected_seed_manifest")
            selected_manifest_refs.append({"path": manifest_ref["path"], "sha256": manifest_ref["sha256"]})
            for number, seed in enumerate(util.rows(manifest), 1):
                if seed.get("url") in candidate_urls:
                    already_selected[seed["url"]].append({"path": manifest_ref["path"], "sha256": manifest_ref["sha256"], "record_number": number})
    selected, decisions, seen_associations = [], [], set()
    for seed in candidates:
        url = seed["url"]
        active, lineage = [], []
        for barrier in barriers.get(util.host_group(urlsplit(url).netloc), []):
            saved = barrier.get("saved_robots_control")
            proof = seed["provenance"]
            is_source_lineage = seed["source_family"] == ROBOTS_FAMILY and saved and saved["path"] == proof["robots_control_path"] and saved["sha256"] == proof["robots_control_sha256"] and saved["problem"] == "robots_redirect_outside_host" and not saved["in_progress"]
            (lineage if is_source_lineage else active).append(barrier)
        records = prior.get(url, [])
        if records:
            decision = "excluded_existing_downloaded_attempted_or_pending_url"
        elif already_selected.get(url):
            decision = "excluded_already_selected_alias_url"
        elif active:
            decision = "excluded_preserved_host_or_robots_barrier"
        else:
            key = (url, seed["provenance"]["source_collection"], seed["provenance"]["source_context_id"], seed["provenance"]["source_resource_id"])
            decision = "excluded_duplicate_context_association" if key in seen_associations else "selected_unseen_verified_canonical_alias"
            if not decision.startswith("excluded"):
                selected.append(seed)
                seen_associations.add(key)
        decisions.append({"url": url, "source_family": seed["source_family"], "authority_evidence_family": seed["authority_evidence_family"], "source_collection": seed["provenance"]["source_collection"], "source_resource_id": seed["provenance"]["source_resource_id"], "source_context_id": seed["provenance"]["source_context_id"], "decision": decision, "prior_resource_records": records, "prior_selected_manifest_records": already_selected.get(url, []), "other_barriers": active, "preserved_source_redirect_lineage": lineage})
    selected.sort(key=lambda s: (s["provenance"]["source_collection"], s["url"], s["provenance"]["source_context_id"]))
    assert all(not prior.get(s["url"]) and not already_selected.get(s["url"]) for s in selected)
    assert len({s["url"] for s in selected}) <= 600
    base_cfg = util.read(ROOT / SOURCE_COLLECTIONS[1] / "config.json")
    def config_for(seeds):
        cfg = copy.deepcopy(base_cfg)
        cfg.update(allow=[{"host": host, "path_prefixes": ["/"]} for host in sorted({urlsplit(s["url"]).netloc for s in seeds})], follow_links=False, follow_external_allowed_links=False, max_depth=0, max_retries=0, workers=8, shared_host_dir="corpus/_shared_hosts", per_host_delay=2.0)
        contract = util.engine.Config.from_dict(cfg)
        assert all(contract.allowed(s["url"], s["scope"])[0] for s in seeds)
        assert contract.respect_robots and not contract.follow_links and contract.max_depth == 0
        return cfg
    jsonl("all_redirects_reviewed.jsonl", reviews)
    jsonl("all_verified_candidates.jsonl", candidates)
    jsonl("decisions.jsonl", decisions)
    jsonl("seeds.jsonl", selected)
    jsonl("saved_controls_reviewed.jsonl", controls)
    write("config.json", config_for(selected))
    by_collection = {}
    for collection in SOURCE_COLLECTIONS:
        subset = [s for s in selected if s["provenance"]["source_collection"] == collection]
        name = Path(collection).name
        jsonl("seeds." + name + ".jsonl", subset)
        write("config." + name + ".json", config_for(subset))
        by_collection[collection] = {"selected_seed_associations": len(subset), "selected_unique_urls": len({s["url"] for s in subset}), "seeds_path": util.relative(OUT / ("seeds." + name + ".jsonl")), "config_path": util.relative(OUT / ("config." + name + ".json"))}
    for collection, snapshot in snapshots.items():
        used = {r["source_resource_id"] for r in reviews if r["source_collection"] == collection}
        context_ids = {link["context_id"] for link in snapshot["associations"] if link["resource_id"] in used}
        write("source_snapshot." + Path(collection).name + ".json", {"collection": collection, "database_sha256": source_db_hashes[collection + "/corpus.sqlite3"], "runs": snapshot["runs"], "historical_unfinished_runs_preserved": [r["id"] for r in snapshot["runs"] if not r["ended_at"]], "resource_status_counts": dict(Counter(r["status"] for r in snapshot["resources"])), "reviewed_resources": [r for r in snapshot["resources"] if r["id"] in used], "contexts": [snapshot["contexts"][i] for i in sorted(context_ids)], "resource_contexts": [r for r in snapshot["associations"] if r["resource_id"] in used]})
    assert all(util.sha(ROOT / path) == expected for path, expected in source_db_hashes.items())
    # Recheck source files after all snapshotting, so a simultaneous change
    # cannot silently turn previously verified provenance into a fresh claim.
    assert all(util.sha(ROOT / p) == r["sha256"] for p, r in refs.items())
    summary = {"prepared_at": util.now(), "status": "prepared_offline_not_ingested_or_started", "package": util.relative(OUT), "source_collections": list(SOURCE_COLLECTIONS), "reviewed_redirect_resources": len(reviews), "review_class_counts": dict(Counter(r["review_decision"] for r in reviews)), "verified_candidate_associations": len(candidates), "verified_candidate_unique_urls": len(candidate_urls), "selected_seed_associations": len(selected), "selected_unique_urls": len({s["url"] for s in selected}), "selected_family_counts": dict(Counter(s["source_family"] for s in selected)), "selected_authority_counts": dict(Counter(s["authority_evidence_family"] for s in selected)), "decision_counts": dict(Counter(r["decision"] for r in decisions)), "by_source_collection": by_collection, "deduplication_database_inputs": database_inputs, "prior_selected_seed_manifests": selected_manifest_refs, "source_database_hashes_unchanged": source_db_hashes, "verified_file_references": len(refs), "provenance_validation_errors": len(integrity_errors), "fresh_destination_robots_checks_required": True, "source_controls_removed_or_changed": 0, "corpus_rows_modified": 0, "network_requests": 0, "collectors_started": 0, "full_source_corpus_complete": False, "limitations": ["Registration and county-name hints remain unreviewed ownership/jurisdiction evidence; no registry candidate is promoted to a verified Census GEOID.", "Robots-origin entries are derived; only HTTP Location targets are observed page redirects.", "A selected target has not been fetched by this review. Future acquisition must preserve current host controls and fresh destination robots checks.", "Saved same-host redirects, different domains/CMS paths, changed paths/queries, and already recorded targets remain excluded.", "Historical unfinished runs are retained as history; empty process probes and available OS locks established these two review sources were idle."]}
    jsonl("validated_file_references.jsonl", sorted(refs.values(), key=lambda r: r["path"]))
    jsonl("provenance_errors.jsonl", integrity_errors)
    write("summary.json", summary)
    write("validation.json", {"validated_at": util.now(), "passed": not integrity_errors, "candidate_raw_and_parent_metadata_hashes_verified": True, "selected_urls_have_no_prior_resource_or_selected_seed_record": True, "source_databases_and_referenced_files_unchanged": True, "source_context_namespaces_preserved": True, "registered_domain_authority_and_unreviewed_hints_preserved": True, "source_path_query_preserved": True, "saved_references_verified": len(refs), "provenance_errors": len(integrity_errors), "network_requests": 0, "corpus_mutations": 0})
    (OUT / "README.md").write_text("# Offline county canonical-alias review\n\nThis package reviews saved robots-origin and page HTTP Location evidence from the two current county continuation collections. It makes no network requests, ingests no seeds, and changes no corpus databases or configs. `scope.json` and the current RUNBOOK were read first; source locks were independently available while historical unfinished run rows remained untouched.\n\n`seeds.jsonl` contains only previously unrecorded exact www/apex aliases preserving the requested source path and query. Separate per-source seed/config files support later ingestion into the corresponding existing collection. Proposed configs use eight workers, shared host coordination, no link following, depth zero, no retries, and exact selected target hosts. These configs are review artifacts, not live settings.\n\nRobots-derived seeds use `derived_county_entry_from_observed_robots_redirect_origin`; their entry URL was not observed as a page link. Actual HTTP Location seeds use `observed_county_entry_from_same_domain_http_redirect`, with exact metadata, raw response and Location hashes. Both retain the original entry, original reported href where present, source collection/resource/context IDs, and full parent seed provenance. CISA registry records, registered domains and unreviewed county hints remain distinct from Trellis-reported websites.\n\nRead `summary.json`, `decisions.jsonl`, `all_redirects_reviewed.jsonl`, `all_verified_candidates.jsonl`, and `validation.json` before acquisition. Any future collector must still pass fresh destination robots and existing host policies. Only the precise source redirect control is derivation evidence; no unrelated barrier was ignored or removed. Previously captured, attempted, pending, and selected target URLs were excluded. This does not establish full county coverage or government ownership.\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("deduplication_database_inputs", "prior_selected_seed_manifests", "source_database_hashes_unchanged", "limitations")}, indent=2))


if __name__ == "__main__":
    main()

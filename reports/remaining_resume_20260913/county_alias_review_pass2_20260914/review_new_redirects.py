"""Freeze an offline delta review; this program neither fetches nor ingests."""
from collections import Counter, defaultdict
from contextlib import closing
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PRIOR = ROOT / "reports/remaining_resume_20260913/county_alias_review_20260914"
COLLECTIONS = (
    "corpus/county_registry_continuation_20260913",
    "corpus/county_entries_continuation_20260913",
)
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_county_entries_resume_20260913 as util
import prepare_county_entries_resume_pass2_20260913 as prior_tools


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jsonl(name, values):
    (OUT / name).write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in values), encoding="utf-8")


def main():
    assert not (OUT / "summary.json").exists(), "Frozen review must not be regenerated"
    started = util.now()
    refs = {}

    def ref(value, expected=None, kind="evidence"):
        path = (ROOT / value).resolve()
        assert path.is_relative_to(ROOT) and path.is_file(), str(value)
        key = util.relative(path)
        if key not in refs:
            refs[key] = {"path": key, "sha256": util.sha(path), "bytes": path.stat().st_size, "kinds": []}
        result = refs[key]
        assert expected is None or result["sha256"] == expected, key + " hash mismatch"
        if kind not in result["kinds"]:
            result["kinds"].append(kind)
        return dict(result)

    for p in (ROOT / "reports/remaining_resume_20260913/scope.json", ROOT / "RUNBOOK.md"):
        ref(p, kind="scope_read_at_review_start")
    assert util.read(ROOT / "reports/remaining_resume_20260913/scope.json")["latest_user_direction"] == "Continue official sources only"
    prior_summary = util.read(PRIOR / "summary.json")
    for n in ("summary.json", "all_redirects_reviewed.jsonl", "integration/root_review.json", "integration/deferred_chain_associations.jsonl"):
        ref(PRIOR / n, kind="frozen_prior_review")
    old_reviews = {(r["source_collection"], r["source_resource_id"]): r for r in util.rows(PRIOR / "all_redirects_reviewed.jsonl")}

    probe_cmd = "Get-CimInstance Win32_Process -Filter \"Name = 'python.exe'\" | Where-Object { $_.CommandLine -like '*corpus_crawler.py*' -and ($_.CommandLine -like '*county_entries_continuation_20260913*' -or $_.CommandLine -like '*county_registry_continuation_20260913*') } | Select-Object ProcessId,CreationDate | ConvertTo-Json -Compress"
    process = subprocess.run(["powershell", "-NoProfile", "-Command", probe_cmd], capture_output=True, text=True, check=True)
    assert not process.stdout.strip(), "A reviewed collector is running"
    process_evidence = {"observed_at": util.now(), "query": probe_cmd, "exit_code": process.returncode, "matching_processes": [], "lock_checks": []}
    snapshots, source_files, changes, pending = {}, {}, [], []
    unchanged_control_checks = []
    for collection in COLLECTIONS:
        base = ROOT / collection
        for p in (base / "corpus.sqlite3", base / "config.json"):
            source_files[util.relative(p)] = ref(p, kind="stable_source_before_review")
        lock = base / ".crawler.lock"
        assert lock.is_file() and lock.stat().st_size > 0
        lock_sha = util.sha(lock)
        with util.engine.run_lock(base):
            pass
        assert util.sha(lock) == lock_sha
        process_evidence["lock_checks"].append({"collection": collection, "observed_at": util.now(), "exclusive_lock_available": True, "lock_sha256_before_and_after": lock_sha})
        old_path = PRIOR / ("source_snapshot." + base.name + ".json")
        ref(old_path, kind="prior_source_snapshot")
        old = {r["id"]: r for r in util.read(old_path)["reviewed_resources"]}
        with closing(util.db_read(base / "corpus.sqlite3")) as db:
            resources = [dict(r) for r in db.execute("SELECT * FROM resources ORDER BY id")]
            contexts = {r["id"]: dict(r) for r in db.execute("SELECT * FROM contexts")}
            associations = [dict(r) for r in db.execute("SELECT * FROM resource_contexts")]
            runs = [dict(r) for r in db.execute("SELECT id,started_at,ended_at,stop_reason,processed FROM runs ORDER BY rowid")]
            fetches = {r["id"]: dict(r) for r in db.execute("SELECT * FROM fetches")}
        assert not any(r["status"] == "fetching" for r in resources)
        snapshots[collection] = dict(resources=resources, contexts=contexts, associations=associations, runs=runs, fetches=fetches)
        for row in resources:
            if row["status"] == "pending":
                pending.append({"source_collection": collection, "resource": row})
            if row["status"] not in ("redirect", "robots_redirect_outside_host"):
                continue
            previous = old.get(row["id"])
            reasons = []
            if previous is None:
                reasons.append("resource_not_in_frozen_redirect_snapshot")
            elif (previous["status"], previous["last_fetch_id"]) != (row["status"], row["last_fetch_id"]):
                reasons.append("status_or_fetch_changed")
            old_proof = old_reviews.get((collection, row["id"]), {}).get("provenance", {})
            if previous and old_proof.get("robots_control_path"):
                p = ROOT / old_proof["robots_control_path"]
                actual = util.sha(p) if p.is_file() else None
                unchanged_control_checks.append({"source_collection": collection, "source_resource_id": row["id"], "path": old_proof["robots_control_path"], "prior_sha256": old_proof["robots_control_sha256"], "current_sha256": actual, "unchanged": actual == old_proof["robots_control_sha256"]})
                if actual != old_proof["robots_control_sha256"]:
                    reasons.append("saved_robots_control_changed")
            if reasons:
                changes.append((collection, row, reasons))

    def capture_proof(collection, row, kind):
        base = ROOT / collection
        metadata_ref = ref(base / row["metadata_path"], kind=kind + "_metadata")
        meta = util.read(ROOT / metadata_ref["path"])
        fetch = snapshots[collection]["fetches"][row["last_fetch_id"]]
        assert meta["requested_url"] == row["url"]
        assert meta["fetch_id"] == fetch["id"] == row["last_fetch_id"]
        assert meta == json.loads(fetch["response_json"])
        assert fetch["resource_id"] == row["id"] and meta["status"] == row["status"]
        proof = {"source_collection": collection, "source_resource_id": row["id"], "source_entry_url": row["url"], "source_fetch_id": fetch["id"], "source_fetch_row": fetch, "source_fetch_row_sha256": digest(fetch), "parent_metadata_path": metadata_ref["path"], "parent_metadata_sha256": metadata_ref["sha256"], "fetched_at": meta["fetched_at"]}
        if row["raw_path"]:
            raw = ref(base / row["raw_path"], row["sha256"], kind + "_raw")
            assert raw["sha256"] == meta["sha256"] == fetch["sha256"]
            assert raw["bytes"] == row["byte_count"] == meta["byte_count"] == fetch["byte_count"]
            assert bool(row["raw_complete"]) == bool(meta["raw_complete"]) == bool(fetch["raw_complete"])
            proof.update(raw_path=raw["path"], raw_sha256=raw["sha256"], raw_bytes=raw["bytes"], raw_complete=bool(row["raw_complete"]))
        if row.get("text_path"):
            proof["text_file"] = ref(base / row["text_path"], kind=kind + "_text")
        return proof, meta

    registry_indexes = {}
    def authority_proofs(collection, row):
        snap = snapshots[collection]
        result = []
        for link in snap["associations"]:
            if link["resource_id"] != row["id"]:
                continue
            context = snap["contexts"][link["context_id"]]
            seed = json.loads(context["seed_json"])
            # This exact delta consists only of registry contexts. Reject any
            # unrecognized lineage instead of inferring county authority.
            assert "registry_record" in seed and seed.get("court_fips_association_verified") is False
            assert seed.get("county_name_association") == "UNREVIEWED" and not seed.get("site_authority_verified")
            assert not seed["jurisdiction"].get("geoid")
            domain = seed["registered_domain"].lower()
            assert domain != "washingtoncopa.gov", "Held ancestral context must remain excluded"
            assert util.host_group(urlsplit(row["url"]).hostname) == util.host_group(domain)
            original = seed.get("original_entry_url", seed["url"])
            assert util.host_group(urlsplit(original).hostname) == util.host_group(domain)
            dataset = ref(seed["provenance"]["registry_dataset"], seed["provenance"]["registry_dataset_sha256"], "cisa_registry_dataset")
            if dataset["path"] not in registry_indexes:
                registry_indexes[dataset["path"]] = {digest(x): i for i, x in enumerate(util.read(ROOT / dataset["path"]))}
            rhash = digest(seed["registry_record"])
            assert rhash == seed["registry_record_sha256"] and rhash in registry_indexes[dataset["path"]]
            assert seed["registry_record"]["domain"].lower() == domain
            p = seed["provenance"]
            for path_key, hash_key in (("parent_metadata_path", "parent_metadata_sha256"), ("raw_path", "raw_sha256"), ("robots_control_path", "robots_control_sha256")):
                if p.get(path_key):
                    ref(p[path_key], p[hash_key], "ancestral_seed_evidence")
            for r in p.get("robots_observation_raw_refs", []):
                ref(r["path"], r["sha256"], "ancestral_robots_raw")
            for raw_path in p.get("registry_evidence_paths", []):
                ref(ROOT / "sources/official_courts" / raw_path, kind="original_cisa_registry_response")
            result.append({"source_collection": collection, "source_context_id": context["id"], "source_context_seed_url": context["seed_url"], "source_context_seed_sha256": digest(seed), "source_context_seed": seed, "original_entry_url": original, "authority_evidence_family": "cisa_registered_domain_candidate", "registered_domain": domain, "registry_record_sha256_verified": rhash, "registry_dataset_record_index_zero_based": registry_indexes[dataset["path"]][rhash], "site_authority_verified": False, "county_geography_association": "UNREVIEWED", "cross_domain_ancestry_promoted": False})
        assert result
        return result

    reviews = []
    for collection, row, reasons in changes:
        proof, meta = capture_proof(collection, row, "new_source")
        item = {"source_collection": collection, "source_resource_id": row["id"], "source_url": row["url"], "source_status": row["status"], "delta_reasons": reasons, "provenance": proof, "authority_contexts": authority_proofs(collection, row), "candidate_entry_url": None}
        if row["status"] == "redirect":
            location = meta["headers"]["location"]
            target = util.engine.canonical_url(urljoin(row["url"], location))
            assert meta["http_status"] in (301, 302, 303, 307, 308) and meta["raw_complete"]
            assert target == row["redirect_url"] == meta["redirect_url"]
            assert urlsplit(target).hostname == urlsplit(row["url"]).hostname
            item.update(evidence_kind="observed_HTTP_Location", literal_location=location, observed_redirect_target=target, candidate_entry_url=target, entry_url_observed_as_redirect_target=True, hostname_relation="same_host", path_query_preserved=(urlsplit(target).path, urlsplit(target).query) == (urlsplit(row["url"]).path, urlsplit(row["url"]).query))
            proof.update(http_status=meta["http_status"], location_header=location, observed_redirect_target=target, redirect_metadata_path=proof["parent_metadata_path"], redirect_metadata_sha256=proof["parent_metadata_sha256"])
        else:
            source = urlsplit(row["url"])
            origin = source.scheme + "://" + source.netloc
            control_path = ROOT / collection / "controls/robots" / (hashlib.sha256(origin.encode()).hexdigest() + ".json")
            control_ref = ref(control_path, kind="new_robots_control")
            control = util.read(control_path)
            assert control["origin"] == origin and control["problem"] == "robots_redirect_outside_host" and not control.get("in_progress")
            observations = []
            for observation in control["observations"]:
                raw = ref(ROOT / collection / observation["raw_path"], observation["sha256"], "new_robots_response")
                assert observation["raw_complete"] and raw["bytes"] == observation["byte_count"]
                literal = observation["headers"].get("location")
                observations.append({"saved_observation": observation, "saved_observation_sha256": digest(observation), "raw_file": raw, "literal_location": literal, "resolved_location": util.engine.canonical_url(urljoin(observation["requested_url"], literal)) if literal else None})
            assert observations and not any(o["saved_observation"].get("http_status") in (401,403,429) for o in observations)
            last = observations[-1]
            assert util.host_group(urlsplit(last["resolved_location"]).hostname) != util.host_group(source.hostname)
            item.update(evidence_kind="robots_redirect_origin_evidence", entry_url_observed_as_redirect_target=False, robots_entry_derivation_performed=False, literal_location=last["literal_location"], observed_redirect_target=last["resolved_location"], hostname_relation="different_domain", review_decision="excluded_external_CMS_robots_redirect")
            proof.update(robots_control_path=control_ref["path"], robots_control_sha256=control_ref["sha256"], robots_control_checked_at=control["checked_at"], robots_observation_chain=observations)
        reviews.append(item)

    urls = {r["source_url"] for r in reviews} | {r["candidate_entry_url"] for r in reviews if r["candidate_entry_url"]} | {r["resource"]["url"] for r in pending}
    prior, barriers, controls, db_inputs = prior_tools.inspect_existing(urls)
    for control in controls:
        ref(control["path"], control["sha256"], "preserved_host_control")
    prior_manifests = set(PRIOR.glob("seeds*.jsonl")) | {PRIOR / "integration/reviewed_seeds.jsonl"}
    for base in sorted((ROOT / "corpus").glob("county*")):
        if base.is_dir():
            prior_manifests.update(p for p in base.rglob("*seeds*.jsonl") if p.is_file())
    # Include earlier staged alias/website packages, even if never ingested.
    for pattern in ("county*/*seeds*.jsonl", "county*/**/*seeds*.jsonl", "county*/canonical_entry_candidates.jsonl"):
        prior_manifests.update((ROOT / "reports/geography").glob(pattern))
    selected_matches = defaultdict(list)
    manifest_refs = []
    for p in sorted(prior_manifests):
        receipt = ref(p, kind="prior_seed_or_staged_alias_manifest")
        manifest_refs.append(receipt)
        for number, seed in enumerate(util.rows(p), 1):
            if seed.get("url") in urls:
                selected_matches[seed["url"]].append({"path": receipt["path"], "sha256": receipt["sha256"], "record_number": number})

    for item in reviews:
        target = item["candidate_entry_url"]
        relevant_url = target or item["source_url"]
        item["preserved_barriers"] = barriers.get(util.host_group(urlsplit(relevant_url).hostname), [])
        item["prior_seed_matches"] = selected_matches.get(relevant_url, [])
        if not target:
            continue
        item["prior_url_records"] = prior.get(target, [])
        saved = [r for r in item["prior_url_records"] if r["status"] == "downloaded"]
        denied = [r for r in item["prior_url_records"] if r["status"] == "forbidden"]
        assert saved or denied, "Unexpected uncaptured new endpoint requires a fresh review"
        item["target_capture_proofs"] = []
        for record in saved + denied:
            collection = str(Path(record["database"]).parent).replace("\\", "/")
            full_row = next(r for r in snapshots[collection]["resources"] if r["id"] == record["id"])
            target_proof, target_meta = capture_proof(collection, full_row, "already_recorded_target")
            assert target_meta["requested_url"] == target
            target_proof.update(status=full_row["status"], http_status=target_meta["http_status"])
            item["target_capture_proofs"].append(target_proof)
        if saved:
            assert all(p["raw_bytes"] > 0 for p in item["target_capture_proofs"] if p["status"] == "downloaded")
            item["review_decision"] = "excluded_already_downloaded_target"
        else:
            assert all(p["http_status"] == 403 for p in item["target_capture_proofs"])
            assert any(b.get("pause_reason") == "forbidden" for b in item["preserved_barriers"])
            item["review_decision"] = "excluded_already_attempted_403_target"

    gaps = []
    for item in reviews:
        if item["review_decision"] != "excluded_already_downloaded_target":
            gaps.append({"source_collection": item["source_collection"], "source_resource_id": item["source_resource_id"], "source_url": item["source_url"], "target": item["observed_redirect_target"], "gap": item["review_decision"], "new_redirect_delta_member": True, "evidence_record": util.relative(OUT / "new_redirects_reviewed.jsonl"), "preserved_barriers": item["preserved_barriers"]})
    for item in pending:
        row = item["resource"]
        held = barriers.get(util.host_group(urlsplit(row["url"]).hostname), [])
        assert any(b.get("pause_reason") == "forbidden" for b in held)
        gaps.append({**item, "gap": "existing_pending_behind_forbidden_host", "new_redirect_delta_member": False, "resource_row_sha256": digest(row), "preserved_barriers": held, "action": "Retain pending row and host pause; no retry or acquisition"})
    held_path = PRIOR / "integration/deferred_chain_associations.jsonl"
    held_records = util.rows(held_path)
    assert len(held_records) == 1 and "washingtoncopa.gov" in json.dumps(held_records)
    write("held_associations_preserved.json", {"input": ref(held_path), "records": held_records, "reconsidered": False, "promoted_to_verified_authority": False, "included_in_new_redirect_denominator": False})

    counts = Counter(r["review_decision"] for r in reviews)
    # Guard this snapshot against accidental scope expansion or false exhaustion.
    assert len(reviews) == 15 and counts == {"excluded_already_downloaded_target": 12, "excluded_already_attempted_403_target": 1, "excluded_external_CMS_robots_redirect": 2}
    assert all(r["source_collection"] == COLLECTIONS[0] for r in reviews)
    assert len(pending) == 1 and all(x["unchanged"] for x in unchanged_control_checks)
    assert all(util.sha(ROOT / p) == receipt["sha256"] for p, receipt in source_files.items())
    # Scope and RUNBOOK may legitimately change while root publishes; retain
    # their start receipts without asserting shared documentation is immutable.
    for p, receipt in refs.items():
        if "scope_read_at_review_start" not in receipt["kinds"]:
            assert util.sha(ROOT / p) == receipt["sha256"], "Evidence changed during review: " + p

    jsonl("new_redirects_reviewed.jsonl", reviews)
    jsonl("excluded_endpoints.jsonl", [{k: v for k, v in r.items() if k not in ("authority_contexts", "provenance", "target_capture_proofs")} for r in reviews])
    jsonl("remaining_gaps.jsonl", gaps)
    jsonl("seeds.jsonl", [])
    jsonl("candidate_seeds.jsonl", [])
    jsonl("unchanged_robots_controls.jsonl", unchanged_control_checks)
    jsonl("saved_controls_preserved.jsonl", controls)
    write("source_process_and_lock_checks.json", process_evidence)
    write("deduplication_inputs.json", {"observed_at": util.now(), "exact_urls_checked": sorted(urls), "database_reads": db_inputs, "prior_manifests": manifest_refs, "all_county_database_resource_states_excluded": True, "shared_barriers_removed": 0, "snapshot_only": True})
    for collection, snap in snapshots.items():
        ids = {r["source_resource_id"] for r in reviews if r["source_collection"] == collection}
        ids.update(r["resource"]["id"] for r in pending if r["source_collection"] == collection)
        cids = {a["context_id"] for a in snap["associations"] if a["resource_id"] in ids}
        write("source_snapshot." + Path(collection).name + ".json", {"collection": collection, "observed_at": util.now(), "database": source_files[collection + "/corpus.sqlite3"], "resource_count": len(snap["resources"]), "resource_status_counts": dict(Counter(r["status"] for r in snap["resources"])), "reviewed_resources": [r for r in snap["resources"] if r["id"] in ids], "contexts": [snap["contexts"][i] for i in sorted(cids)], "resource_contexts": [a for a in snap["associations"] if a["resource_id"] in ids], "runs": snap["runs"], "historical_unfinished_runs_preserved": [r["id"] for r in snap["runs"] if r["ended_at"] is None]})
    write("proposed_additive_config.json", {"artifact_kind": "additive_config_proposal_not_a_replacement_config", "apply_required": False, "reason": "No newly eligible exact endpoints", "base_configs": [source_files[c + "/config.json"] for c in COLLECTIONS], "allow_additions": [], "seed_additions": [], "existing_values_to_change": {}, "follow_links": False, "max_depth": 0, "maximum_new_endpoints_authorized": 100, "selected_endpoints": 0, "barrier_mutations": [], "collector_launch_required": False})
    summary = {"started_at": started, "prepared_at": util.now(), "status": "frozen_no_new_eligible_endpoints", "prior_review": util.relative(PRIOR), "prior_review_prepared_at": prior_summary["prepared_at"], "scope": "Only changed or newly unresolved saved county entry redirects since the frozen prior review", "new_redirect_resources": len(reviews), "new_redirect_resources_by_collection": {c: sum(r["source_collection"] == c for r in reviews) for c in COLLECTIONS}, "evidence_kind_counts": dict(Counter(r["evidence_kind"] for r in reviews)), "review_decision_counts": dict(counts), "new_seed_associations": 0, "new_exact_endpoints": 0, "prior_robots_controls_rechecked": len(unchanged_control_checks), "prior_robots_controls_changed": 0, "held_ancestral_associations_preserved": len(held_records), "pending_gaps_preserved": len(pending), "gap_records": len(gaps), "source_databases_and_configs_unchanged": True, "network_requests": 0, "collectors_started": 0, "corpus_mutations": 0, "full_county_corpus_complete": False, "limitations": ["The reviewed delta is exhausted; nationwide county coverage is not complete.", "Twelve observed HTTP targets were already downloaded. One returned 403 and remains paused. No target is retried.", "Two robots chains leave the registered host for external CMS domains; no site endpoint was invented from those targets.", "CISA registration evidence and county hints remain unreviewed site/jurisdiction associations. No cross-domain ancestry is promoted.", "The existing Leon pending row remains behind a forbidden-host barrier; it is not a newly discovered redirect.", "The held washingtoncopa.gov ancestral association remains separate and excluded.", "Source HTTP redirect bodies may legitimately contain zero bytes. They are response evidence, not content-bearing pages."]}
    write("summary.json", summary)
    jsonl("validated_file_references.jsonl", sorted(refs.values(), key=lambda r: r["path"]))
    write("validation.json", {"validated_at": util.now(), "passed": True, "new_redirects_validated": len(reviews), "raw_metadata_fetch_row_consistency_verified": True, "original_registry_and_context_hashes_verified": True, "already_recorded_target_hashes_verified": 13, "nonempty_successful_target_bodies": 12, "forbidden_target_bodies_preserved": 1, "source_databases_and_configs_unchanged": True, "changed_old_controls": 0, "held_ancestry_not_selected": True, "new_endpoint_count": 0, "maximum_endpoint_bound": 100, "verified_file_references": len(refs), "validation_errors": 0, "row_hash_serialization": "SHA256 of sorted-key compact ensure_ascii=False UTF-8 JSON", "file_hash_basis": "SHA256 of exact saved bytes"})
    (OUT / "README.md").write_text("# Offline county redirect delta review\n\nNo new acquisition endpoints qualify. The 15 newly unresolved rows since the frozen first review contain 13 actual HTTP Location redirects: 12 destinations already downloaded and one already returned 403. Two further robots chains leave the registered county domain for external Revize CMS hosts. No entry URL was derived from those external hosts.\n\n`new_redirects_reviewed.jsonl` retains literal Locations, complete robots response chains, raw and metadata hashes, source fetch-row hashes, namespaced contexts, original registered domains and unreviewed geography hints. Actual HTTP evidence remains distinct from robots-origin evidence. `excluded_endpoints.jsonl` provides compact decisions; `remaining_gaps.jsonl` preserves the Rooks 403, two external CMS robots gaps, and the pre-existing Leon pending/forbidden-host gap. The held washingtoncopa.gov ancestral association is preserved separately and excluded from both selection and the new-redirect denominator.\n\n`seeds.jsonl` and `candidate_seeds.jsonl` are intentionally empty. `proposed_additive_config.json` is a no-op proposal, not a replacement crawler config. Do not ingest, launch, reset, or retry anything for this package. Existing source databases, configs, controls, archive captures, index and delivery were not modified. No network requests were made.\n\nThe review compares prior resource IDs/status/fetches and existing saved robots-control hashes. It checks exact URLs against all generic corpus resource states, the shared host coordinator, saved catalog records, and prior county seed/staging manifests. Locks and process observations distinguish stopped collectors from historical unfinished run rows. Scope/RUNBOOK receipts are start-of-review observations because root may publish concurrently.\n\n`validation.json`, `validated_file_references.jsonl`, `deduplication_inputs.json`, source snapshots and `output_manifest.json` are the audit trail. This exhausts only the specified saved-redirect delta, not the nationwide county corpus. The immutable report can be reproduced in a new review directory after adjusting its explicit snapshot guard; do not rerun over this frozen directory.\n", encoding="utf-8")
    write("output_manifest.json", {"created_at": util.now(), "files": [{"path": util.relative(p), "bytes": p.stat().st_size, "sha256": util.sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "output_manifest.json"]})
    print(json.dumps({"status": summary["status"], "new_redirect_resources": len(reviews), "decisions": counts, "new_exact_endpoints": 0, "verified_file_references": len(refs), "package": util.relative(OUT)}, indent=2))


if __name__ == "__main__":
    main()

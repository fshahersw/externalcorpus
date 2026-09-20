# Geography reconciliation and county website queues

This is an offline reconciliation of the captured Trellis catalog with the saved 2026 Census county baseline. No website was fetched and no collector was launched to create these reports. `summary.json` identifies the input snapshots and SHA-256 hashes; the exact input bytes are retained under `input_snapshots/`.

The captured snapshot contains 374 Trellis profiles and a Census baseline of 3,144 counties or county equivalents across the 50 states and DC. It yields 362 clear name matches, two ambiguous profiles, and ten court scopes that do not identify a current Census county equivalent. A missing Census geography means it was not matched in this snapshot; it does not mean Trellis or an official site lacks that county's records.

## Tables

Every table is available as CSV and JSONL. JSONL retains nested provenance and string FIPS codes.

| File stem | Meaning |
| --- | --- |
| `county_reconciliation` | Every observed profile, source identity, Census candidates and final decision |
| `county_matches` | Clear state/name associations, including the exact Census GEOID |
| `county_ambiguities` | Conflicting names or entity types; no assigned GEOID |
| `county_unmatched` | Observed court scopes without a current county-equivalent match |
| `non_census_jurisdictions` | Historical Connecticut counties, Delaware Chancery and the federal Supreme Court scope |
| `census_counties_missing` | Every baseline geography without a clear matched profile in this snapshot |
| `state_coverage` | Per-state denominator, observed profiles and matched/missing counts |
| `county_aliases` | State-specific source slugs, official names and normalization methods |
| `duplicate_geographies` | Multiple source profiles sharing one matched GEOID, if present |
| `website_associations` | Website observations, recovered display text, county match and authority classification |
| `website_issues` | Missing/invalid links or unresolved geography preventing a seed |
| `official_county_website_seeds` | Website URLs attached only to clear county-name matches |

The two ambiguous records are retained explicitly: the Florida `jackson` URL has a title naming Washington County, and the Florida `sarasota` URL has a title naming Manatee County. The script does not choose a FIPS code when the URL and title conflict.

Eight historical Connecticut counties remain separate from the nine 2026 planning regions; no geographic crosswalk was guessed. Virginia independent cities remain a distinct Census entity type. Names such as Richmond can identify both a county and a city, so an explicit entity type is required when there are multiple candidates. Judicial-circuit prefixes in otherwise clear county titles are retained as `source_court_scope` and do not replace the county identity. The Delaware Court of Chancery and federal Supreme Court entries remain court scopes with no county GEOID.

Matching uses exact state and normalized county names, ordinary punctuation/spacing differences and explicit St./Saint or Ste./Sainte spelling variants. It does not use edit distance, geographic proximity, substring selection or an assumed historical-to-current crosswalk.

## Website extraction and authority

`scripts/build_catalog.py` now selects the observed link target in the Website field. The former shortened/corrupted display value remains in `official_website_display`, `fields_json`, and exported provenance. The catalog snapshot recovered 151 shortened display URLs from actual saved HTML hrefs. Its extraction version is `2-website-href`; unchanged source files are reprocessed when the extraction version changes. Multiple distinct field hrefs and invalid links remain explicit issues.

The clear-match queue contains 360 county/URL associations representing 330 unique URLs. All are classified `trellis_reported_government_site`; **none is promoted to `verified_government_site` merely because the county name matched Census or the hostname ends in `.gov`**. Some Website fields point to shared judicial-circuit sites or non-`.gov` domains. `site_authority_verified` remains false pending independent verification. A successful geography join establishes the name association, not current website ownership, court authority, case coverage or site content.

The separate config `official_county_websites.config.json` permits only the observed hosts and starts with `follow_links=false` and `max_depth=0`. Seeds retain their exact observed host scopes. A redirect to another host remains unresolved until reviewed and explicitly allowed.

These are preparation commands; they do not fetch websites:

```powershell
python scripts/build_catalog.py
python reports/geography/reconcile_counties.py
python reports/geography/prepare_cisa_county_entries.py
python -m unittest discover -s reports/geography -p 'test_*.py' -v
```

An operator can ingest the clear-match queue into a separate corpus and run a bounded public fetch:

```powershell
python pipeline/corpus_crawler.py --root corpus/county_websites_matched ingest --seeds reports/geography/official_county_website_seeds.jsonl --config reports/geography/official_county_websites.config.json
python pipeline/corpus_crawler.py --root corpus/county_websites_matched run --max-pages 100 --max-seconds 600
python pipeline/corpus_crawler.py --root corpus/county_websites_matched export
```

## Independent CISA registry entry queue

`cisa_county_entries/` is a separate nationwide queue based on the saved official `.gov` registry dataset. It is not merged with the Trellis/Census matches.

The registry has 2,676 distinct county-category domains. The preparation snapshot includes 2,673 entry URLs and excludes three exact URLs already in an active official queue. `domain_decisions.csv` and `.jsonl` account for every registration. `exclusion_snapshot.jsonl` records captured exact URLs, active queued exact URLs and known paused/access-denied hosts from the official collections, with evidence references. The registry source hash and inspected collections appear in `cisa_county_entries/summary.json`.

Each entry is `https://registered-domain/`, explicitly labeled `registry-derived-site-entry`. The HTTPS scheme and root path are deterministic entry choices derived from the registered domain, not a claim that the exact URL was observed on an already fetched website. The domain's registry organization and state are preserved. Upstream county-name/FIPS hints are retained only as `UNREVIEWED` metadata and never copied into a verified county or court assignment.

`cisa_county_entries/config.json` permits only the included registered hosts and their `www` counterparts, with `follow_links=false`, `max_depth=0`, bounded retries, robots handling and a 2 GiB disk floor. Per-seed host pairs are preserved in `allowed_registered_www_hosts`.

The current crawler enforces the shared global allowlist. It cannot enforce a different host pair for every seed: a redirect to another registered domain that is globally allowed may be fetched. Every destination outside that seed's recorded pair must be reviewed and cannot promote the seed to a verified county mapping. Destinations outside the global allowlist remain recorded, unfetched redirects. Redirects and robots requests can require additional HTTP requests beyond the one entry URL per registration.

Refresh the exclusion snapshot immediately before ingestion because other collections may be progressing:

```powershell
python reports/geography/prepare_cisa_county_entries.py
python pipeline/corpus_crawler.py --root corpus/county_gov_registry_entries ingest --seeds reports/geography/cisa_county_entries/seeds.jsonl --config reports/geography/cisa_county_entries/config.json
python pipeline/corpus_crawler.py --root corpus/county_gov_registry_entries run --max-pages 100 --max-seconds 600
python pipeline/corpus_crawler.py --root corpus/county_gov_registry_entries export
```

Ten local fixtures cover shortened Website display text versus the full href, version-triggered re-extraction, ambiguous hrefs, county/city collisions, Connecticut planning regions, special court scopes, source-title conflicts, explicit spelling aliases and exact-URL/paused-host queue exclusions. No fixture uses network access.

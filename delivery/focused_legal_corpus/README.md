# Focused legal corpus package

Snapshot updated on 2026-09-18T16:50:18.240723+00:00. The official-only continuation has saved **3,885 responses**, with **3,661 nonempty collector text files** and **182 verified offline document text derivatives**. **3,843 saved responses have indexed searchable text** through either representation. Collection continues through the paced reviewed queues. The full nationwide corpus remains incomplete.

| Component | Saved scope | Files |
|---|---|---|
| Official laws | 10,669 source URL entries, including directories and ancillary material | [CSV](laws/official_resources.csv) · [JSONL](laws/official_resources.jsonl) · [Guide](laws/README.md) |
| Trellis laws | 1,418 previously saved representations; acquisition deferred | [JSONL](laws/trellis_law_captures.jsonl) |
| Judges | Previously saved official roster/profile evidence | [CSV](judges/sources.csv) · [Guide](judges/README.md) |
| Counties | 3,144 Census county-equivalent rows across 50 states and DC, linked to saved profile/website evidence where available | [CSV](counties/counties.csv) · [JSONL](counties/counties.jsonl) · [Guide](counties/README.md) |
| County local resources | Local rules, court/clerk pages, filing guidance, forms and county data with explicit source and geographic evidence | [Guide](county_local_resources/README.md) · [Ledger](county_local_resources/county_ledger.jsonl) · [Captures](county_local_resources/captures.jsonl) |

The package contains **16,454 capture records** and **15,837 distinct searchable texts**. Original response bytes, extracted text, timestamps and hashes remain in the workspace under `sources/` and `corpus/`.

```powershell
python -X utf8 delivery/focused_legal_corpus/search.py "due process" --exact --group laws
python -X utf8 delivery/focused_legal_corpus/search.py "Cocke" --group counties
```

[Official continuation results](official_expansion_20260913/summary.json) · [Per-URL outcomes](official_expansion_20260913/outcomes.jsonl) · [Previous paid expansion](expansion_20260913/summary.json).

County inventory coverage does not mean every county's content is downloaded. 1,421 rows have clear saved Trellis profile matches. Reported websites, registered government domains, derived origins and observed HTTP redirects retain separate evidence. Agency or district government sites are not automatically county-court websites, and geographic candidates are not verified assignments. Empty responses and files without usable text remain explicit in the capture metadata.

Law source entries include navigation, historical editions and ancillary material. Saved text does not establish complete current law. [Law coverage](laws/jurisdiction_coverage.csv) · [Law gaps](laws/official_resource_gaps.csv) · [County website evidence](counties/website_evidence.csv). Trellis and Firecrawl collection remain deferred under the user's official-only direction; this continuation made no paid requests.

[Summary](summary.json) · [Validation](validation.json) · [File hashes](package_files.json) · [Search selection](focused.sqlite3). Keep this folder within the workspace because it references original files and the shared text index. Retain GEOID/FIPS fields as strings.

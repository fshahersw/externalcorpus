# Aggregated legal dataset quality requirements

The user's priority is a valuable, high-quality eventual aggregated dataset. Acquisition is still active. A large URL count or a completed finite batch is not a completion criterion.

The release will aggregate the existing searchable archive with the new official state-law and county-local collections. It will retain source records, document versions, geographic associations, text representations, and unresolved gaps separately.

## Required record evidence

- Preserve the requested and final source URLs, publisher/site, retrieval time, response status, original file, metadata file, and SHA-256 hashes. Every extracted or OCR text file must bind to its original bytes.
- Keep state, county GEOID/FIPS, court name, and the evidence for their association. County equivalents are geography, not necessarily court jurisdictions. Ambiguous municipal, district, multi-county, and agency matches remain unresolved.
- Distinguish statutes, constitutions, statewide rules, local rules, enacted ordinances, proposed ordinances, standing orders, forms, filing guidance, record-search portals, actual filed documents, and general government information. Link-based categories are candidates until content supports them.
- Retain publisher dates, effective/repeal dates, editions, and source labels only when observed. A recent download does not establish that a document is current law. Preserve historical versions as versions, not duplicate errors.
- Deduplicate identical content while retaining every source observation and version relationship. Do not merge different judges, courts, counties, chapters, or document versions solely on a similar name.
- Track text quality: native extraction versus OCR, file/page counts where available, text length, truncation, scanned pages, extraction failures, and manual-review flags. Empty or mismatched text does not count as usable legal content.

## Value priorities

Prioritize full legal bodies and original rule/order documents, followed by court forms, filing requirements, official record access, and useful institutional context. County homepages and directories support discovery; they do not substitute for a county's laws or filings. Preserve acquired ancillary pages, but keep them out of claims about substantive legal coverage.

For each state and county, expose captured source families, saved originals, usable text, versions, source-authority confidence, and explicit gaps. Use a known source inventory as a denominator only for that inventory. All 3,144 county-equivalent rows being inventoried does not mean their content is complete.

## Publication gates

1. Wait for the finite collectors to checkpoint and acquire all participating collection locks before the coordinated aggregate rebuild.
2. Verify raw/text/metadata identity and hashes; preserve failed requests and extraction gaps separately.
3. Include every eligible saved capture in the aggregate manifest and search index, with its component, source, version, and geographic evidence. Keep county-local documents separate from county-entry evidence.
4. Validate source references, unique keys, FIPS strings, count reconciliation, and representative searches. Review substantive classification samples and retain remaining unknown classifications.
5. Publish only a passing snapshot. State its capture time, exact coverage, unresolved gaps, and legal-currency limitations. A final package must not imply complete national current law without reconciling the underlying source inventories.

Current evidence: the county semantic sample is in `reports/counties/local_documents_20260914/content_kind_sample_summary.json`; county artifact checks are in its adjacent `progress.json` and `resources.jsonl`; state chapter body/hash checks are under `reports/laws/state_rules_followup_20260914`. These are evidence for their stated scope, not blanket certification of the entire archive.

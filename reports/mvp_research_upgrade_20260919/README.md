# Research navigation and evidence quality pass

This pass improves the existing localhost:8769 MVP with state/category law
navigation, county subpages and saved court-access information, explicit source
dates, document availability filters and reproducible judge library summaries.

## Date meanings

- Source date/as-of: an explicit date retained in source metadata. A missing date
  stays unknown; a year or month remains at that precision.
- Saved date: the latest valid recorded capture timestamp, not filesystem mtime.
- Effective date: a separately recorded legal-effect date, when present.
- Computed date: when a derived library summary was calculated.

These dates do not establish that a law is in force or that a judge still serves.
Publisher snapshot dates remain separately labeled.

## Derived judge insights

The application counts distinct source pages (URL fragments removed), saved court
affiliations and published analysis records; lists available profile components
and missing components; and preserves reported periods and sample-size coverage.
Repeated numerical measures are not deduplicated merely because their values
match. Source measures are not case counts, simultaneous current appointments,
performance scores or predicted litigation outcomes. No such outcome statistic
has been invented from biography or directory records.

## Availability and grouping

Grouped browsing preserves the richest preferred record. Availability filtering
applies to that displayed record; source-observation browsing applies to each
source row. Saved text requires nonempty-text provenance, not merely a text-file
reference. Laws hub local document groups and bulk publisher records remain
separate counts; facets may overlap and should not be summed into unique laws.

Deployment receipts and the next-run handoff will be added after live verification.

# County local resources

This supplement stores local-resource captures separately from county entry pages. `county_ledger.jsonl` preserves all 3,144 county-equivalent GEOIDs as strings. `resources.jsonl` has every request outcome and verified original/text/metadata references. `captures.jsonl` contains downloaded records with their geographic association evidence; `summary.json` records the snapshot time and exact counts.

Filter by county GEOID, state, source category, court label where observed, download status and extraction status. Unassigned municipal/multi-county court documents remain unassigned. Candidate county website associations are labeled; a name match does not establish court jurisdiction. A court information page is not automatically a filing or rule document. Publisher versions and dates require content review before treating text as current law. Full county content is incomplete.

`discovery_categories` preserves selection hints. `reviewed_resource_kind` is populated only by the separately hash-bound `semantic_review`; unreviewed kinds remain null. `detected_type` describes file format, not legal content. Raw, extracted-text and metadata SHA-256 fields preserve each artifact identity. GEOID arrays are source associations with verification flags retained in `contexts`, not verified court territorial assignments.

The focused search includes these collections after the coordinated index rebuild. Original files remain in the workspace at each capture's recorded path. This supplement is not a standalone copy of those bytes.

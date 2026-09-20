# Litigation source browser review

The supplied `C:/Users/firas/Downloads/litigation/_source/_browser.html` does not exist. A bounded filename check found `C:/Users/firas/Downloads/litigation_source_browser.html`, which was inspected as data without executing its HTML or JavaScript.

The replacement is a **2,148,193-byte standalone registry viewer**, last modified August 19, 2026. SHA-256: `e2d1849b1b672092573d699e200f5315ecda6eee73c20b2f0c6d2478461317f7`.

Its embedded JSON contains **9,348 records and 9,348 unique URLs**, all already present in `registry_v06_1.sqlite`: **zero new URLs**. Eight compact fields match the corresponding registry fields in every row. Its description field differs on 131 rows; the SQLite registry retains more information, and 130 of those HTML descriptions are blank. The HTML should not overwrite the richer registry.

The `v` flag exactly represents presence of the historical `verified_date`. It is not precisely equivalent to HTTP 200 and does not establish present availability. The viewer contains no document bodies, images, external scripts, fetch calls, or direct local-file references.

Reference counts include 152 judge-page links, 553 court-rule links, 409 statute/code links, 527 regulation/register links, and 1,355 form links. References occur for all 50 states, DC, Puerto Rico, the Virgin Islands, federal/nationwide and multiple-jurisdiction scopes. This is reference presence, not complete state/county coverage. There are no structured county identity fields or structured judge biographies. The 16 API-typed references and 62 API/bulk-layer references are the same previously reviewed set, with no new access credentials or endpoints.

Exact URL comparison found 339 canonical saved-catalog matches, 347 directory artifact matches, and 32 new pilot matches: **588 distinct matches across those three checks**. These overlapping figures must not be summed. Unmatched URLs may have alternate spellings or captures elsewhere; this was not a recursive corpus audit.

The useful reusable artifact is **`display_labels.json` (9,326 bytes)**, extracted from the literal `const M` object. It preserves exact source keys and attribution for 55 jurisdiction labels, 28 category labels, 14 task-family labels, 31 layer labels and 9 content-kind labels. Fourteen current source-directory labels could be improved without changing IDs or counts, for example `Api` → `API`, `Efiling cmecf` → `E-filing / CM-ECF`, and `Ethics professional resp` → `Ethics & professional responsibility`. Blank category maps only to the existing `uncategorized` ID. These label suggestions do not modify the separate eight-category saved-laws taxonomy.

The viewer's state filter uses strict jurisdiction equality, so choosing a state excludes federal and multiple-jurisdiction rows. Other dimensions combine with AND. Search requires every whitespace-separated term. Facets apply all filters except their own dimension. Those semantics were established by reading source text only.

`inventory.json` records hashes, sizes, samples, field reconciliation, counts, duplicate checks and limitations. No source data or MVP files were modified. Recommended integration is optional label-only humanization, not another corpus import.

# Continue from the archive-link checkpoint (September 19, 2026)

Read RUNBOOK.md first. The source directory now has two separate availabilities:
**Saved content attached** (32 pilot captures, exact URL) and **Saved in archive**
(554 references linked to 370 directory records, 204 retained captures and 104 judge
profiles). Do not repeat the link build unless the directory or canonical index was
rebuilt; then run `sources/source_archive_links_20260919/build.py` so the gate binds the
new receipts, and restart the server with `reports/source_archive_links_20260919/restart.ps1`.

Checks that must keep passing:
`delivery/archive-directory/test_source_archive_links.py`,
`sources/source_archive_links_20260919/test_build.py`,
`sources/public_law_directory_20260919/test_source_directory.py`, and
`reports/source_archive_links_20260919/verify_live.py` against the running server.

1. The 588-candidate reuse pass is closed: 586 are reachable in the MVP, 2 are documented
   exclusions (empty text; zero-byte original). Do not redownload any of them.
2. Two `official_laws` final-URL matches (CA rules of court, VT rules) stay excluded because
   only `sources/official_courts` and `corpus/official_courts` are registered asset roots.
   Register another root only with the same fresh-hash and confinement checks.
3. The Ballotpedia capture `sources/official_courts/raw/9ca4a2810feff11904c2.html` is a
   zero-byte original that the canonical index marks searchable; treat it as an index
   quality finding, not saved content.
4. Next bounded slices, in order of value: (a) exact observed state/local rule, form and
   order document links from the 32 saved pilot pages and the 204 retained court pages,
   deduplicated against saved URLs/hashes, under the existing eight-worker/host-lock/
   600-second controls; (b) documented API/bulk adapters where access is established;
   (c) judge portraits/biographies from known local collections.
5. `Downloads/registry_v06_1.jsonl` is an identical export of the integrated registry; no
   import is needed. The Trellis state-rules/county material remains in its existing
   bounded queues with the view-allowance limits recorded in RUNBOOK.md.

Keep raw files immutable and reading copies separate. Links are exact-URL evidence only;
never infer county jurisdiction from hosts or merge judges by name.

# Legal Archive UI sketch

A clickable wireframe built only from the saved September 13, 2026 focused corpus. No new scraping or external requests are used.

Open `index.html` directly, or view the running local preview at http://127.0.0.1:8768.

## Pages

- Overview: available data and proposed research flows.
- Laws & rules: filter the saved source entries by title, jurisdiction, content type, publisher and text availability; inspect source evidence and 30 saved legal excerpts.
- Counties: filter 3,144 county-equivalent inventory rows by name, state, GEOID, profile status and website evidence; inspect the selected county.
- Judge sources: filter 145 saved official roster/directory/profile sources by title, state and type. These are source entries, not 145 individual judges.
- Coverage & gaps: distinguish saved content, directory entries and missing records.

Metadata filters, record selection, navigation, source-reference copying and CSV export are implemented. Full-document search, complete document loading and original-file downloads are proposed connections to the existing corpus, not implemented in this sketch.

The inventory covers all 50 states and DC; only 1,421 county rows have a clear saved Trellis profile match. Law and judge coverage is partial. No case analytics, judge win rates or live updates are implied.

## Regenerate or restart

From the SCRAPE workspace:

```powershell
python delivery/ui-sketch/build_data.py
python -m http.server 8768 --bind 127.0.0.1 --directory delivery/ui-sketch
```

Keep `index.html` and `data.js` together. Original source files remain in the corpus; this preview serves only its own folder.

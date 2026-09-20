# Next run: continue the corpus upgrade

Read `README.md` here first, then `BRIEF.md` (agent rules) and the scoping reports under `understand/`.
Server: check `delivery/archive-directory/server.json`; if the port is down run `start_server.ps1`; to deploy code changes run
`restart.ps1` (verifies the recorded PID's command line before stopping it). Then `verify_round2.py` and `verify_scaffold.py`.

Bounded next slices, in value order (one agent or one session each, behind its own `validation.json`):

1. **Settlements** — build `settlements.jsonl` (settlement-record-v1) and the document registry from the 234 captured pages in
   `sources/settlements_20260919/packet1` using the tested classifier; adapter `settlements.py`; then un-hide the sidebar link.
2. **Federal court statistics** — parse the 93 fetched AO tables (XLSX) and CJRA Tables 7/8/9 (PDF) into `tables.jsonl` with
   period labels; adapter `court_statistics.py`; join CJRA judge rows conservatively through the MDL registry's judge keys.
3. **Court spine + logos + Seeger document subtypes** — from `sources/local_asset_discovery_20260918` and CourtListener courts;
   then rerun `sources/record_facets_20260919/build.py` so court ids and county geoids fill the facet columns.
4. **Judge structured overlay** — FJC structured appointments, nid→jid→CourtListener person bridge, SW-BULK assignment evidence;
   surface on judge profiles beside the MDL block.
5. **Trellis coverage metadata** — normalise the 30 saved free responses; no view-consuming calls.
6. **Integration foundation** — canonical id crosswalk, validation-envelope linter, licence registry, dry-run export bundle
   (draft plan in `integration/INTEGRATION_PLAN_DRAFT.md`). Do not touch the external platform.

Housekeeping: `test_mvp.py` has two stale expectations (10,669 judges; 14 portraits) from before the September 19 portrait
integration; a task chip exists for it. The `.building` file left in `sources/agency_safety_20260919` from the interrupted
round-1 build can be deleted once the passed `agency_safety.sqlite3` is confirmed (it is not referenced by the envelope).

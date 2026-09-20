# Conservative judge identity layer

This offline layer preserves all 7,736 source observations from the pinned sealed judge snapshot. It creates 6,687 identity groups, including unresolved single observations. These counts are not a count of distinct people or current judges.

`observation_identity.jsonl` maps each existing report ID to `judge_id`; `judges.jsonl` summarizes groups. `match_decisions.jsonl` records every exact-name candidate pair and its evidence or reason for no link. Same-publisher profile links and independently corroborated source pairs are distinguished. CSV versions are included.

Links require the exact normalized full name, explicit state, and a specific identical court supported by literal source fields. Initial-only first/last names, name-only matches, fuzzy spellings, omitted middle initials, court aliases, county-only matches, competing publisher URLs, duplicate official entries and conflicting affiliations do not produce automatic links. Every pair in a group must pass independently.

`service_timeline.jsonl` preserves reported affiliations, appointment/service passages, career rows and explicitly labeled service dates. Narrative dates are not interpreted or attached to inferred events; undated rows stay undated. Capture timestamps are not service dates. Current judicial status remains unknown; conflicting source statuses are retained.

The original package and source files are unchanged. `method.json` pins consumed file hashes and normalization rules. Original artifact references and their previously sealed hashes are carried forward; this run verifies the sealed components, not current website truth. Canonical IDs are deterministic for fixed group membership and may change when reviewed new evidence changes that membership. Rebuilding requires a new output directory.

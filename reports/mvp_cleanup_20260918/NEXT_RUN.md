# Clean personal MVP maintenance

The user's latest request prioritizes a clean, accurate personal-testing interface.
Full scraping/downloading is not required for this phase. Read the newest REQUEST.md
section first; historical acquisition queues are saved, not instructions to resume.

Open http://127.0.0.1:8769/. The interface is in delivery/archive-directory.
The current features are Home, Laws & rules, dedicated judge profiles, state/county
pages and four curated local-library collections. Sources and technical metadata
remain optional details. Legal status/date and analytical scope must stay accurate.

## Preserve and reuse

- Open US Law v2026.08 is ready: 2,978,617 publisher records, 229 checked files,
  successful FTS external-content integrity and SQLite quick_check. Its validated
  ready marker and catalog_validation.json are the gate. Do not repeat full import,
  FTS rebuild or hashing without changed evidence. Counts are not unique current law.
- Preserve Seeger originals, the validated 384-record recovery overlay, clean reader
  bindings and conservative judge entity groups. The older enrichment NEXT_RUN.md
  explains their rebuild rules; its acquisition-resume step is superseded here.
- judges.py builds only a human-facing presentation database. It retains 10,669
  identities, including 5,942 detailed profiles and all 708 sourced analysis records.
  Five portraits are confirmed; nine ambiguous image matches stay unassigned.
- Local library previews use a frozen exact allowlist. Original external PDFs remain
  in their user-authorized folders; moved/changed files fail closed. Do not copy whole
  libraries or expose arbitrary filesystem paths. Four copied images are court marks
  or icons, not courthouse photos or county seals.
- The MDL catalog contains 1,612 PDFs, but this MVP exposes 24 selected previews;
  settlement references have 848 catalog rows and four selected official PDF previews.
  Collection search filters the available preview records. Never describe a preview
  search as searching every original document body.

## Maintenance

1. Complete only concrete, bounded UI/data-quality defects or source-backed preview
   improvements from existing authorized local datasets. Avoid speculative redesign.
2. Keep broad new law/county/judge/vendor network acquisition parked. Existing finite
   queues and access policies remain preserved for a later acquisition phase.
3. Do not rebuild the main directory for frontend-only changes. After a source change,
   use the existing validated publication workflow and recovery/reader gates.
4. Restart only the verified loopback server process after backend source changes.
   Use START.cmd or the hidden Python --serve launch, preserving file allowlists.
5. Run tests appropriate to changed modules and the live API. Verify desktop/mobile,
   keyboard navigation, search/filter persistence, empty/missing states and actual
   profile/collection routes in the browser before claiming UI completion.
6. Update verification.json with observed results. Preserve raw evidence, unresolved
   identities, missing official URLs, historical statuses, edition and OCR limitations.

The existing 30-minute heartbeat now follows this MVP scope. Stay quiet when no
meaningful change needs attention; notify only a validated improvement, failure,
completion or required user action. Do not create activity by restarting old crawlers.

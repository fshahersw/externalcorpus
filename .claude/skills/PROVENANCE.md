# Project skills: provenance

Installed 2026-09-20 from https://github.com/LegalQuants/lq-skills at commit `884cf402949981ca2a4afb8ff88f19337005eecf` (Apache-2.0; licence text in `LICENSE-lq-skills-Apache-2.0.txt`).
Files are unmodified copies; each was checked against the SHA-256 recorded when it was fetched
(`sources/upstream_open_data_20260920/repos/LegalQuants__lq-skills/manifest.json`). Authors are named in each SKILL.md.

Before installation each SKILL.md was read in full and every supporting file was scanned for external calls, credential requests and
instructions to override the conversation: none was found. All of them produce drafts for attorney review, not legal advice.

| Skill | What it is for |
|---|---|
| `statutory-analysis` | First-pass framework for reading US statutes and regulations; draft-only, attorney review required. |
| `enhance-prompt` | Rewrites a short prompt into a structured legal prompt and shows what changed; never silent. |
| `building-chronologies` | Sourced event chronologies from documents; every event cites its source; gaps are listed, not filled. |
| `proposition-checking` | Checks whether cited authorities or record material actually support each proposition. |
| `adversarial-qc` | Two-reviewer quality control of a deliverable before it goes to a person. |

Reviewed and not installed: `bart-statutory-reference-checker` and `text-provenance` (Singapore-specific), `case-file-analyzer` (proof of concept),
`legal-claim-economics` (UK funding structures). They remain in the pinned copy if wanted later.

To refresh: run `fetch.py survey`, `fetch.py get LegalQuants/lq-skills "skills/<name>/*"`, re-read the changed files, then run this script again.

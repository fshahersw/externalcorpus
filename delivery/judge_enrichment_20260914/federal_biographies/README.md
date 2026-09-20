# Federal professional biography enrichment

This separate FJC snapshot contains **4,074 federal judge source observations** and **18,337 grouped professional facts**:

| Fact category | Records |
|---|---:|
| Main federal judicial service / appointments | 4,774 |
| Education entries | 8,153 |
| Other federal judicial service | 618 |
| Professional career text | 4,070 |
| Other nominations / recess appointments | 722 |

Open `observations.csv` for a spreadsheet export or `observations.jsonl` for the complete structured professional projection. `facts.jsonl` contains the corresponding grouped facts, each citing exact original CSV cells. `schema.json`, `summary.json`, `validation.json`, `independent_validation.json` and `files.sha256.json` describe the contract, counts, checks and artifact hashes.

Each observation retains FJC `nid` and literal legacy `jid`, a source-bound observation ID, display name, native name components, court names, education, appointments and career/service text. Court Seat IDs and all appointment dates remain attached to their original service slot. The source URL, workspace-relative raw path, SHA-256, capture time, logical CSV record and physical line range allow every record to be traced to the saved original. `native_record` retains all 189 professional/name/ID columns literally, including source blanks. The unchanged source file is referenced rather than duplicated.

`judge_system` is `federal`; `judge_category` is `fjc_article_iii_directory`. `state_code` stays null and `counties` stays empty. Other federal service can include non-Article-III offices; it is not mislabeled as Article III. Four repeated display names each have two distinct FJC IDs and remain separate. No name-only joins or cross-source entity resolution were performed.

This is a dated historical/current directory export, not a state-judge census or an assertion that any individual currently holds office. Blank termination dates are not interpreted as active service. Other nominations remain distinct from successful appointments. Education entries with no degree remain degree-null. Career prose is not split into inferred jobs, counties or dates. ABA nomination qualification ratings are preserved as source fields and are not litigation outcome or performance metrics. No metrics were computed.

The original CSV has 12 demographic/birth/death fields that are excluded from this professional projection. The FJC documentation describes a different CSV date display than this actual export; all 31,539 date literals are preserved as received. There are 25 source observations with no education entry and four without professional career text. Those gaps are retained. Validation establishes integrity, attribution and deterministic parsing; it does not independently certify every FJC assertion.

Source documentation: [FJC export](https://www.fjc.gov/node/7436) and [directory scope](https://www.fjc.gov/history/judges). Original and acquisition evidence: `sources/judges/enrichment_20260914/federal_biographies/`. To regenerate offline, run `normalize.py` there using the bundled Python runtime, followed by `validate_independently.py`. Do not rerun its network acquisition script.

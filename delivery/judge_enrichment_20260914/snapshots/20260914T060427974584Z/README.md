# Standardized judge corpus

This immutable snapshot combines the previously reviewed judge corpus with authoritative public professional biographies and official judge-performance evaluations. See summary.json for exact counts and acquisition dates.

judges.jsonl and judge_index.csv contain conservative identity groups, not a verified census of unique current judges. source_observations.jsonl preserves each publisher's record, dates, court labels and native payload. facts.jsonl retains professional facts as evidence-linked claims. analyses.jsonl retains source-reported survey/evaluation measurements with their cycle, unit, available denominator, cohort and methodology. Unknown contexts remain null. Source conflicts and historical information are retained without silently choosing one value.

The observations table and FTS index in judge_corpus.sqlite3 support name, professional text, state, source, court and judge-system filtering. Analyses and facts link through observation and judge IDs. Use scripts/search_judge_enrichment.py for search and full evidence-linked reports.

An official retention/performance evaluation is not a motion-grant rate, litigation win rate or causal quality score. Comparisons require compatible evaluation programs, cycle, respondent cohort and metric definition. Federal biographies do not supply litigation outcome statistics. Court-level values are not assigned to individual judges. Historical marketing reports remain separate from actual judge analysis. External observations stay separate until a court/jurisdiction identity match is independently verified.

components/ preserves frozen inputs and identity decisions; component_inputs.json and verified_originals.json record their SHA-256 evidence. validation.json documents structural checks, while individual source components document extraction checks and gaps. Full nationwide collection remains incomplete.

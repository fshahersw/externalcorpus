"""Read-only topical FTS pass over the Open US Law index (mode=ro; about 2.5 minutes).

Writes _work/oul_analysis.json: per-topic hit counts by state and kind, plus the publisher
chapter/title names of every court_rules row grouped by state. Queries are FTS5 phrase sets and
are stored verbatim with the results so every number can be reproduced.
"""
import collections
import json
import sqlite3
import time

ROOT = 'C:/Users/firas/Downloads/SCRAPE'
OUT = ROOT + '/reports/corpus_upgrade_20260919/understand/_work/oul_analysis.json'

TOPICS = {
    'sol_any': '"limitation of actions" OR "limitations of actions" OR "statute of limitations" OR "statutes of limitations" OR "limitations period" OR "period of limitation" OR "period of limitations"',
    'sol_personal_injury': '("personal injury" OR "personal injuries" OR "injuries to the person" OR "injury to the person" OR "injury to person") AND (limitation OR limitations OR "shall be brought within" OR "shall be commenced within" OR "must be commenced within" OR "within two years" OR "within three years")',
    'repose': '"statute of repose" OR "period of repose" OR "statutes of repose"',
    'product_liability': '"product liability" OR "products liability" OR "product liability action" OR "defective product" OR "product seller"',
    'comparative_fault': '"comparative fault" OR "comparative negligence" OR "contributory negligence" OR "contributory fault" OR "comparative responsibility" OR "proportionate responsibility"',
    'joint_several': '"joint and several liability" OR "jointly and severally liable" OR "several liability"',
    'damages_any': '"noneconomic damages" OR "non-economic damages" OR "noneconomic loss" OR "noneconomic losses" OR "punitive damages" OR "exemplary damages"',
    'damages_caps': '("noneconomic damages" OR "non-economic damages" OR "noneconomic loss" OR "punitive damages" OR "exemplary damages") AND ("shall not exceed" OR "may not exceed" OR "not to exceed" OR "not exceed")',
    'udap': '"deceptive trade practices" OR "unfair trade practices" OR "consumer protection act" OR "consumer fraud" OR "unfair or deceptive acts" OR "deceptive acts or practices" OR "unfair methods of competition"',
    'wrongful_death_survival': '"wrongful death" OR "death by wrongful act" OR "survival of actions" OR "survival action" OR "survival of causes of action" OR "survival of cause of action"',
    'class_action': '"class action" OR "class actions" OR "representative parties"',
    'expert_evidence': '"testimony by experts" OR "testimony by expert" OR "expert testimony" OR "testimony by expert witnesses"',
    'complex_coordination': '"multicounty litigation" OR "multi-county litigation" OR "coordination proceeding" OR "coordination proceedings" OR "coordinated proceedings" OR "complex litigation" OR "mass tort" OR "mass torts" OR "multidistrict litigation" OR "litigation coordinating panel" OR "complex case" OR "complex cases" OR "complex civil"',
    'medical_monitoring': '"medical monitoring"',
    'asbestos_silica_claims': 'title:asbestos OR title:silica OR "asbestos claim" OR "asbestos claims" OR "asbestos action"',
    'affidavit_certificate_of_merit': '"affidavit of merit" OR "certificate of merit"',
    'forum_non_conveniens_venue': '"forum non conveniens" OR "inconvenient forum"',
}


def main():
    c = sqlite3.connect('file:' + ROOT + '/sources/open_us_law_20260918/catalog.sqlite3?mode=ro', uri=True)
    topics = {}
    for k, q in TOPICS.items():
        t0 = time.time()
        rows = c.execute(
            'select r.state,r.kind,count(*) from records_fts f join records r on r.rowid=f.rowid '
            'where records_fts match ? group by 1,2', (q,)).fetchall()
        by = collections.defaultdict(dict)
        for s, kind, n in rows:
            by[s][kind] = n
        topics[k] = {'query': q, 'by_state': by, 'seconds': round(time.time() - t0, 1), 'total': sum(n for _, _, n in rows)}
        print(k, topics[k]['total'], flush=True)
    sets = collections.defaultdict(collections.Counter)
    for st, pl in c.execute("select state,payload from records where kind='court_rules'"):
        try:
            d = json.loads(pl)
        except ValueError:
            d = {}
        sets[st][(d.get('title_name') or '', d.get('chapter_name') or '')] += 1
    out = {s: [{'title_name': k[0], 'chapter_name': k[1], 'rows': n} for k, n in v.most_common()] for s, v in sets.items()}
    json.dump({'topics': topics, 'court_rule_sets': out}, open(OUT, 'w', encoding='utf-8'))


if __name__ == '__main__':
    main()

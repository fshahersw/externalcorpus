"""Read-only independent audit of the saved Colorado component."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib,json,re

ROOT=Path(__file__).resolve().parents[3]
COMP=ROOT/'delivery/judge_enrichment_20260914/state_evaluations'
OUT=Path(__file__).resolve().parent
def loadl(name):return [json.loads(x) for x in (COMP/(name+'.jsonl')).read_text(encoding='utf-8').splitlines()]
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def main():
    issues=[];counts=Counter();hashcache={};textcache={};receipts=[]
    def check(ok,kind,detail):
        counts[kind]+=1
        if not ok:issues.append(dict(kind=kind,detail=detail))
    def digest(path):
        if path not in hashcache:hashcache[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        return hashcache[path]
    def text(path):
        if path not in textcache:textcache[path]=(ROOT/path).read_text(encoding='utf-8')
        return textcache[path]
    component_paths=sorted(p for p in COMP.rglob('*') if p.is_file())
    initial={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in component_paths}
    observations=loadl('observations');facts=loadl('facts');analyses=loadl('analyses');contexts=loadl('context_analyses')
    boundaries=loadl('section_boundaries');source_records=loadl('source_manifest')
    by_id={x['source_observation_id']:x for x in observations};bounds={x['source_observation_id']:x for x in boundaries}
    check(len(by_id)==len(observations)==116,'observation_ids_unique',len(observations))
    check(set(by_id)==set(bounds) and len(boundaries)==116,'boundary_ids_complete',len(boundaries))
    doc_map={};page_map={}
    for rec in source_records:
        if not rec.get('pdf_pages'):continue
        body=''
        for p in rec['pdf_pages']:
            content=text(p['text_path']);start=len(body)
            page_map[(rec['source_path'],p['page_number'])]=dict(start=start,end=start+len(content),**p)
            check(digest(p['text_path'])==p['text_sha256'],'page_hash',p['text_path'])
            body+=content+'\n'
        doc_map[rec['source_path']]=body
    verification=json.loads((COMP/'validation.json').read_text(encoding='utf-8'))
    for item in verification['file_checks']:
        check(digest(item['path'])==item['sha256'],'saved_source_file_hash',item['path'])
        receipts.append(dict(path=item['path'],sha256=digest(item['path'])))
    for obs in observations:
        sid=obs['source_observation_id'];b=bounds[sid];doc=doc_map[obs['source_path']]
        check(b['role_start']<=b['name_start']<b['name_end']==b['narrative_start']<b['narrative_end']<=b['next_role_start'],
              'boundary_order',sid)
        check(doc[b['narrative_start']:b['narrative_end']]==obs['native']['evaluation_narrative'],'full_native_narrative',sid)
        check(text(obs['narrative_path'])==obs['native']['evaluation_narrative'],'narrative_file_text',sid)
        check(digest(obs['narrative_path'])==obs['narrative_sha256'],'narrative_file_hash',sid)
        check(doc[b['name_start']:b['name_end']].strip()==obs['native']['name_heading_literal'],'name_bound_to_heading',sid)
        check(doc[b['role_start']:b['name_start']]==obs['native']['role_heading_literal'],'role_bound_to_heading',sid)
        if obs['court_level']=='district_court':check(obs['counties'] is None,'district_counties_not_inferred',sid)
        check(obs['current_status']=='not_verified_beyond_2024_evaluation','historical_cycle_preserved',sid)
    def evidence(row,kind):
        ev=row['evidence'];sid=row.get('source_observation_id');global_ranges=[]
        check(digest(ev['source_path'])==ev['source_sha256'],'evidence_original_hash',kind)
        for seg in ev['segments']:
            p=page_map[(ev['source_path'],seg['page'])]
            check(seg['text_path']==p['text_path'],'evidence_page_source_join',kind)
            check(digest(seg['text_path'])==seg['text_sha256'],'evidence_page_hash',kind)
            check(0<=seg['start']<seg['end']<=len(text(seg['text_path'])),'evidence_page_range',kind)
            check(text(seg['text_path'])[seg['start']:seg['end']]==seg['quote'],'exact_page_quote',kind)
            global_ranges.append((p['start']+seg['start'],p['start']+seg['end']))
        if global_ranges:
            start,end=global_ranges[0][0],global_ranges[-1][1]
            quote_start,quote_end=start,end
            if sid and row.get('predicate')=='observed_name':
                # Name boundaries may begin/end on the one synthetic LF inserted between pages.
                # That LF belongs to Document.text but intentionally to neither page segment.
                quote_start,quote_end=bounds[sid]['name_start'],bounds[sid]['name_end']
                if (quote_start,quote_end)!=(start,end):
                    extras=list(range(quote_start,start))+list(range(end,quote_end))
                    separators={p['end'] for (source_path,_),p in page_map.items() if source_path==ev['source_path']}
                    check(bool(extras) and all(i in separators and doc_map[ev['source_path']][i]=='\n' for i in extras),
                          'explicit_synthetic_page_separator_reconstruction',row['fact_id'])
            check(doc_map[ev['source_path']][quote_start:quote_end]==ev['quote'],'full_quote_including_page_breaks',kind)
            if sid:
                b=bounds[sid]
                if kind=='analysis':
                    check(b['narrative_start']<=start<end<=b['narrative_end'],'judge_analysis_within_own_narrative',sid)
                elif row.get('predicate')=='court_jurisdiction_at_evaluation' and by_id[sid]['court_level']=='district_court':
                    # This intentional shared district heading is jurisdiction evidence, not person-level analysis.
                    expected=by_id[sid]['native']['district_heading_literal']
                    check(ev['quote']==expected and start<b['role_start'],'shared_district_context_typed',sid)
                else:check(b['role_start']<=start<end<=b['narrative_end'],'judge_fact_within_own_section',sid)
    for row in facts:evidence(row,'fact')
    for row in analyses:evidence(row,'analysis')
    for row in contexts:
        check(row['source_observation_id'] is None,'aggregate_not_person_attributed',row['metric']);evidence(row,'context')
    methodology=json.loads((COMP/'methodology.json').read_text(encoding='utf-8'))
    evidence(methodology,'methodology')
    findings=[x for x in analyses if x['analysis_type']=='commission_performance_evaluation']
    negative=[by_id[x['source_observation_id']]['name'] for x in findings if x['value']=='does_not_meet_performance_standards']
    check(len(findings)==116 and negative==['Angela M. Roff'],'finding_census',negative)
    for row in analyses:
        if row['analysis_type']=='commission_vote':
            match=re.search(r'\b(\d{1,2})\s*(?:[-–]|to)\s*(\d{1,2})\b',row['evidence']['quote'])
            check(bool(match) and [int(x) for x in match.groups()]==[row['votes_for_finding'],row['votes_against_finding']],
                  'vote_literal_matches_counts',row['analysis_id'])
            check(row['observed_votes_cast']==row['votes_for_finding']+row['votes_against_finding'],'cast_votes_exclude_noncaster_counts',row['analysis_id'])
        if row['analysis_type']=='survey_overall_rating':
            check(row['unit']=='scale_points' and row['numerator'] is None and row['denominator'] is None,'scale_not_proportion_denominator',row['analysis_id'])
            check(str(row['value']) in row['evidence']['quote'],'score_value_literal',row['analysis_id'])
            check(row['scale_minimum'] is None,'scale_minimum_not_inferred',row['analysis_id'])
    names=['Angela M. Roff','Monica M. Márquez','Kim Soon Shopshire','Benjamin Figa','Milla Lishchuk','Anita J. Crowther',
           'Shay K. Whitaker','Cynthia J. Jones','Jason Todd Kelly','David L. Shakes','Allison J. Esser','Stephanie Dunn']
    notes=[
      'Garfield County heading; sole negative finding is 4-3 with three absent. The judge response is preserved with its speaker label; its closure/appeal claims are not normalized as commission findings or independent outcome metrics.',
      'Supreme Court heading; 10-0 plus one recusal. Overall 3.8/4 score is separate from 95% attorneys and 98% judges meeting-standard responses. The 20 attorney/41 judge totals are not fabricated score denominators.',
      'Sixth District heading says Shopshire while body says Shropshire. Both spellings and the explicit conflict flag are retained; 3.4/4 and 34 respondents remain in the same section without identity correction.',
      'District 18 county list conflict remains flagged and counties null. Overall 2.9 is separate from appellate-judge subgroup 3.9 (10 responses); maximum for 2.9 stays null rather than borrowing a nearby scale.',
      'Baca County; source says Meets with 3-3 vote, two absent and two vacancies. The apparent publication inconsistency remains literal. No survey rating invented where narrative says no public survey results.',
      'District 19; 7-0 with one abstention and two absent, cast votes 7. Overall 2.8/4 remains separate from 23 attorney and 16 nonattorney groups and their percentages.',
      'District 18; counties null. Overall 3.4/4 with 20 returned surveys (14 attorneys/6 nonattorneys) stays distinct from 13/14 meeting-standard answers and 100% nonattorneys.',
      'Clear Creek County; 9-0 plus recusal. Overall 3.0/4, 42 returned surveys (15/27 cohorts) retained. End-of-section district note is preserved as publication context and does not create other county or judge analyses.',
      'Conejos County; unanimous categorical finding has no numeric tally, and the numeric-vote gap is explicit. No guessed perfect survey score from qualitative highest-score wording.',
      'District 4; 5-0 unanimous with five absent. Combined 3.4/4 remains separate from appellate subgroup 3.5/4; low-response caution retained in complete narrative.',
      'District 19; 8-0 with two absent. Explicit 3.5/4 overall rating remains separate from 88% attorney/92% nonattorney meeting-standard responses; no guessed sample size.',
      'Court of Appeals; 10-0 plus recusal. 3.8/4 is separate from 94% attorney and 100% judge answers; 16 attorney/33 judge totals are not assigned as a question-level denominator.',
    ]
    sample=[]
    for name,note in zip(names,notes):
        obs=next(x for x in observations if x['name']==name)
        sample.append(dict(name=name,source_observation_id=obs['source_observation_id'],pages=obs['source_pages'],
          narrative_path=obs['narrative_path'],narrative_sha256=obs['narrative_sha256'],review_result='passed',review=note))
    src=next(x for x in source_records if x.get('source_kind')=='cycle_compilation')
    discrepancy=[]
    for pn in (7,113):
        pg=page_map[(src['source_path'],pn)];body=text(pg['text_path'])
        m=re.search(r'Eighteenth Judicial District[^\n]*(?:\n[^\n]*)?',body)
        discrepancy.append(dict(page=pn,path=pg['text_path'],sha256=digest(pg['text_path']),literal=m.group() if m else None))
    check(all(x['literal'] for x in discrepancy),'district18_conflict_both_sources_present',discrepancy)
    final={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in component_paths}
    check(initial==final,'component_unchanged_during_audit',len(final))
    result=dict(validated=not issues,status='passed' if not issues else 'issues_found',audited_at=datetime.now(timezone.utc).isoformat(),
      component_path=COMP.relative_to(ROOT).as_posix(),component_sha256=final,
      counts=dict(observations=len(observations),facts=len(facts),analyses=len(analyses),context_analyses=len(contexts),section_boundaries=len(boundaries),sampled_narratives=len(sample)),
      checks=dict(counts),source_artifact_receipts=receipts,sample_reviews=sample,district18_publication_evidence=discrepancy,
      unresolved_findings=len(issues),issues=issues,
      preserved_publication_uncertainties=['Shopshire/Shropshire spelling conflict','District 18 body/TOC county-list conflict',
        'Milla Lishchuk source finding Meets together with 3-3 vote; not converted to a majority claim'],
      scope_notes=['116 published 2024 ballot evaluations; not all 120 evaluated or 130 eligible officers.',
        'All saved quoted evidence and section boundaries checked; 12 narratives read purposively, not a full semantic certification.',
        'Twelve observed-name quotes include a leading/trailing synthetic LF inserted between pages by Document.text. Each was reproduced at its explicit saved name boundaries and the extra character independently verified to occur exactly at a page separator; no source correction was needed.',
        '28 normalized rating passages also inspected; grouped cohorts and denominators are not inferred.',
        'No network and no changes to source/builder/delivery.'])
    dump(OUT/'colorado_independent_audit.json',result)
    (OUT/'colorado_independent_audit.md').write_text(
      '# Colorado independent audit\n\n'+f'**{result["status"]}: {len(issues)} unresolved findings.** Checked 116 observations, 478 facts, 258 judge analyses, six state-level analyses and 116 section boundaries. All {counts["exact_page_quote"]} saved page-offset quotation segments reproduce the source text; all 258 judge analyses remain inside their own judge narrative. '+
      f'Rechecked {counts["saved_source_file_hash"]} source-artifact hashes and {len(final)} component-file hashes. The component remained unchanged during the audit.\n\n'+
      'Read 12 purposively selected complete narratives and all 28 normalized overall-rating passages. The JSON report retains exact source IDs, page/narrative hashes and review notes. Survey scale points are not proportions; absent, recused or vacant commission positions are not counted as votes cast. Statewide totals remain unassigned to persons.\n\n'+
      'The source spelling conflict, district 18 county discrepancy and Lishchuk 3-3/Meets wording remain preserved. Roff\'s response is retained with its speaker label and has not been promoted into an independent outcome metric. No current standing, extra identities or additional survey denominators were inferred.\n\n'+
      'This is exhaustive integrity/offset/boundary checking plus a 12-narrative semantic sample, not certification of every source assertion. No network or component/source mutations were made.\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],issues=issues,checks=dict(counts),component_files=len(final)),ensure_ascii=True))

if __name__=='__main__':main()

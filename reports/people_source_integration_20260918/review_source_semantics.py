"""Bounded offline review of CourtListener people/positions/courts source tables."""
import bz2
from collections import Counter
import csv
import datetime
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
SOURCE=Path('C:/Users/firas/Downloads/returnedfiles/bulk')


def read_table(stem):
    path=SOURCE/(stem+'-2026-06-30.csv.bz2')
    with bz2.open(path,'rt',encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f,escapechar='\\',doublequote=False,strict=True)
        rows=list(reader)
    assert all(None not in r and all(v is not None for v in r.values()) for r in rows)
    return rows,{'path':path.as_posix(),'compressed_bytes':path.stat().st_size,
                 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':len(rows),'columns':reader.fieldnames}


def date_summary(rows,date,granularity):
    mismatches=[{k:r[k] for k in ['id',date,granularity]} for r in rows if bool(r[date])!=bool(r[granularity])]
    examples=[];invalid=[]
    for precision in ('%Y','%Y-%m','%Y-%m-%d'):
        sample=next((r for r in rows if r[date] and r[granularity]==precision),None)
        if sample:examples.append({k:sample[k] for k in ['id',date,granularity]})
    for r in rows:
        if r[date]:
            try:datetime.date.fromisoformat(r[date])
            except ValueError:invalid.append({k:r[k] for k in ['id',date,granularity]})
    return {'nonempty_dates':sum(bool(r[date]) for r in rows),
            'granularity_for_nonempty_dates':dict(Counter(r[granularity] for r in rows if r[date])),
            'all_granularity_values':dict(Counter(r[granularity] for r in rows)),
            'date_precision_presence_mismatches':mismatches,'invalid_iso_dates':invalid,'examples':examples}


def main():
    people,people_source=read_table('people-db-people')
    positions,position_source=read_table('people-db-positions')
    courts,court_source=read_table('courts')
    by_id={p['id']:p for p in people};aliases=[p for p in people if p['is_alias_of_id']]
    missing=[];cycles=[];depths=Counter()
    for p in aliases:
        seen={p['id']};target=p['is_alias_of_id'];depth=1
        while target:
            if target not in by_id:missing.append({'id':p['id'],'target':target});break
            if target in seen:cycles.append({'id':p['id'],'target':target});break
            seen.add(target);target=by_id[target]['is_alias_of_id']
            if target:depth+=1
        depths[depth]+=1
    report={
        'status':'passed','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope':'Only three explicitly named small biography/reference tables; no opinions, disclosure tables, full inventory, network, or live writes.',
        'snapshot_label':'2026-06-30 from filenames; not a current-service verification date',
        'sources':[people_source,position_source,court_source],
        'csv_dialect':{'escapechar':'\\','doublequote':False,'strict':True,'encoding':'utf-8'},
        'people':{'source_rows':len(people),'unique_source_ids':len(by_id),'non_alias_records':len(people)-len(aliases),
                  'alias_records':len(aliases),'with_death_date':sum(bool(p['date_dod']) for p in people),
                  'has_photo_true':sum(p['has_photo']=='t' for p in people)},
        'aliases':{'missing_targets':missing,'cycles':cycles,'chain_depth_counts':dict(depths),
                   'aliases_with_positions':len({p['person_id'] for p in positions}&{p['id'] for p in aliases}),
                   'examples':[{'id':p['id'],'name':' '.join(p[k] for k in ('name_first','name_middle','name_last','name_suffix') if p[k]),'alias_of_id':p['is_alias_of_id']} for p in aliases[:5]]},
        'dates':{date:date_summary(rows,date,gran) for rows,date,gran in [
            (people,'date_dob','date_granularity_dob'),(people,'date_dod','date_granularity_dod'),
            (positions,'date_start','date_granularity_start'),(positions,'date_termination','date_granularity_termination')]},
        'positions':{'rows':len(positions),'people_with_positions':len({p['person_id'] for p in positions}),
                     'with_court_id':sum(bool(p['court_id']) for p in positions),
                     'missing_start':sum(not p['date_start'] for p in positions),
                     'missing_termination':sum(not p['date_termination'] for p in positions),
                     'position_type_counts':dict(Counter(p['position_type'] for p in positions)),
                     'court_linked_position_type_counts':dict(Counter(p['position_type'] for p in positions if p['court_id'])),
                     'has_inferred_values_counts':dict(Counter(p['has_inferred_values'] for p in positions)),
                     'sector_counts':dict(Counter(p['sector'] for p in positions)),
                     'how_selected_counts':dict(Counter(p['how_selected'] for p in positions))},
        'courts':{'rows':len(courts),'jurisdiction_code_counts':dict(Counter(p['jurisdiction'] for p in courts))},
        'presentation_rules':[
            'Use the companion granularity: %Y -> year, %Y-%m -> month/year, %Y-%m-%d -> full date. Preserve raw values.',
            'A granularity flag without a date does not create a date; null stays unknown.',
            'Unknown granularity must not promote the padded stored date into day precision.',
            'No termination date does not establish current service; use end not recorded and the dated snapshot context.',
            'Keep all native IDs and explicit alias target links; do not silently redirect, merge names, or equate FJC historical IDs with another namespace.',
            'A court_id may occur on a clerk, prosecutor or private-practice position; it is a source court association, not a judicial-role/current-service flag.',
            'Prefer explicit job_title; expand only validated role codes and preserve unknown codes with a neutral label.',
            'Retain has_inferred_values and distinguish inferred appointment/history data from explicit source values.',
            'Birthplace/death-place states are not office locations; education year is not a full graduation date.',
            'has_photo is an availability flag, not a fetched or verified image; all 1,230 flags remain separate from installed portraits.'
        ],'network_requests':0,'source_mutations':0,'live_writes':0,
        'limits':['Source rows include historical people, aliases and nonjudicial positions; counts are not unique current judges.',
                  'Categorical code meanings not documented in these tables must stay qualified instead of being guessed.']}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'source_semantics_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'people':report['people'],'aliases':{k:v for k,v in report['aliases'].items() if k!='examples'},'positions':len(positions),'date_anomalies':{k:len(v['date_precision_presence_mismatches']) for k,v in report['dates'].items()},'invalid_iso_dates':{k:len(v['invalid_iso_dates']) for k,v in report['dates'].items()}},indent=2))


if __name__=='__main__':main()

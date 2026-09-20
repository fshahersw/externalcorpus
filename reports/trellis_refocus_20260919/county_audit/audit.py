"""Read-only Trellis county/state evidence audit; no acquisition or publication."""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.parse import urlsplit
import hashlib
import json
import sqlite3
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def readl(path): return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
def ro(path):
    c = sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    c.row_factory = sqlite3.Row
    return c
def write(name, value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def writel(name, rows): (OUT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=True)
    inventory = readl(ROOT/'delivery/focused_legal_corpus/counties/counties.jsonl')
    states = {r['state'].lower().replace(' ','-') for r in inventory}
    def profile(url, n=3):
        p=urlsplit(url);s=p.path.strip('/').split('/')
        return p.scheme=='https' and p.netloc=='trellis.law' and not p.query and not p.fragment and len(s)==n and s[0]=='coverage' and s[1] in states
    catpath=ROOT/'sources/trellis/catalog/catalog.sqlite3'
    with ro(catpath) as db:
        pages={r['url']:dict(r) for r in db.execute('SELECT * FROM pages')}
        counties={r['url']:dict(r) for r in db.execute('SELECT * FROM counties') if profile(r['url'])}
        proofs=defaultdict(list)
        for row in db.execute("SELECT * FROM links WHERE category='coverage_county' ORDER BY url,source_url"):
            if profile(row['url']): proofs[row['url']].append(dict(row))
        state_links={r['url'] for r in db.execute("SELECT DISTINCT url FROM links WHERE category='coverage_state'") if profile(r['url'],2)}
    with ro(ROOT/'sources/trellis/worker/frontier.sqlite3') as db:
        frontier={r['url']:dict(r) for r in db.execute("SELECT url,status,attempts,error,discovered_from FROM frontier WHERE category='county' AND in_scope=1")}
    browser=[];browser_checks=[]
    for name in ('trellis_browser_backfill_20260918','trellis_browser_backfill_20260918T2213'):
        folder=ROOT/'sources/counties'/name;rows=readl(folder/'resources.jsonl');gate=json.loads((folder/'validation.json').read_text(encoding='utf8'))
        assert gate['status']=='passed' and sha(folder/'resources.jsonl')==gate['resources_sha256']
        for r in rows:
            for key,digest in (('raw_path','sha256'),('text_path','text_sha256'),('metadata_path','metadata_sha256')):
                assert sha(ROOT/r[key])==r[digest]
            assert profile(r['source_url']) and r['source_url'] not in counties
            dom=json.loads((ROOT/r['raw_path']).read_text(encoding='utf8'))
            browser.append(r)
            browser_checks.append({'url':r['source_url'],'county':r['county'],'state':r['state'],'geoid':r['county_geoids'][0],
                                   'fields':[h['text'] for h in dom.get('dom_profile_headings',[]) if h.get('tag')=='h2'],'captured_at':r['captured_at'],
                                   'raw_representation_kind':r['raw_representation_kind'],'verified_artifacts':3})
    known=set(proofs)|set(counties)
    saved=set(counties)|{r['source_url'] for r in browser}
    gaps=known-saved
    quality=Counter();field_counts=Counter()
    for r in counties.values():
        fields=json.loads(r.get('fields_json') or '{}')
        field_counts.update(k for k,v in fields.items() if v is not None and str(v).strip())
        quality['empty_field_objects'] += not bool(fields)
        quality['source_files_present'] += bool(pages.get(r['url'],{}).get('source_path') and (ROOT/pages[r['url']]['source_path']).is_file())
        quality['canonical_website_present'] += bool(r.get('official_website'))
        quality['truncated_display_website'] += '…' in str(fields.get('website','')) or '...' in str(fields.get('website',''))
        quality['raw_title_needs_whitespace_cleanup'] += r['title'] != ' '.join(r['title'].split())
    rawdir=ROOT/'sources/trellis_coverage_20260919/raw';logs=readl(rawdir/'_call_log.jsonl')
    rawrows=[]
    for f in sorted(rawdir.glob('*get_state_coverage*.response.json')):
        d=json.loads(f.read_text(encoding='utf8'));state=f.stem.rsplit('_',1)[1].split('.')[0]
        rawrows.append({'state':state,'path':str(f.relative_to(ROOT)).replace('\\','/'),'sha256':sha(f),'error':d.get('error'),
                        'county_rows':len(d.get('counties',[])), 'names_unique':len({c['county_name'] for c in d.get('counties',[])}),
                        'documents_true':sum(c.get('has_documents') is True for c in d.get('counties',[])),
                        'courthouse_count_zero':sum(c.get('courthouse_count')==0 for c in d.get('counties',[]))})
    missing_receipts=[r for r in logs if not (rawdir/r['response_file']).is_file()]
    field_quality={'catalog_profiles':len(counties),'field_presence':dict(field_counts),'checks':dict(quality),
                   'website_status_counts':dict(Counter(r.get('website_validation_status') for r in counties.values())),
                   'browser_captures':browser_checks,
                   'qualification':'Population, officials, websites and coverage flags are publisher claims, not current ground truth; no judge-person identity or paid document entitlement is inferred.'}
    bystate=Counter(urlsplit(u).path.split('/')[2] for u in gaps)
    candidates=[]
    for url in sorted(gaps):
        f=frontier.get(url,{})
        for proof in proofs[url]:
            p=pages.get(proof['source_url'],{})
            if f.get('attempts')==0 and f.get('status')=='pending' and p.get('source_path') and (ROOT/p['source_path']).is_file() and re.search(r'\b(county|parish)\b',proof.get('label',''),re.I):
                candidates.append({'url':url,'state_slug':urlsplit(url).path.split('/')[2],'observed_link':proof,'parent_page':p,'frontier':f})
                break
    selected=[];used_states=set()
    for c in sorted(candidates,key=lambda r:(-bystate[r['state_slug']],r['url'])):
        if c['state_slug'] in used_states: continue
        selected.append(c);used_states.add(c['state_slug'])
        if len(selected)==10: break
    if len(selected)<10:
        selected_urls={r['url'] for r in selected}
        selected += [r for r in candidates if r['url'] not in selected_urls][:10-len(selected)]
    for rank,c in enumerate(selected,1):
        parent=ROOT/c['parent_page']['source_path']
        c['priority']=rank;c['parent_source_sha256']=sha(parent)
        c['reason']='Unattempted exact observed county/parish URL with saved parent-link evidence; spread among states with the most remaining known URL gaps.'
        c['county_geoid']=None;c['county_geoid_reason']='Must be joined from the visible county heading, state breadcrumb and observed label before publication; URL slug alone is insufficient.'
        c['next_action']='Ordinary authorized browser visit or verified-free coverage connector call. Stop at access barriers; capture only visible profile metadata. No cases, guesses, broad crawl or credit-consuming judge tools.'
    state_saved={u for u,p in pages.items() if p['category']=='coverage_state' and p['status']==200 and profile(u,2)}
    with ro(ROOT/'delivery/archive-directory/directory.sqlite3') as db:
        published_browser=db.execute("SELECT count(*) FROM browse WHERE dataset='trellis_browser_counties' AND kind='coverage_county'").fetchone()[0]
    suspicious=[u for u in sorted(gaps) if re.search(r'\.(org|com|gov|net)$',urlsplit(u).path,re.I)]
    summary={'audited_at':datetime.now(timezone.utc).isoformat(),'network_requests':0,
             'county_url_denominator':{'basis':'Distinct valid state/DC county-profile URLs observed in catalog links or saved county profiles. Not Census counties and not all possible Trellis URLs.',
                'known':len(known),'catalog_saved':len(counties),'browser_saved':len(browser),'saved_union':len(saved),'remaining':len(gaps),'saved_percent':round(100*len(saved)/len(known),2),
                'remaining_by_state':dict(sorted(bystate.items())),'frontier_gap_statuses':dict(Counter(frontier.get(u,{}).get('status','not_in_frontier') for u in gaps)),
                'eligible_unattempted_parent_proven_candidates':len(candidates),'published_browser_records':published_browser,
                'known_website_link_artifacts_needing_exclusion':suspicious,
                'gap_count_after_excluding_website_link_artifacts':len(gaps)-len(suspicious),
                'denominator_after_excluding_website_link_artifacts':len(known)-len(suspicious)},
             'state_url_denominator':{'known_observed':len(state_links|state_saved),'saved':len(state_saved),'remaining_observed':sorted(state_links-state_saved),
                 'note':'No new state URL is invented for states not observed in this catalog. Missing free-connector state metadata is a separate measure.'},
             'free_connector_partial':{'response_files':len(list(rawdir.glob('*.response.json'))),'state_response_files':len(rawrows),
                 'state_nonerror_responses':sum(not r['error'] for r in rawrows),'state_county_rows_total':sum(r['county_rows'] for r in rawrows),
                 'state_response_codes':[r['state'] for r in rawrows],'call_log_entries':len(logs),'logged_responses_missing':missing_receipts,
                 'county_detail_scout_saved':'reports/corpus_upgrade_20260919/understand/connector_samples/14_trellis_get_county_coverage_nj_middlesex.response.json',
                 'adapter_exists':(ROOT/'delivery/archive-directory/trellis_coverage.py').exists(),
                 'validation_exists':(ROOT/'sources/trellis_coverage_20260919/validation.json').exists()},
             'prior_gap_note':{'reported':1073,'current':len(gaps),'reason':'Earlier note counted only the first three browser captures; the second three are already published.'},
             'selected_next_urls':len(selected),'limitations':['No live access or current entitlement check performed.',
                 'Connector state files include compact agent-transcribed responses; label reconstructed connector data where verbatim capture is not evidenced.',
                 'Zero courthouse counts and has_documents flags do not prove absent courthouses or downloaded documents.',
                 'Existing test_trellis_coverage.py is a design fixture; without its adapter it does not establish readiness.']}
    write('report.json',summary);write('profile_field_quality.json',field_quality);write('free_connector_receipts.json',rawrows)
    writel('next_10_observed_urls.jsonl',selected)
    writel('remaining_observed_county_urls.jsonl',[{'url':u,'state_slug':urlsplit(u).path.split('/')[2],'status':frontier.get(u,{}).get('status'),'attempts':frontier.get(u,{}).get('attempts')} for u in sorted(gaps)])
    print(json.dumps(summary,ensure_ascii=True))

if __name__=='__main__':main()

"""Local-only reconciliation of observed Trellis court scopes with Census geography."""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import re
import unicodedata
import urllib.parse

VERSION='1.0.0'
DEFAULT_ROOT=Path(__file__).resolve().parents[2]
INPUTS={
    'county_profiles':'sources/trellis/catalog/county_profiles.csv',
    'website_csv':'sources/trellis/catalog/official_county_websites.csv',
    'website_jsonl':'sources/trellis/catalog/official_county_websites.jsonl',
    'census':'sources/official_courts/datasets/counties_50_plus_dc.json',
}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def norm(value):
    plain=unicodedata.normalize('NFKD',str(value or '')).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]','',plain)


def clean(value):
    return ' '.join(str(value or '').split())


def entity(name):
    for suffix,kind in [(' City and Borough','city_and_borough'),(' Census Area','census_area'),(' Planning Region','planning_region'),(' Municipality','municipality'),(' County','county'),(' Parish','parish'),(' Borough','borough'),(' city','independent_city')]:
        if name.casefold().endswith(suffix.casefold()):
            return name[:-len(suffix)],kind
    if name=='District of Columbia':return name,'federal_district'
    return name,'county_equivalent_other'


def title_identity(title):
    title=clean(title).split('|')[0].strip()
    circuit=re.match(r'^(.*?\bJudicial Circuit\b.*?)\s+[-\u2013\u2014]\s+(.+)$',title,re.I)
    if circuit:title=circuit[2]
    match=re.match(r'^(.*?)\s+(City and Borough|Census Area|Planning Region|Independent City|County|Parish|Borough|Municipality|City)\b',title,re.I)
    if match:
        kind=match[2].lower().replace(' ','_')
        if kind in ('city','independent_city'):kind='independent_city'
        return clean(match[1]),kind
    match=re.match(r'^City of (.*?)(?:\s+(?:Circuit|Superior|District|Court|Records)|$)',title,re.I)
    if match:return clean(match[1]),'independent_city'
    return '',None


def url_value(value):
    raw=str(value or '').strip()
    if not raw:return None,'missing_url'
    if any(c in raw for c in ('\ufffd','\u2026')) or '...' in raw:return None,'truncated_or_corrupted_url'
    if re.search(r'[\x00-\x20\x7f]',raw):return None,'whitespace_or_control_in_url'
    try:
        p=urllib.parse.urlsplit(raw)
        if p.scheme not in ('http','https') or not p.hostname:return None,'unsupported_or_missing_scheme'
        if p.username or p.password:return None,'credential_in_url'
        hostname=p.hostname.lower()
        if not re.fullmatch(r'[a-z0-9.-]+',hostname) or '..' in hostname or '.' not in hostname:return None,'invalid_hostname'
        port=p.port
        host=hostname if port is None or (p.scheme,port) in (('http',80),('https',443)) else hostname+':'+str(port)
        if hostname in ('trellis.law','www.trellis.law'):return None,'internal_trellis_url'
        return urllib.parse.urlunsplit((p.scheme,host,p.path or '/',p.query,'')),'valid_observed_url'
    except ValueError:return None,'invalid_url'


class GeographyIndex:
    def __init__(self,baseline):
        self.baseline=baseline
        self.states={}
        self.full=collections.defaultdict(list)
        self.base=collections.defaultdict(list)
        self.aliases=collections.defaultdict(list)
        seen=set()
        for record in baseline:
            if not re.fullmatch(r'\d{5}',str(record.get('geoid',''))) or record['geoid'] in seen:
                raise ValueError('Census baseline has a missing, invalid, or duplicate GEOID')
            seen.add(record['geoid'])
            if record['geoid']!=record['state_fips']+record['county_fips']:
                raise ValueError('Census component FIPS codes do not match GEOID')
            state=record['state']
            for key in (state,record['usps'],record['state_fips']):self.states[norm(key)]=state
            base,kind=entity(record['name'])
            item={**record,'entity_kind':kind,'base_name':base}
            self.full[(state,norm(record['name']))].append(item)
            self.base[(state,norm(base))].append(item)
            # Only explicit Saint/Sainte spelling variants; never fuzzy similarity.
            if re.match(r'^St[.\s]',base,re.I):
                self.aliases[(state,'saint'+norm(re.sub(r'^St[.\s]+','',base,flags=re.I)))].append(item)
            if re.match(r'^Ste[.\s]',base,re.I):
                self.aliases[(state,'sainte'+norm(re.sub(r'^Ste[.\s]+','',base,flags=re.I)))].append(item)

    def match(self,row):
        source_url=row.get('url','')
        parts=urllib.parse.urlsplit(source_url).path.strip('/').split('/')
        url_state=parts[1] if len(parts)>=3 and parts[0]=='coverage' else ''
        url_county=parts[2] if len(parts)>=3 and parts[0]=='coverage' else ''
        source_state=row.get('state') or url_state
        source_county=row.get('county_slug') or url_county
        state=self.states.get(norm(source_state))
        title_name,title_kind=title_identity(row.get('title',''))
        circuit=re.match(r'^(.*?\bJudicial Circuit\b.*?)\s+[-\u2013\u2014]\s+',clean(row.get('title','')),re.I)
        result={'source_url':source_url,'source_state':source_state,'source_county_slug':source_county,'source_title':clean(row.get('title','')),'source_court_scope':circuit[1] if circuit else None,'title_name':title_name,'title_entity_kind':title_kind,'state':state,'match_status':'unmatched','match_method':None,'reason':None,'census_geoid':None,'state_fips':None,'county_fips':None,'census_name':None,'census_entity_kind':None,'geography_vintage':2026,'candidate_geoids':[],'candidate_names':[]}
        if not state:
            if norm(source_state) in ('federal','us','unitedstates'):
                return {**result,'match_status':'non_census_jurisdiction','reason':'federal_court_outside_state_county_baseline','source_jurisdiction_kind':'federal_court_scope'}
            return {**result,'reason':'unknown_state_name'}
        if url_state and self.states.get(norm(url_state))!=state:
            return {**result,'match_status':'ambiguous','reason':'state_field_and_source_url_conflict'}
        if url_county and norm(url_county)!=norm(source_county):
            return {**result,'match_status':'ambiguous','reason':'county_slug_and_source_url_conflict'}
        key=(state,norm(source_county))
        candidates=self.full.get(key,[])
        method='exact_normalized_full_name'
        if not candidates:
            candidates=self.base.get(key,[])
            method='exact_state_and_county_base_name'
        if not candidates:
            candidates=self.aliases.get(key,[])
            method='explicit_saint_spelling_variant'
        result['candidate_geoids']=[c['geoid'] for c in candidates]
        result['candidate_names']=[c['name'] for c in candidates]
        if state=='Connecticut' and title_kind=='county' and not candidates:
            return {**result,'match_status':'non_census_jurisdiction','reason':'historical_connecticut_county_not_2026_planning_region','source_jurisdiction_kind':'historical_county_court_scope'}
        if re.search(r'court.?of.?chancery|judicial.?district|circuit.?district|statewide|district.?court',norm(source_county)) and not candidates:
            return {**result,'match_status':'non_census_jurisdiction','reason':'court_or_district_scope_has_no_county_equivalent_match','source_jurisdiction_kind':'special_court_scope'}
        if not candidates:return {**result,'reason':'no_exact_state_county_name_match'}
        if title_kind:
            typed=[c for c in candidates if c['entity_kind']==title_kind]
            if not typed:
                return {**result,'match_status':'ambiguous','reason':'explicit_title_entity_type_conflicts_with_census_type'}
            candidates=typed
        if title_name and norm(title_name)!=norm(source_county):
            # A slug may include the entity suffix; then compare the selected full name.
            agrees=any(norm(title_name)==norm(c['base_name']) and (norm(source_county) in (norm(c['base_name']),norm(c['name'])) or method=='explicit_saint_spelling_variant') for c in candidates)
            if not agrees:return {**result,'match_status':'ambiguous','reason':'title_name_and_county_slug_conflict'}
        if len(candidates)!=1:return {**result,'match_status':'ambiguous','reason':'multiple_county_or_city_candidates'}
        record=candidates[0]
        return {**result,'match_status':'matched','match_method':method+('_with_explicit_entity_type' if title_kind else ''),'reason':'unique_exact_name_association_within_state','census_geoid':record['geoid'],'state_fips':record['state_fips'],'county_fips':record['county_fips'],'census_name':record['name'],'census_entity_kind':record['entity_kind'],'candidate_geoids':[record['geoid']],'candidate_names':[record['name']]}


def safe_cell(value):
    if isinstance(value,(list,dict)):value=json.dumps(value,ensure_ascii=False,sort_keys=True)
    value='' if value is None else str(value)
    return "'"+value if value.startswith(('=','+','-','@','\t','\r')) else value


def write_table(out,name,rows,empty_fields=()):
    fields=[]
    for row in rows:
        for key in row:
            if key not in fields:fields.append(key)
    if not fields:fields=list(empty_fields) or ['status','reason']
    with (out/(name+'.jsonl')).open('w',encoding='utf-8',newline='\n') as stream:
        for row in rows:stream.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n')
    with (out/(name+'.csv')).open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        for row in rows:writer.writerow({key:safe_cell(row.get(key)) for key in fields})


def parse_json(value,default):
    try:return json.loads(value) if isinstance(value,str) and value else default
    except (ValueError,TypeError):return default


def input_snapshot(root,out):
    data,manifest={},{}
    snapshot=out/'input_snapshots'
    snapshot.mkdir(exist_ok=True)
    for key,relative in INPUTS.items():
        path=root/relative
        before=path.stat()
        raw=path.read_bytes()
        after=path.stat()
        if before.st_mtime_ns!=after.st_mtime_ns or before.st_size!=after.st_size:
            raise RuntimeError('Input changed while being read: '+relative+'; rerun after the catalog pass finishes')
        saved=snapshot/(key+path.suffix)
        saved.write_bytes(raw)
        manifest[key]={'source_path':relative,'snapshot_path':str(saved.relative_to(root)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'source_modified_at':dt.datetime.fromtimestamp(after.st_mtime,dt.timezone.utc).isoformat()}
        text=raw.decode('utf-8-sig')
        if path.suffix=='.csv':data[key]=list(csv.DictReader(io.StringIO(text,newline='')))
        elif path.suffix=='.jsonl':data[key]=[json.loads(line) for line in text.splitlines() if line.strip()]
        else:data[key]=json.loads(text)
    return data,manifest


def reconcile(root=DEFAULT_ROOT):
    root=Path(root).resolve()
    out=root/'reports'/'geography'
    out.mkdir(parents=True,exist_ok=True)
    data,inputs=input_snapshot(root,out)
    baseline=data['census'];profiles=data['county_profiles']
    index=GeographyIndex(baseline)
    reconciled=[index.match(row) for row in profiles]
    by_source={row['source_url']:row for row in reconciled}
    profile_by_source={row['url']:row for row in profiles}
    matches=[row for row in reconciled if row['match_status']=='matched']
    ambiguities=[row for row in reconciled if row['match_status']=='ambiguous']
    non_census=[row for row in reconciled if row['match_status']=='non_census_jurisdiction']
    unmatched=[row for row in reconciled if row['match_status'] not in ('matched','ambiguous')]
    matched_geoids={row['census_geoid'] for row in matches}
    missing=[]
    for county in baseline:
        if county['geoid'] in matched_geoids:continue
        _,kind=entity(county['name'])
        reason='no_observed_profile_matched_in_this_snapshot'
        if county['state']=='Connecticut':reason='2026_planning_region_not_matched_by_historical_county_court_profiles'
        missing.append({**county,'census_entity_kind':kind,'missing_reason':reason,'meaning':'Missing from the collected, name-matched profile snapshot; no claim about Trellis or official source availability'})
    states=[]
    for state in sorted({r['state'] for r in baseline}):
        census=[r for r in baseline if r['state']==state]
        rows=[r for r in reconciled if r['state']==state]
        matched={r['census_geoid'] for r in rows if r['match_status']=='matched'}
        states.append({'state':state,'usps':census[0]['usps'],'state_fips':census[0]['state_fips'],'census_counties_or_equivalents':len(census),'observed_profiles':len(rows),'matched_profiles':sum(r['match_status']=='matched' for r in rows),'matched_unique_geoids':len(matched),'ambiguous_profiles':sum(r['match_status']=='ambiguous' for r in rows),'non_census_court_scopes':sum(r['match_status']=='non_census_jurisdiction' for r in rows),'unmatched_profiles':sum(r['match_status']=='unmatched' for r in rows),'missing_census_geographies':len(census)-len(matched),'census_entity_kinds':dict(collections.Counter(entity(r['name'])[1] for r in census))})
    observations={}
    for key in ('website_csv','website_jsonl'):
        for number,row in enumerate(data[key],2 if key=='website_csv' else 1):
            source=row.get('discovered_from','');url=row.get('url','')
            entry=observations.setdefault((source,url),{'source_url':source,'observed_url':url,'state':row.get('state'),'county_slug':row.get('county_slug'),'displayed_value':row.get('displayed_value'),'website_validation_status':row.get('website_validation_status'),'website_provenance':parse_json(row.get('website_provenance_json'),{}),'observed_in':[]})
            entry['observed_in'].append({'path':INPUTS[key],'record_number':number})
    for number,row in enumerate(profiles,2):
        if not row.get('official_website'):continue
        key=(row['url'],row['official_website'])
        entry=observations.setdefault(key,{'source_url':row['url'],'observed_url':row['official_website'],'state':row.get('state'),'county_slug':row.get('county_slug'),'displayed_value':row.get('official_website_display'),'website_validation_status':row.get('website_validation_status'),'website_provenance':parse_json(row.get('website_provenance_json'),{}),'observed_in':[]})
        entry['observed_in'].append({'path':INPUTS['county_profiles'],'record_number':number})
    associations=[];website_issues=[];seeds=[]
    shared_urls=collections.defaultdict(set)
    for entry in observations.values():
        match=by_source.get(entry['source_url'])
        url,validation=url_value(entry['observed_url'])
        profile=profile_by_source.get(entry['source_url'],{})
        display=entry.get('displayed_value') or profile.get('official_website_display') or parse_json(profile.get('fields_json'),{}).get('website') or ''
        display_url,display_status=url_value(display)
        government_signal='unknown'
        if url:
            host=urllib.parse.urlsplit(url).hostname
            government_signal='gov_namespace' if host.endswith('.gov') else ('state_or_local_us_namespace' if re.search(r'\.(?:[a-z]{2})\.us$',host) else 'non_gov_namespace')
        association={**entry,'displayed_value':display,'canonical_url':url,'url_validation':validation,'displayed_url_validation':display_status,'display_differs_from_href':bool(display and url and display_url!=url),'state':match['state'] if match else index.states.get(norm(entry.get('state'))),'county_association_status':match['match_status'] if match else 'missing_profile','county_association_reason':match['reason'] if match else 'website_export_has_no_county_profile','census_geoid':match['census_geoid'] if match else None,'census_name':match['census_name'] if match else None,'authority_classification':'trellis_reported_government_site','site_authority_verified':False,'government_namespace_signal':government_signal,'authority_note':'Trellis Website field is an observed claim. Census verifies the county-name association, not ownership or authority of the website.'}
        if match and (index.states.get(norm(entry.get('state')))!=match['state'] or norm(entry.get('county_slug'))!=norm(match['source_county_slug'])):
            association['county_association_status']='ambiguous_export_profile_conflict'
            association['county_association_reason']='website_export_state_or_county_conflicts_with_matched_profile'
        associations.append(association)
        if url and association['county_association_status']=='matched':
            shared_urls[url].add(association['census_geoid'])
            seed={'url':url,'source_family':'trellis_reported_official_county_website','jurisdiction':{'country':'US','state':match['state'],'state_fips':match['state_fips'],'county':match['census_name'],'county_fips':match['county_fips'],'geoid':match['census_geoid'],'geography_vintage':2026,'entity_kind':match['census_entity_kind']},'category':'county_government_website_to_verify','source_category':'observed_external_website_from_trellis_public_provider_extract','discovered_from':entry['source_url'],'association_status':'verified_exact_name_association_to_census','match_method':match['match_method'],'authority_classification':'trellis_reported_government_site','site_authority_verified':False,'government_namespace_signal':government_signal,'provenance':{'county_profiles_snapshot_sha256':inputs['county_profiles']['sha256'],'census_snapshot_sha256':inputs['census']['sha256'],'observed_in':entry['observed_in'],'website_field':entry.get('website_provenance') or parse_json(profile.get('website_provenance_json'),{}),'displayed_value':display,'observed_href':entry['observed_url']},'scope':{'host':urllib.parse.urlsplit(url).netloc,'path_prefixes':['/']}}
            seeds.append(seed)
        else:
            website_issues.append(association)
    present_sources={entry['source_url'] for entry in observations.values()}
    for profile in profiles:
        if profile['url'] in present_sources:continue
        match=by_source[profile['url']]
        website_issues.append({'source_url':profile['url'],'state':match['state'],'county_slug':profile['county_slug'],'census_geoid':match['census_geoid'],'census_name':match['census_name'],'county_association_status':match['match_status'],'url_validation':profile.get('website_validation_status') or 'missing_website','displayed_value':profile.get('official_website_display') or parse_json(profile.get('fields_json'),{}).get('website'),'website_provenance':parse_json(profile.get('website_provenance_json'),{})})
    unique_seeds={}
    for seed in seeds:
        key=(seed['url'],seed['jurisdiction']['geoid'])
        seed['shared_observed_url_geoids']=sorted(shared_urls[seed['url']])
        unique_seeds.setdefault(key,seed)
    seeds=sorted(unique_seeds.values(),key=lambda r:(r['jurisdiction']['geoid'],r['url']))
    duplicate_geographies=[]
    grouped=collections.defaultdict(list)
    for row in matches:grouped[row['census_geoid']].append(row)
    for geoid,rows in grouped.items():
        if len(rows)>1:duplicate_geographies.append({'census_geoid':geoid,'census_name':rows[0]['census_name'],'profile_urls':[r['source_url'] for r in rows],'profile_count':len(rows)})
    aliases=[{'source_url':row['source_url'],'state':row['state'],'source_county_slug':row['source_county_slug'],'title_name':row['title_name'],'census_name':row['census_name'],'census_geoid':row['census_geoid'],'match_method':row['match_method'],'alias_scope':'State-specific observed spelling/slug mapping; no fuzzy geographic crosswalk'} for row in matches]
    exports={'county_reconciliation':reconciled,'county_matches':matches,'county_ambiguities':ambiguities,'county_unmatched':unmatched,'non_census_jurisdictions':non_census,'census_counties_missing':missing,'state_coverage':states,'county_aliases':aliases,'duplicate_geographies':duplicate_geographies,'website_associations':associations,'website_issues':website_issues,'official_county_website_seeds':seeds}
    for name,rows in exports.items():write_table(out,name,rows)
    website_hosts=sorted({urllib.parse.urlsplit(seed['url']).netloc for seed in seeds})
    website_config={'allow':[{'host':host,'path_prefixes':['/']} for host in website_hosts],'workers':3,'per_host_delay':2.0,'timeout_seconds':30,'max_transfer_seconds':120,'max_response_bytes':16777216,'max_extract_chars':4194304,'min_free_bytes':2147483648,'max_depth':0,'max_retries':1,'respect_robots':True,'follow_links':False,'follow_external_allowed_links':False,'pause_host_on_access_block':True,'user_agent':'LegalCorpusResearch/1.0'}
    (out/'official_county_websites.config.json').write_text(json.dumps(website_config,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    # Required namespace counts are signals only; no public-site verification happened here.
    summary={'generated_at':now(),'reconciliation_version':VERSION,'network_requests':0,'baseline_vintage':2026,'baseline_counties_and_equivalents':len(baseline),'baseline_states_and_dc':len(states),'observed_county_profiles':len(profiles),'matched_profiles':len(matches),'matched_unique_census_geoids':len(matched_geoids),'ambiguous_profiles':len(ambiguities),'non_census_jurisdictions':len(non_census),'unmatched_profiles_total':len(unmatched),'missing_census_geographies_in_snapshot':len(missing),'website_observations_unique':len(associations),'website_export_csv_rows':len(data['website_csv']),'website_export_jsonl_rows':len(data['website_jsonl']),'website_csv_jsonl_url_pairs_agree':{(r.get('discovered_from'),r.get('url')) for r in data['website_csv']}=={(r.get('discovered_from'),r.get('url')) for r in data['website_jsonl']},'website_display_values_recovered_by_observed_href':sum(r['display_differs_from_href'] for r in associations),'website_display_values_truncated_or_corrupted':sum(r['displayed_url_validation']=='truncated_or_corrupted_url' for r in associations),'website_issues':len(website_issues),'ready_website_seed_associations':len(seeds),'unique_ready_website_urls':len({r['url'] for r in seeds}),'government_namespace_signals':dict(collections.Counter(r['government_namespace_signal'] for r in seeds)),'trellis_reported_government_site_associations':len(seeds),'independently_verified_government_site_associations':0,'full_corpus_complete':False,'meaning':'All counts describe the captured input snapshot. Missing means not matched in this collection, not absent from Trellis, courts, or government sites. Website authority remains unverified until checked against an independent official source.','inputs':inputs,'outputs':{name:{'rows':len(rows),'jsonl':f'reports/geography/{name}.jsonl','csv':f'reports/geography/{name}.csv'} for name,rows in exports.items()}}
    summary['website_seed_config']='reports/geography/official_county_websites.config.json'
    summary['website_seed_allowed_hosts']=len(website_hosts)
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('inputs','outputs')},ensure_ascii=False,indent=2))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,default=DEFAULT_ROOT)
    reconcile(parser.parse_args().workspace)

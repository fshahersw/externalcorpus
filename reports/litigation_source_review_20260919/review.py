"""Parse literal JSON only; never execute the supplied HTML/JavaScript."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import sqlite3
from urllib.parse import urlsplit
from lxml import html

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REQUESTED = Path('C:/Users/firas/Downloads/litigation/_source/_browser.html')
FOUND = Path('C:/Users/firas/Downloads/litigation_source_browser.html')
REGISTRY = Path('C:/Users/firas/Downloads/registry_v06_1.sqlite')


def stamp(path):
    s = path.stat()
    return {'path': str(path), 'bytes': s.st_size, 'mtime_utc': datetime.fromtimestamp(s.st_mtime,timezone.utc).isoformat(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def literal(script, name):
    match = re.search(r'\bconst '+re.escape(name)+r'\s*=\s*',script)
    if not match: raise ValueError('Missing literal '+name)
    value,end = json.JSONDecoder().raw_decode(script[match.end():])
    if not script[match.end()+end:].lstrip().startswith(';'): raise ValueError('Unexpected literal terminator')
    return value


def main():
    raw = FOUND.read_bytes(); doc = html.fromstring(raw)
    scripts = doc.xpath('//script')
    assert len(scripts)==1 and scripts[0].get('src') is None
    script = scripts[0].text or ''
    data, labels = literal(script,'DATA'),literal(script,'M')
    assert isinstance(data,list) and isinstance(labels,dict)
    assert all(set(row)=={'n','u','j','l','c','t','k','d','v','x'} for row in data)
    db = sqlite3.connect(REGISTRY.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    registry={r['url']:dict(r) for r in db.execute('SELECT * FROM registry')};db.close()
    urls={r['u'] for r in data}
    assert len(data)==len(urls)==len(registry)==9348 and urls==set(registry)
    field_map={'n':'name','u':'url','j':'jurisdiction','l':'layer','c':'record_category','t':'task_family','k':'content_kind','d':'domain','x':'description'}
    equivalence={k:{'registry_field':v,'exact_matches':sum(r[k]==registry[r['u']][v] for r in data),'compared':len(data)} for k,v in field_map.items()}
    differences=[r for r in data if r['x']!=registry[r['u']]['description']]
    assert all(r['v']==int(bool(registry[r['u']]['verified_date'])) for r in data)
    localrefs=[{'tag':e.tag,'attribute':a,'value':e.get(a)} for e in doc.xpath('//*[@href or @src]') for a in ('href','src') if e.get(a) and not re.match(r'^(?:https?:|data:|#)',e.get(a))]
    catalog=json.loads((ROOT/'sources/public_law_directory_20260919/catalog.json').read_text(encoding='utf-8'))
    categories={r['value']:r for r in catalog['facets']['categories']}
    jurisdictions={r['value']:r for r in catalog['facets']['jurisdictions']}
    category_labels={('uncategorized' if k=='' else k):v for k,v in labels['cats'].items()}
    changes=[{'key':k,'current':row['label'],'candidate':category_labels[k]} for k,row in categories.items() if k in category_labels and row['label']!=category_labels[k]]
    source=stamp(FOUND)
    extracted={'source':source,'extraction':'JSONDecoder over the literal const M object; no JavaScript execution','key_rules':{'jurisdictions':'M.states keys are exact lowercase registry jurisdiction IDs; us and multi are not states.','categories':'M.cats keys match source record_category; blank source key maps to the current directory value uncategorized. Every other ID stays unchanged.','task_families':'M.fams keys match task_family; blank means source display General, not a newly assigned family.','layers':'M.layers keys match layer; blank display Other does not classify the record.','content_kinds':'M.kinds keys match content_kind. PDF/API labels describe reference types, not saved files or operational APIs.'},'jurisdictions':labels['states'],'categories':category_labels,'original_source_category_labels':labels['cats'],'task_families':labels['fams'],'layers':labels['layers'],'content_kinds':labels['kinds'],'compatible_current_category_label_changes':changes,'optional_jurisdiction_label_changes':[{'key':k,'current':v['label'],'candidate':labels['states'].get(k)} for k,v in jurisdictions.items() if labels['states'].get(k)!=v['label']],'not_extracted_for_data_integration':['famColor (presentation styling only)']}
    (HERE/'display_labels.json').write_text(json.dumps(extracted,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    canonical=sqlite3.connect((ROOT/'catalog/documents.sqlite3').as_uri()+'?mode=ro',uri=True)
    canonical_urls={r[0] for r in canonical.execute('SELECT source_url FROM versions UNION SELECT final_url FROM versions')};canonical.close()
    compact=sqlite3.connect((ROOT/'delivery/archive-directory/directory.sqlite3').as_uri()+'?mode=ro',uri=True)
    directory_saved={r[0] for r in compact.execute("SELECT source_url FROM browse WHERE COALESCE(original_id,'')!='' OR COALESCE(text_id,'')!='' OR content_id IS NOT NULL OR inline_text=1")};compact.close()
    pilot_path=ROOT/'sources/public_law_acquisition_20260919/resources.jsonl'
    pilot_urls={r['source_url'] for r in map(json.loads,pilot_path.read_text(encoding='utf-8').splitlines())}
    states=set('al ak az ar ca co ct de fl ga hi id il in ia ks ky la me md ma mi mn ms mo mt ne nv nh nj nm ny nc nd oh ok or pa ri sc sd tn tx ut vt va wa wv wi wy'.split())
    counts={k:dict(Counter(str(r[k]) for r in data)) for k in ['j','l','c','t','k','v']}
    samples=[]
    for category in ['judge_pages','court_rules','statutes_codes','court_forms','api']:
        r=next(r for r in data if r['c']==category)
        samples.append({'name':r['n'],'url':r['u'],'jurisdiction':r['j'],'category':r['c'],'content_kind':r['k'],'registry_id':registry[r['u']]['id'],'exact_registry_match':True})
    out={'reviewed_at':datetime.now(timezone.utc).isoformat(),'requested_path':str(REQUESTED),'requested_path_exists':REQUESTED.exists(),'replacement_basis':'Exact supplied path is missing; filename-only bounded search found the semantically matching standalone litigation_source_browser.html. Parent approved reviewing it.','candidate':source,'title':doc.xpath('string(//title)'),'related_files':[stamp(REGISTRY),stamp(Path('C:/Users/firas/Downloads/publicLaw_directory.md'))],'embedded_data':{'rows':len(data),'unique_urls':len(urls),'fields':field_map,'verified_flag_semantics':'v is exactly bool(verified_date) for all9348 records; it is not exactly HTTP200 and does not prove present availability.','verified_date_flag_count':sum(r['v'] for r in data),'http200_equivalence_matches':sum(r['v']==int(registry[r['u']]['http_status']=='200') for r in data),'field_equivalence':equivalence,'description_differences':{'rows':len(differences),'html_blank':sum(not r['x'] for r in differences),'registry_nonblank':sum(bool(registry[r['u']]['description']) for r in differences),'interpretation':'Current SQLite retains richer descriptions in131 records. Do not overwrite it with compact HTML data.'},'counts':counts},'coverage':{'states_with_reference_rows':len(states & set(counts['j'])),'state_coverage_is_reference_presence_only':True,'other_jurisdictions':sorted(set(counts['j'])-states),'judge_reference_rows':counts['c'].get('judge_pages',0),'structured_judge_profiles':0,'county_identity_fields':[],'full_state_county_enumeration':False,'law_reference_rows':{k:counts['c'].get(k,0) for k in ['statutes_codes','court_rules','standing_orders','regulations_register']},'saved_document_bytes_embedded':False},'images_and_scripts':{'img_elements':len(doc.xpath('//img')),'data_uri_assets':sum((e.get(a) or '').startswith('data:') for e in doc.xpath('//*[@src or @href]') for a in ['src','href']),'external_scripts':len(doc.xpath('//script[@src]')),'fetch_expressions':len(re.findall(r'\bfetch\s*\(',script)),'executed':False},'local_references':localrefs,'duplicates':{'exact_registry_url_overlap':len(urls&set(registry)),'new_urls':len(urls-set(registry)),'canonical_saved_url_matches':len(urls&canonical_urls),'directory_saved_artifact_url_matches':len(urls&directory_saved),'new_pilot_url_matches':len(urls&pilot_urls),'union_exact_saved_matches':len(urls&(canonical_urls|directory_saved|pilot_urls)),'not_an_absence_claim':'URLs unmatched by exact spelling may have aliases, derivatives or captures elsewhere; no recursive corpus scan performed.'},'api_references':{'typed_api':counts['k'].get('api',0),'api_bulk_layer':counts['l'].get('api_bulk',0),'api_category':counts['c'].get('api',0),'credential_fields_present':False,'access_fields_present':False,'new_api_urls':0,'existing_mapping':'reports/public_law_api_review_20260919/api_sources.jsonl'},'filter_semantics':{'jurisdiction':'Strict row.j equality: selecting a state excludes us and multi records. Counts are records, not coverage completeness.','other_filters':'Exact layer/category/task-family/content-kind equality, combined with AND.','verified':'Checks historical boolean v only.','search':'All whitespace-separated terms must occur in concatenated name,description,domain,url; case-insensitive.','facets':'Recomputed with all filters except their own dimension; source code read only.'},'safe_candidates':[{'artifact':'display_labels.json','bytes':(HERE/'display_labels.json').stat().st_size,'sha256':hashlib.sha256((HERE/'display_labels.json').read_bytes()).hexdigest(),'recommended':'Optional label-only humanization on Source directory facets; preserve filter IDs/counts/access semantics.','category_label_changes':len(changes)}],'samples':samples,'verdict':'No new source URLs, documents, images, structured judges, or county corpus. Reuse display-label metadata only; retain richer existing SQLite registry.'}
    (HERE/'inventory.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'candidate_sha256':source['sha256'],'rows':len(data),'new_urls':0,'description_differences':len(differences),'category_label_changes':len(changes),'duplicates':out['duplicates'],'display_labels_bytes':(HERE/'display_labels.json').stat().st_size}))


if __name__=='__main__':main()

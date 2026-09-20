"""Read-only checks for the live additions, without rebuilding any corpus."""
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[2]
BASE='http://127.0.0.1:8769'
checks=[]


def get(path):
    with urlopen(BASE+path,timeout=60) as response:return json.loads(response.read())


def check(label,value):
    assert value,label
    checks.append(label)


def main():
    summary=get('/api/trellis-coverage/summary')
    check('Validated county layer is served',summary.get('available') is True and summary['counties_with_detail']>=17)
    progress=get('/api/trellis-coverage/progress')
    check('Final county URL inventory is reconciled',progress.get('available') is True and progress['saved_county_urls']==2478 and progress['observed_county_urls']==2505 and progress['remaining_county_urls']==27)
    matrix=get('/api/coverage/matrix')
    check('Coverage overview publishes fresh backfill counts',matrix['trellis_progress']['saved_county_urls']==progress['saved_county_urls'] and matrix['totals']['trellis_unsaved_county_profiles']==progress['remaining_county_urls'])
    check('Completed states no longer show stale profile gaps',all('trellis_county_profiles_partial' not in r['gaps'] for r in matrix['rows'] if (r.get('trellis_county_profiles') or {}).get('unsaved')==0))
    virginia=get('/api/coverage/state?state=VA')
    va_progress=get('/api/trellis-coverage/progress?state=VA')
    check('State subpage publishes the same explicit gaps',virginia['trellis_unsaved_profiles']['count']==va_progress['remaining_county_urls'] and set(virginia['trellis_unsaved_profiles']['urls'])==set(va_progress['remaining_urls']))
    jasper=get('/api/trellis-coverage/county?fips=48241')
    check('Exact county identity',jasper['county']=='Jasper County' and jasper['state']=='TX')
    fields=jasper['publisher_reported']
    check('Observed website href preserved',fields['website']=='https://www.co.jasper.tx.us/')
    check('Administration address not promoted to courthouse',fields['administration_address'] and fields['court_address'] is None)
    check('Capture and unknown source currency distinct',jasper['captured_at'] and jasper['source_as_of'] is None)
    county=get('/api/counties?q=48241&limit=1')['items'][0]
    check('New profile reflected in county counts',county['saved_profiles']>=1 and county['has_trellis_detail'] is True)
    filtered=get('/api/counties?availability=trellis_details&limit=10')
    check('Refreshed county availability filter',filtered['total']>=16 and all(r['has_trellis_detail'] for r in filtered['items']))
    check('Unknown FIPS has no invented profile',get('/api/trellis-coverage/county?fips=00000')=={'available':False})
    linked=get('/api/judges?has=reports&limit=60')
    check('Report-only filter contains exactly mapped entities',linked['total']==308 and all(r['report_link_count']>0 for r in linked['items']))
    photos=get('/api/judges?has=photo&limit=60')
    check('Eight installed portraits appear in the live filter',photos['total']==51)
    bannon=get('/api/judges?q=Terry%20Bannon&has=reports')['items'][0]
    profile=get('/api/judge?id='+bannon['id'])
    check('Dashboard links are not analytic measures',len(profile['analysis_references'])==5 and profile['analysis_count']==0 and not profile['analyses'])
    check('References use explicit link-only availability',all(r['availability']=='publisher_link' for r in profile['analysis_references']))
    text=json.dumps(jasper)
    check('County API does not disclose absolute workspace paths','C:\\Users' not in text and 'C:/Users' not in text)
    # This is the external-agent directory publication; sidecar additions must not rewrite it.
    check('Main directory database size preserved',(ROOT/'delivery/archive-directory/directory.sqlite3').stat().st_size==1328373760)
    result={'status':'passed','checked_at':datetime.now(timezone.utc).isoformat(),'checks':checks,
            'trellis_summary':summary,'trellis_progress':{k:v for k,v in progress.items() if k not in {'states','remaining_urls'}},
            'refreshed_county_filter_total':filtered['total'],'report_link_profiles':linked['total'],'judge_portraits':photos['total']}
    (Path(__file__).parent/'live_verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':result['status'],'checks_passed':len(checks),'saved_profile_urls':progress['saved_county_urls'],
        'observed_profile_urls':progress['observed_county_urls'],'url_gaps':progress['remaining_county_urls'],
        'county_filter_total':filtered['total'],'report_link_profiles':linked['total'],'judge_portraits':photos['total']}))


if __name__=='__main__':main()

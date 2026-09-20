"""Offline fixtures for source-block selection, mobile duplication and metrics."""
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('profile_normalizer', Path(__file__).with_name('normalize.py'))
n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)

BASE = '''<ol class="breadcrumb"><li><a data-category="state" href="/coverage/arizona">Arizona</a></li></ol>
<h1>Judge Example Judge: Professional Background and Legal Expertise</h1>
<h2>Biography</h2><p>Example Judge was appointed to the bench on January 2, 2020.</p>
<h2>Recent Cases by Hon. Example Judge</h2><p>Case status: Active; 12 files; 95% complete.</p><a href="https://trellis.law/case/123/example">Example case</a>
<h2>About</h2><table><tr><td><span class="judge-about-key">Education</span><span class="judge-about-value">Duplicate mobile value</span></td><td>J.D., Example University<br>B.A., Example College</td></tr></table>
<h2>Court Info</h2><table><tr><th>Current Court:</th><td>AZ - Example Superior Court</td></tr></table>
<h2>Career History</h2><table><tr><th>Role</th><th>Employer</th><th>Where</th></tr><tr><td>Judge</td><td>Example Superior Court</td><td>Example County, Arizona</td></tr></table>
<h2>Analytics</h2>{analytics}<a href="/judge-dashboard/example.judge/at-a-glance/preview">Preview</a>'''


def run(html):
    data = {'metadata': {'sourceURL': 'https://trellis.law/judge/example.judge', 'url': 'https://trellis.law/judge/example.judge', 'statusCode': 200}, 'html': html, 'markdown': ''}
    return n.normalize_capture(data, 'synthetic_fixture.json', json.dumps(data).encode())


complete = '<table><tr><th>Metric</th><th>Value</th><th>Period</th><th>Denominator</th></tr><tr><td>Granted motions</td><td>40%</td><td>2024</td><td>100 decisions</td></tr></table>'
p, f, links, gaps, metrics, candidates, tables = run(BASE.format(analytics=complete))
assert p['reported_name'] == 'Example Judge'
assert p['reported_state'] == 'Arizona' and p['reported_county'] == 'Example County'
assert p['education'] == ['J.D., Example University', 'B.A., Example College']
assert 'Recent Cases' not in p['biography'] and '12 files' not in p['biography']
assert len(metrics) == 1 and metrics[0]['value_as_reported'] == '40%'
assert p['independently_computed_statistics'] is None
assert len(links) == 1 and links[0]['access_status'].startswith('observed_link_only')
assert p['saved_related_case_links_not_acquired'] == 1
incomplete = '<table><tr><th>Metric</th><th>Value</th></tr><tr><td>Granted motions</td><td>40%</td></tr></table>'
p, f, links, gaps, metrics, candidates, tables = run(BASE.format(analytics=incomplete))
assert p['directly_reported_analytics'] is None and not metrics and len(candidates) == 1
p, *_ = run('<h1>Judge Example Judge: Professional Background and Legal Expertise</h1><h2>Biography</h2><p>Subscribe to view this biography.</p>')
assert p['biography'] is None and p['status'] == 'partial_profile'
assert p['reported_county'] is None and p['directly_reported_analytics'] is None
for value in [
    'After graduating from law school, Example began her legal career as a deputy city attorney.',
    'Following graduation, Example practiced as a lawyer.',
    'Example served on the Bar Law School Division committee.',
    'Example prosecuted first-degree murder cases.',
]:
    p, f, *_ = run('<h1>Judge Example Judge</h1><h2>Biography</h2><p>' + value + '</p>')
    assert not any(x['field'] == 'education_passage' for x in f), value
    assert p['biography'] == value
for value in [
    'Example received a B.A. in history from Example College.',
    'Example completed a J.D. at Example University.',
    'Example received a law degree from Example University.',
    'Example earned a Juris Doctor in 2000.',
    'Example graduated from Watson Chapel High School.',
    'Example received a B.B.A. and an LL.B. from Example College.',
]:
    p, f, *_ = run('<h1>Judge Example Judge</h1><h2>Biography</h2><p>' + value + '</p>')
    assert any(x['field'] == 'education_passage' for x in f), value

# Saved personal paragraphs retain their complete biographies and education
# facts, but a negated presiding transition does not become a service assertion.
for value in [
    'Anderson and his wife, Lois, have two adult children. When not presiding over legal proceedings, he enjoys cross country skiing, snowshoeing, hiking, canoeing, boating, and golfing.',
    'Chiles was born and raised in Cabell County, where he graduated from Huntington High School. He and his wife, Michaela, have three children. When not presiding over legal proceedings, Chiles is active in his church, attending First United Methodist Church in Huntington.',
    'Her husband, Paul, served as a police lieutenant for the Lake Oswego Police Department. When not presiding over legal proceedings, she is an avid traveler, gardener, and knitter.',
    'Cherry enjoys hunting, fishing, and reading when not presiding over legal proceedings.',
    'When not presiding on the bench, Auslander is an avid runner, having competed in marathons and ultra-marathons.',
    'When not presiding over legal matters, Jones enjoys coaching youth football, softball, baseball, and basketball.',
    'Her father, the late John Prescott, worked as a prosecutor in Norfolk County as well as a public defender for the Massachusetts Defenders Committee in Boston. When not presiding over legal matters, Cannone enjoys running, cooking, and reading.',
]:
    p, f, *_ = run('<h1>Judge Example Judge</h1><h2>Biography</h2><p>' + value + '</p>')
    assert p['biography'] == value
    assert not p['professional_service_passages']
    assert not any(x['field'] == 'service_or_role_passage' for x in f), value
    assert any(x['field'] == 'biography_passage' and x['value'] == value for x in f)
    if 'graduated from Huntington High School' in value:
        assert any(x['field'] == 'education_passage' for x in f)

for value in [
    'She is the presiding judge of the civil division.',
    'He served on the judicial ethics committee.',
    'Her assignments included criminal and civil matters.',
    'She served as a member of the Advisory Board of the Immigration Justice Project.',
    'When not presiding over legal proceedings, she served on the judicial ethics committee.',
    'Her husband, Paul, served as a police lieutenant. When not presiding over legal proceedings, she served on the judicial ethics committee.',
    'Baumann is a veteran of the United States Army Reserve (1994 to 2002). When not presiding over legal proceedings, he volunteers for Project Angel Heart, delivering meals to homebound patients who struggle from life-threatening illnesses.',
    'When not presiding over legal matters, Beltrami serves as a Northeast Little League Coach and a coach for the Easton High School Mock Trial Team.',
    'When not presiding over legal matters, Bartlett has volunteered with Meals on Wheels. She also sat on the Executive Board for the Elder Justice Center, acting as a liaison with its companion non-profit organization, the Friends of the EJC.',
]:
    p, f, *_ = run('<h1>Judge Example Judge</h1><h2>Biography</h2><p>' + value + '</p>')
    assert p['biography'] == value
    assert p['professional_service_passages'] == [value]
    assert any(x['field'] == 'service_or_role_passage' for x in f), value
role = 'Example served as director of the Immigration Justice Project.'
p, f, *_ = run('<h1>Judge Example Judge</h1><h2>Biography</h2><p>' + role + '</p>')
assert p['biography'] == role and role in p['professional_service_passages']
print('Passed: exact blocks, duplicate cells, metric completeness, nulls, education credentials versus career transitions, and retained Immigration Justice Project role.')

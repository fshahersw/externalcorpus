"""Small regression fixtures for the observed colspan/missing-value trap."""
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('judge_audit', Path(__file__).with_name('audit.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
context = {'source_url': 'https://trellis.law/judges/test'}
table = '''<table><tr><th>Judge Name</th><th>Court</th><th>County</th><th>Status</th><th>Analytics</th></tr>
<tr><td><a href="https://trellis.law/judge/alice.example">Alice Example</a></td><td colspan="2">Example County Superior Court</td><td>Active</td></tr>
<tr><td><a href="https://trellis.law/judge/bob.example">Bob Example</a></td><td colspan="2">Example District Court</td><td></td></tr></table>'''
rows = audit.extract_rows(table, context)
assert len(rows) == 2
assert rows[0]['reported_status'] == 'Active'
assert rows[0]['reported_county'] is None
assert rows[0]['reported_court'] is None
assert rows[0]['reported_court_county_combined'] == 'Example County Superior Court'
assert rows[0]['analytics_cell'] is None
assert rows[1]['reported_status'] is None
assert not any(r['numeric_analytics_observed'] for r in rows)
print('Passed: colspan alignment and missing status/analytics remain null.')

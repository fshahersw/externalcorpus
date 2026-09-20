"""Re-use the reviewed exact-link preparation with a smaller finite county batch."""
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parents[3]
PREPARER = ROOT / 'reports/county_law_focus_20260914/heartbeats/20260918T1622/prepare_county_substantive_documents.py'
spec = importlib.util.spec_from_file_location('county_substantive_preparer', PREPARER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.LIMIT = 30
module.PER_COUNTY = 2
prior_classifier = module.classify
def reviewed_classifier(url, anchor):
    # Saved landing associates these links with Seminole, but the literal linked
    # path explicitly names Brevard. Hold for county-association review.
    if '/Brevard_Civil_Trial_Dockets/' in url:
        return None
    return prior_classifier(url, anchor)
module.classify = reviewed_classifier
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
batch = Path('sources/counties/backfill_20260918/batches') / stamp
sys.argv = [str(__file__), '--output-dir', batch.as_posix()]
module.main()
summary_path = ROOT / batch / 'summary.json'
summary = json.loads(summary_path.read_text(encoding='utf8'))
summary['selection_order'] = 'Substantive document priority, then county association; maximum two per county and 30 URLs. Brevard docket links on a Seminole-associated landing withheld for jurisdiction review.'
summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True)+'\n', encoding='utf8')
receipt = {'batch': batch.as_posix(), 'prepared_at': datetime.now(timezone.utc).isoformat(),
           'parent_preparer': PREPARER.relative_to(ROOT).as_posix(),
           'parent_preparer_sha256': hashlib.sha256(PREPARER.read_bytes()).hexdigest(),
           'scope': 'At most 30 exact observed substantive document URLs, maximum two per candidate county association; no link following.',
           'existing_collections_modified': False, 'network_requests': 0}
(ROOT / 'reports/mvp_backfill_20260918/county/preparation_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf8')
print(json.dumps(receipt))

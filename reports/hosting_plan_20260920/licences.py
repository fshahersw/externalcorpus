"""Read-only: groups the published supplements found by inventory.py by their recorded licence reference and export flag.

The point is to see which layers may leave this machine at all before choosing where anything is hosted. Reads validation.json only.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    inventory = json.loads((HERE / 'inventory.json').read_text(encoding='utf-8'))
    groups = defaultdict(lambda: {'layers': 0, 'mb': 0.0, 'folders': []})
    unpublished = {'layers': 0, 'mb': 0.0}
    for row in inventory['supplements']['rows']:
        if row['status'] != 'passed' or row['ready'] is not True:
            unpublished['layers'] += 1
            unpublished['mb'] += row['mb']
            continue
        try:
            gate = json.loads((ROOT / row['folder'] / 'validation.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            gate = {}
        licence = gate.get('license_ref') if isinstance(gate.get('license_ref'), str) else '(none recorded)'
        export = gate.get('export_allowed')
        key = '%s | export_allowed=%s' % (licence[:70], export)
        groups[key]['layers'] += 1
        groups[key]['mb'] += row['mb']
        groups[key]['folders'].append('%s (%.0f MB)' % (row['folder'], row['mb']))
    report = {'published_groups': {key: {'layers': value['layers'], 'mb': round(value['mb'], 1), 'folders': value['folders']} for key, value in sorted(groups.items(), key=lambda kv: -kv[1]['mb'])},
              'not_published': {'layers': unpublished['layers'], 'mb': round(unpublished['mb'], 1)}}
    (HERE / 'licences.json').write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    for key, value in report['published_groups'].items():
        print('%7.0f MB  %3d layers  %s' % (value['mb'], value['layers'], key))
    print('not published:', report['not_published'])


if __name__ == '__main__':
    main()

"""Read-only inventory for the hosting plan (2026-09-20).

Answers, from the file system only: how much of the project is code and how much is data, which files are too large for a git
host, which file NAMES look like credentials (names only, contents are never opened), and how much data the published
supplements need. Nothing is opened except validation.json files. Output: inventory.json beside this script and a printed summary.
"""
from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name('inventory.json')
CODE = {'.py', '.js', '.css', '.html', '.md', '.ps1', '.yml', '.yaml', '.toml', '.sh', '.bat'}
SECRET_HINTS = ('.env', 'credential', 'secret', 'apikey', 'api_key', 'password', '.pem', '.pfx', 'id_rsa')
MB = 1024 * 1024
GIT_FILE_LIMIT = 100 * MB          # a git host such as GitHub rejects any single file above this
RELEASE_ASSET_LIMIT = 2048 * MB    # one release asset


def walk(top):
    stack = [top]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            yield entry.path, entry.name, entry.stat(follow_symlinks=False).st_size
                    except OSError:
                        continue
        except OSError:
            continue


def bucket():
    return {'files': 0, 'bytes': 0}


def ranked(table, limit):
    rows = [{'path': key, 'files': value['files'], 'mb': round(value['bytes'] / MB, 1)} for key, value in table.items()]
    return sorted(rows, key=lambda row: row['mb'], reverse=True)[:limit]


def main():
    started = time.time()
    root = str(ROOT)
    level1, level2, extensions = defaultdict(bucket), defaultdict(bucket), defaultdict(bucket)
    total, code, code_in_delivery = bucket(), bucket(), bucket()
    large, mid, over_asset, secrets, gates = [], bucket(), bucket(), [], []
    for path, name, size in walk(root):
        parts = path[len(root) + 1:].split(os.sep, 2)
        first = parts[0] if len(parts) > 1 else '(top-level files)'
        second = first + '/' + (parts[1] if len(parts) > 2 else '(files)')
        extension = os.path.splitext(name)[1].lower() or '(none)'
        for table, key in ((level1, first), (level2, second), (extensions, extension)):
            table[key]['files'] += 1
            table[key]['bytes'] += size
        total['files'] += 1
        total['bytes'] += size
        if extension in CODE and size < MB:
            code['files'] += 1
            code['bytes'] += size
            if first == 'delivery':
                code_in_delivery['files'] += 1
                code_in_delivery['bytes'] += size
        if size >= GIT_FILE_LIMIT:
            large.append((size, path[len(root) + 1:].replace(os.sep, '/')))
            if size >= RELEASE_ASSET_LIMIT:
                over_asset['files'] += 1
                over_asset['bytes'] += size
        elif size >= 50 * MB:
            mid['files'] += 1
            mid['bytes'] += size
        lowered = name.lower()
        if any(hint in lowered for hint in SECRET_HINTS) and len(secrets) < 120:
            secrets.append(path[len(root) + 1:].replace(os.sep, '/'))
        if name == 'validation.json':
            gates.append(path)

    supplements = []
    for gate_path in sorted(gates):
        folder = os.path.dirname(gate_path)
        row = {'folder': folder[len(root) + 1:].replace(os.sep, '/'), 'status': None, 'ready': None, 'data_files': 0, 'mb': 0.0, 'missing': 0, 'over_100mb': 0}
        try:
            with open(gate_path, encoding='utf-8') as handle:
                gate = json.load(handle)
            row['status'], row['ready'] = gate.get('status'), gate.get('ready')
            for item in gate.get('data_files') or []:
                if not isinstance(item, dict) or not item.get('path'):
                    continue
                row['data_files'] += 1
                try:
                    size = os.path.getsize(os.path.join(folder, item['path']))
                except OSError:
                    row['missing'] += 1
                    continue
                row['mb'] += size / MB
                row['over_100mb'] += size >= GIT_FILE_LIMIT
        except (OSError, ValueError, AttributeError):
            row['status'] = 'unreadable'
        row['mb'] = round(row['mb'], 1)
        supplements.append(row)

    large.sort(reverse=True)
    report = {
        'root': root.replace(os.sep, '/'), 'seconds': round(time.time() - started, 1),
        'total': {'files': total['files'], 'gb': round(total['bytes'] / MB / 1024, 2)},
        'code_under_1mb': {'files': code['files'], 'mb': round(code['bytes'] / MB, 1), 'of_which_delivery_mb': round(code_in_delivery['bytes'] / MB, 1)},
        'files_over_100mb': {'files': len(large), 'gb': round(sum(size for size, _ in large) / MB / 1024, 2)},
        'files_over_2gb': {'files': over_asset['files'], 'gb': round(over_asset['bytes'] / MB / 1024, 2)},
        'files_50_to_100mb': {'files': mid['files'], 'gb': round(mid['bytes'] / MB / 1024, 2)},
        'level1': ranked(level1, 40), 'level2': ranked(level2, 70), 'extensions': ranked(extensions, 30),
        'largest_files': [{'path': path, 'mb': round(size / MB, 1)} for size, path in large[:80]],
        'secret_looking_names': secrets,
        'supplements': {'count': len(supplements), 'published': sum(1 for row in supplements if row['status'] == 'passed' and row['ready'] is True),
                        'data_gb': round(sum(row['mb'] for row in supplements) / 1024, 2),
                        'rows': sorted(supplements, key=lambda row: row['mb'], reverse=True)},
    }
    OUT.write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('seconds', 'total', 'code_under_1mb', 'files_over_100mb', 'files_over_2gb', 'files_50_to_100mb')}, indent=1))
    print('supplements:', report['supplements']['count'], 'published:', report['supplements']['published'], 'data GB:', report['supplements']['data_gb'])


if __name__ == '__main__':
    main()

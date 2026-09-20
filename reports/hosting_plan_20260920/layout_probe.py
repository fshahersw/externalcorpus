"""Read-only: facts needed to design the git/data split. Names and counts only; no file contents are read."""
from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def count_depth(top):
    direct, nested = Counter(), 0
    for entry in os.scandir(ROOT / top):
        if entry.is_dir(follow_symlinks=False):
            for child in os.scandir(entry.path):
                if child.is_file(follow_symlinks=False):
                    direct[os.path.splitext(child.name)[1].lower() or '(none)'] += 1
                else:
                    nested += 1
    return direct, nested


for top in ('sources', 'corpus'):
    direct, nested = count_depth(top)
    print(top, 'folders:', sum(1 for e in os.scandir(ROOT / top) if e.is_dir()), '| files directly inside a folder:', sum(direct.values()), '| nested dirs:', nested)
    print('   by extension:', dict(direct.most_common(14)))

print('--- delivery/archive-directory (non-code files)')
for entry in sorted(os.scandir(ROOT / 'delivery/archive-directory'), key=lambda e: e.name):
    ext = os.path.splitext(entry.name)[1].lower()
    if entry.is_dir() or ext not in ('.py', '.js', '.css', '.html', '.md'):
        print('   ', entry.name + ('/' if entry.is_dir() else ''), '' if entry.is_dir() else '%.1f MB' % (entry.stat().st_size / 1048576))

print('--- .claude')
for base, dirs, files in os.walk(ROOT / '.claude'):
    depth = len(Path(base).relative_to(ROOT).parts)
    if depth <= 2:
        print('   ', Path(base).relative_to(ROOT).as_posix() + '/', len(files), 'files', [f for f in files][:6])

print('--- devvvv (top level, and env-like file names outside node_modules)')
print('   ', sorted(e.name + ('/' if e.is_dir() else '') for e in os.scandir(ROOT / 'devvvv'))[:60])
for base, dirs, files in os.walk(ROOT / 'devvvv'):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.output', '.git')]
    for name in files:
        low = name.lower()
        if low.startswith('.env') or low.endswith(('.pem', '.pfx', '.key', '.dpapi')) or 'secret' in low or 'credential' in low:
            print('    env-like:', (Path(base) / name).relative_to(ROOT).as_posix(), os.path.getsize(Path(base) / name), 'bytes')

print('--- env-like names elsewhere (outside devvvv)')
for base, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ('node_modules', 'devvvv', '.git', 'raw', 'originals')]
    for name in files:
        low = name.lower()
        if low.startswith('.env') or low.endswith(('.pem', '.pfx', '.key', '.dpapi', '.p12')) or low in ('credentials.json', 'secrets.json', 'token.json'):
            print('   ', (Path(base) / name).relative_to(ROOT).as_posix())

print('--- test_artifacts / .tools top level')
for top in ('test_artifacts', '.tools'):
    print('   ', top, sorted(e.name for e in os.scandir(ROOT / top))[:20])

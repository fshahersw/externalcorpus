"""Isolated publication/identity fixtures. No full builders or network are run."""
from contextlib import nullcontext
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = Path(__file__).resolve().parent
FIXTURES = TEST_ROOT / 'fixtures' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
sys.path.insert(0, str(ROOT / 'pipeline'))
sys.path.insert(0, str(ROOT / 'scripts'))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PUBLICATION_SOURCE = ROOT / 'reports/county_law_focus_20260914/rebuild_focused_package.py'
JOIN_SOURCE = ROOT / 'scripts/build_focused_package.py'
publication = load('publication_fixture_module', PUBLICATION_SOURCE)
package = load('county_join_fixture_module', JOIN_SOURCE)


def put(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode())
    return path


def fixture(name, *, ui_present=True):
    root = FIXTURES / name
    root.mkdir(parents=True)
    root.resolve().relative_to(TEST_ROOT.resolve())
    put(root, 'delivery/focused_legal_corpus/summary.json', b'{"version":"old"}\n')
    put(root, 'delivery/focused_legal_corpus/package_files.json', b'{"old":true}\n')
    put(root, 'delivery/focused_legal_corpus/old-only.txt', b'preserved original')
    put(root, 'README.md', b'| Location |\nold guide\n')
    put(root, 'reports/remaining_resume_20260913/scope.json', json.dumps({'latest_user_direction': 'Continue official sources only', 'reviewed_collections': ['corpus/fixture_only'], 'fixture_value': 'old'}) + '\n')
    if ui_present:
        put(root, 'delivery/ui-sketch/data.js', b'old UI data\n')
    return root


def published_files(root):
    names = ['README.md', 'reports/remaining_resume_20260913/scope.json', 'delivery/ui-sketch/data.js']
    names += [p.relative_to(root).as_posix() for p in (root / 'delivery/focused_legal_corpus').rglob('*') if p.is_file()]
    return {name: (root / name).read_bytes() if (root / name).exists() else None for name in names}


class PublicationTests(unittest.TestCase):
    def test_failure_restores_existing_files_and_preserves_failed_package(self):
        root = fixture('rollback_existing')
        old = published_files(root)
        out = root / 'reports/run'; out.mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError, 'fixture publication failure'):
            with publication.PublicationBackup(root, out) as backup:
                put(root, 'delivery/focused_legal_corpus/summary.json', b'new summary')
                put(root, 'delivery/focused_legal_corpus/new-only.txt', b'failed output')
                for name in ['README.md', 'reports/remaining_resume_20260913/scope.json', 'delivery/ui-sketch/data.js']:
                    put(root, name, b'changed sidecar')
                backup.record_owned_scope_update()
                raise RuntimeError('fixture publication failure')
        self.assertEqual(published_files(root), old)
        self.assertEqual((out / 'failed_build_package/new-only.txt').read_bytes(), b'failed output')
        self.assertTrue((out / 'publication_rollback.json').exists())

    def test_failure_restores_absence_of_new_sidecar(self):
        root = fixture('rollback_new_sidecar', ui_present=False)
        out = root / 'reports/run'; out.mkdir(parents=True)
        with self.assertRaises(RuntimeError):
            with publication.PublicationBackup(root, out):
                put(root, 'delivery/ui-sketch/data.js', b'new sidecar from failed build')
                raise RuntimeError('fixture publication failure')
        self.assertFalse((root / 'delivery/ui-sketch/data.js').exists(), 'A failed publication must restore the prior absence of this sidecar.')

    def test_success_keeps_new_package_and_sidecars(self):
        root = fixture('success')
        out = root / 'reports/run'; out.mkdir(parents=True)
        with publication.PublicationBackup(root, out):
            put(root, 'delivery/focused_legal_corpus/summary.json', b'new summary')
            put(root, 'delivery/focused_legal_corpus/new-only.txt', b'published output')
            put(root, 'README.md', b'new guide')
            put(root, 'delivery/ui-sketch/data.js', b'new UI data')
        self.assertEqual((root / 'delivery/focused_legal_corpus/summary.json').read_bytes(), b'new summary')
        self.assertEqual((root / 'delivery/focused_legal_corpus/new-only.txt').read_bytes(), b'published output')
        self.assertEqual((root / 'README.md').read_bytes(), b'new guide')
        self.assertEqual((out / 'previous_published_package/summary.json').read_bytes(), b'{"version":"old"}\n')
        self.assertFalse((out / 'publication_rollback.json').exists())

    def test_external_scope_after_owned_update_survives_rollback(self):
        root = fixture('external_scope_after_owned')
        out = root / 'reports/run'; out.mkdir(parents=True)
        with self.assertRaises(RuntimeError):
            with publication.PublicationBackup(root, out) as backup:
                put(root, 'reports/remaining_resume_20260913/scope.json', b'build-owned scope')
                backup.record_owned_scope_update()
                put(root, 'reports/remaining_resume_20260913/scope.json', b'new external user scope')
                raise RuntimeError('fixture failure after external scope change')
        self.assertEqual((root / 'reports/remaining_resume_20260913/scope.json').read_bytes(), b'new external user scope')

    def test_backup_output_cannot_escape_fixture_workspace(self):
        root = fixture('escape_guard')
        with self.assertRaises(ValueError):
            with publication.PublicationBackup(root, FIXTURES / 'outside_this_workspace'):
                self.fail('Escaped output must be rejected before copying.')

    def test_scope_change_cancels_before_next_fake_builder_and_rolls_back(self):
        root = fixture('scope_freeze')
        old = published_files(root)
        put(root, 'corpus/fixture_only/corpus.sqlite3', b'fixture marker; no database opened')
        scripts = ['scripts/build_document_index.py', 'scripts/build_focused_laws.py', 'scripts/build_focused_counties.py', 'scripts/build_county_local_package.py', 'scripts/build_focused_package.py', 'scripts/finalize_official_resume_20260913.py', 'delivery/ui-sketch/build_data.py']
        for script in scripts:
            put(root, script, '# inert fixture script; real builders are not run\n')
        calls = []
        def fake_run_path(path, run_name=None):
            calls.append(Path(path).relative_to(root).as_posix())
            put(root, 'delivery/focused_legal_corpus/summary.json', b'failed scope-change output')
            put(root, 'reports/remaining_resume_20260913/scope.json', b'{"unexpected_scope_change":true}\n')
        with mock.patch.object(publication, 'ROOT', root), mock.patch.object(publication, 'run_lock', lambda _: nullcontext()), mock.patch.object(publication.runpy, 'run_path', fake_run_path):
            with self.assertRaisesRegex(AssertionError, 'Scope changed during locked build'):
                publication.main()
        self.assertEqual(calls, ['scripts/build_document_index.py'])
        expected = dict(old)
        expected['reports/remaining_resume_20260913/scope.json'] = b'{"unexpected_scope_change":true}\n'
        self.assertEqual(published_files(root), expected)
        receipts = list((root / 'reports/county_law_focus_20260914/rebuilds').glob('*/receipt.json'))
        self.assertEqual(len(receipts), 1)
        self.assertFalse(json.loads(receipts[0].read_text())['validated'])

    def coordinated_fixture(self, name, finalizer_source):
        root = fixture(name)
        put(root, 'corpus/fixture_only/corpus.sqlite3', b'fixture marker; no database opened')
        scripts = ['scripts/build_document_index.py', 'scripts/build_focused_laws.py', 'scripts/build_focused_counties.py', 'scripts/build_county_local_package.py', 'scripts/build_focused_package.py', 'scripts/finalize_official_resume_20260913.py', 'delivery/ui-sketch/build_data.py']
        for script in scripts:
            put(root, script, '# inert fixture script; real builders are not run\n')
        put(root, 'scripts/build_county_local_package.py', 'from pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\ndef build():\n    with (ROOT/"fixture_county_build_calls.txt").open("a",encoding="utf-8") as recorded:\n        recorded.write("build called\\n")\n')
        put(root, 'scripts/finalize_official_resume_20260913.py', 'from pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\n' + finalizer_source)
        return root

    def test_failed_finalizer_does_not_persist_scope(self):
        root = self.coordinated_fixture('failed_finalizer', 'def finalize(scope,persist_scope=True):\n    scope["fixture_value"]="new build value"\n    if persist_scope:\n        (ROOT/"reports/remaining_resume_20260913/scope.json").write_text("build-owned partial scope")\n    raise RuntimeError("fixture finalizer failed")\n')
        old = published_files(root)
        def fake_run_path(path, run_name=None):
            put(root, 'delivery/focused_legal_corpus/summary.json', b'failed finalizer new output')
        with mock.patch.object(publication, 'ROOT', root), mock.patch.object(publication, 'run_lock', lambda _: nullcontext()), mock.patch.object(publication.runpy, 'run_path', fake_run_path):
            with self.assertRaisesRegex(RuntimeError, 'fixture finalizer failed'):
                publication.main()
        self.assertEqual((root / 'fixture_county_build_calls.txt').read_text(encoding='utf-8'), 'build called\n')
        self.assertEqual(published_files(root), old)

    def test_external_scope_during_finalizer_survives_and_cancels(self):
        root = self.coordinated_fixture('external_during_finalizer', 'def finalize(scope,persist_scope=True):\n    target=ROOT/"reports/remaining_resume_20260913/scope.json"\n    target.write_bytes(b"external user scope during finalizer")\n    if persist_scope:\n        target.write_bytes(b"incorrect overwritten build scope")\n')
        old = published_files(root)
        def fake_run_path(path, run_name=None):
            put(root, 'delivery/focused_legal_corpus/summary.json', b'new output that must roll back')
        with mock.patch.object(publication, 'ROOT', root), mock.patch.object(publication, 'run_lock', lambda _: nullcontext()), mock.patch.object(publication.runpy, 'run_path', fake_run_path):
            with self.assertRaisesRegex(AssertionError, 'Scope changed'):
                publication.main()
        self.assertEqual((root / 'fixture_county_build_calls.txt').read_text(encoding='utf-8'), 'build called\n')
        expected = dict(old)
        expected['reports/remaining_resume_20260913/scope.json'] = b'external user scope during finalizer'
        self.assertEqual(published_files(root), expected)


class CountyJoinTests(unittest.TestCase):
    A = 'corpus/county_local_documents_20260914'
    B = 'corpus/county_local_rules_washington_20260914'
    URL = 'https://official.example/rules.pdf'
    HASH = 'a' * 64

    def setUp(self):
        self.a = {'geoid_associations': ['01001'], 'contexts': [{'source': 'A'}]}
        self.b = {'geoid_associations': ['53001'], 'contexts': [{'source': 'B'}]}
        self.sources = {(self.A, self.URL, self.HASH): self.a, (self.B, self.URL, self.HASH): self.b}

    def row(self, collection=None, url=None, raw_hash=None, kind='collector'):
        return {'collection': collection or self.A, 'source_url': url or self.URL, 'raw_sha256': raw_hash or self.HASH, 'capture_kind': kind}

    def test_direct_capture_joins_exact_key(self):
        self.assertIs(package.county_source_row(self.row(), self.sources), self.a)

    def test_wrong_url_cannot_inherit_mapping(self):
        with self.assertRaises(RuntimeError):
            package.county_source_row(self.row(url=self.URL + '?different=1'), self.sources)

    def test_wrong_original_hash_cannot_inherit_mapping(self):
        with self.assertRaises(RuntimeError):
            package.county_source_row(self.row(raw_hash='b' * 64), self.sources)

    def test_other_known_collection_uses_its_own_mapping(self):
        self.assertIs(package.county_source_row(self.row(collection=self.B), self.sources), self.b)
        with self.assertRaises(RuntimeError):
            package.county_source_row(self.row(collection=self.B), {(self.A, self.URL, self.HASH): self.a})

    def test_unknown_and_prefix_collision_collections_have_no_county_join(self):
        for value in ['corpus/unrelated', self.A + '_different', 'prefix/' + self.A]:
            with self.subTest(collection=value):
                self.assertIsNone(package.county_source_row(self.row(collection=value), self.sources))

    def test_ocr_child_joins_only_its_own_exact_parent(self):
        self.assertIs(package.county_source_row(self.row(collection=self.A + '/ocr', kind='ocr_derivative'), self.sources), self.a)
        self.assertIs(package.county_source_row(self.row(collection=self.B + '/ocr', kind='ocr_derivative'), self.sources), self.b)
        with self.assertRaises(RuntimeError):
            package.county_source_row(self.row(collection=self.B + '/ocr', kind='ocr_derivative'), {(self.A, self.URL, self.HASH): self.a})
        with self.assertRaises(RuntimeError):
            package.county_source_row(self.row(collection=self.A + '/ocr', raw_hash='c' * 64, kind='ocr_derivative'), self.sources)
        with self.assertRaises(RuntimeError):
            package.county_source_row(self.row(collection=self.A + '/ocr', url='https://other.example/rules.pdf', kind='ocr_derivative'), self.sources)


if __name__ == '__main__':
    FIXTURES.mkdir(parents=True, exist_ok=False)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (FIXTURES / 'test_output.txt').write_text(stream.getvalue(), encoding='utf-8')
    receipt = {'verified_at_utc': datetime.now(timezone.utc).isoformat(), 'valid': result.wasSuccessful(), 'tests_run': result.testsRun, 'failures': [{'test': str(t), 'traceback': message} for t, message in result.failures], 'errors': [{'test': str(t), 'traceback': message} for t, message in result.errors], 'fixture_directory': str(FIXTURES.relative_to(ROOT)), 'full_builders_run': False, 'network_requests': 0, 'production_sources_modified_by_tests': False, 'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [PUBLICATION_SOURCE, JOIN_SOURCE]}}
    (TEST_ROOT / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(stream.getvalue())
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('failures', 'errors')}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)

"""Offline tests of exact-checkpoint reuse; no source acquisition/publication."""
from contextlib import nullcontext
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'reports/county_law_focus_20260914'
sys.path.insert(0, str(BASE))
import rebuild_checkpoint_cache as cache_module
import rebuild_focused_package as coordinator


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else value.encode())
    return path


class CacheTests(unittest.TestCase):
    def setUp(self):
        fixtures = BASE / 'tests/fixtures'
        fixtures.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='checkpoint_cache_', dir=fixtures)
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.source = put(self.root, 'sources/legal/a.txt', b'original law')
        self.output = put(self.root, 'delivery/package/summary.json', b'{"valid":true}')
        self.code = put(self.root, 'scripts/build.py', b'# reviewed builder')
        self.cache = cache_module.CheckpointCache(self.root, input_trees=('sources', 'scripts'),
            output_trees=('delivery/package',), input_files=('REQUEST.md',), output_files=())
        self.receipt = put(self.root, 'reports/full-build/receipt.json', json.dumps({
            'validated': True, 'steps': [{'exit_code': 0, 'script': str(n)} for n in range(7)]}))

    def baseline(self):
        return self.cache.remember(self.receipt, self.cache.inventory(inputs_only=True))

    def test_missing_baseline_never_blesses_existing_package(self):
        self.assertEqual(self.cache.check()['reason'], 'no_validated_baseline')

    def test_unchanged_checkpoint_freshly_hashes_every_file(self):
        self.baseline()
        with mock.patch.object(cache_module, 'hash_file', wraps=cache_module.hash_file) as hashes:
            result = self.cache.check()
        self.assertTrue(result['hit'])
        actual = {Path(call.args[0]).resolve() for call in hashes.call_args_list}
        self.assertTrue({self.source.resolve(), self.output.resolve(), self.code.resolve()}.issubset(actual))

    def test_same_metadata_changed_source_bytes_cannot_hit(self):
        self.baseline()
        original_stat = cache_module._stat(self.source)
        self.source.write_bytes(b'altered  law')
        real_stat_value = cache_module._stat_value
        def masked(value):
            return original_stat if value.st_size == original_stat[0] else real_stat_value(value)
        with mock.patch.object(cache_module, '_stat_value', masked):
            result = self.cache.check()
        self.assertFalse(result['hit'])
        self.assertEqual(result['reason'], 'registered_input_or_output_bytes_changed')

    def test_added_file_invalidates(self):
        self.baseline()
        put(self.root, 'sources/legal/new.pdf', b'new document')
        self.assertFalse(self.cache.check()['hit'])

    def test_deleted_file_invalidates(self):
        self.baseline()
        self.source.unlink()
        self.assertFalse(self.cache.check()['hit'])

    def test_missing_optional_input_appearing_invalidates(self):
        self.baseline()
        put(self.root, 'REQUEST.md', b'new source scope')
        self.assertFalse(self.cache.check()['hit'])

    def test_output_tamper_invalidates(self):
        self.baseline()
        self.output.write_bytes(b'corrupt')
        self.assertFalse(self.cache.check()['hit'])

    def test_sqlite_wal_included_but_shared_memory_ignored(self):
        put(self.root, 'sources/db/corpus.sqlite3-wal', b'committed SQLite content')
        put(self.root, 'sources/db/corpus.sqlite3-shm', b'coordination')
        self.baseline()
        put(self.root, 'sources/db/corpus.sqlite3-shm', b'changed coordination')
        self.assertTrue(self.cache.check()['hit'])
        put(self.root, 'sources/db/corpus.sqlite3-wal', b'new committed content')
        self.assertFalse(self.cache.check()['hit'])

    def test_failed_receipt_cannot_establish_baseline(self):
        self.receipt.write_text('{"validated":false,"steps":[]}', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.baseline()
        self.assertFalse(self.cache.baseline.exists())

    def test_receipt_rewrite_invalidates(self):
        self.baseline()
        self.receipt.write_text('{"validated":true,"steps":[]}', encoding='utf-8')
        self.assertEqual(self.cache.check()['reason'], 'validation_receipt_changed')

    def test_changed_source_during_build_cannot_establish_baseline(self):
        before = self.cache.inventory(inputs_only=True)
        self.source.write_bytes(b'new capture arrived during build')
        with self.assertRaises(RuntimeError):
            self.cache.remember(self.receipt, before)
        self.assertFalse(self.cache.baseline.exists())

    def test_mutation_during_hash_rejected(self):
        inventory = self.cache.inventory()
        original = cache_module.hash_file
        def change(path, expected=None):
            result = original(path, expected)
            if Path(path) == self.source:
                put(self.root, 'sources/legal/during.pdf', b'new source')
            return result
        with mock.patch.object(cache_module, 'hash_file', change):
            with self.assertRaisesRegex(RuntimeError, 'namespace changed'):
                self.cache.fingerprint(inventory)

    def test_imported_helper_outside_broad_roots_is_bound(self):
        helper = put(self.root, 'other_helpers/reconcile.py', b'# original imported helper')
        module = types.ModuleType('fixture_extra_helper')
        module.__file__ = str(helper)
        with mock.patch.dict(sys.modules, {'fixture_extra_helper': module}):
            self.baseline()
        helper.write_bytes(b'# changed imported helper')
        self.assertEqual(self.cache.check()['reason'], 'imported_helper_changed')

    def test_registry_change_cannot_reuse_baseline(self):
        self.baseline()
        self.cache.registry['new_scope'] = True
        self.assertEqual(self.cache.check()['reason'], 'input_registry_changed')

    def test_corrupt_baseline_is_safe_miss(self):
        self.cache.baseline.parent.mkdir(parents=True)
        self.cache.baseline.write_text('broken json', encoding='utf-8')
        self.assertFalse(self.cache.check()['hit'])

    def test_coordinator_hit_never_calls_builder_or_backups(self):
        put(self.root, 'README.md', '| Location |\n')
        put(self.root, 'reports/remaining_resume_20260913/scope.json', json.dumps({
            'latest_user_direction': 'Continue official sources only', 'reviewed_collections': ['corpus/test']}))
        put(self.root, 'corpus/test/corpus.sqlite3', 'fixture marker')
        put(self.root, 'delivery/focused_legal_corpus/summary.json', '{}')
        put(self.root, 'delivery/focused_legal_corpus/package_files.json', '{}')
        fake_cache = mock.Mock()
        fake_cache.check.return_value = {'hit': True, 'reason': 'fixture verified exact bytes'}
        with mock.patch.object(coordinator, 'ROOT', self.root), \
             mock.patch.object(coordinator, 'run_lock', lambda _: nullcontext()), \
             mock.patch.object(coordinator, 'CheckpointCache', return_value=fake_cache), \
             mock.patch.object(coordinator, 'PublicationBackup') as backup, \
             mock.patch.object(coordinator.runpy, 'run_path') as runner, \
             mock.patch('sys.stdout', new_callable=io.StringIO):
            coordinator.main([])
        backup.assert_not_called()
        runner.assert_not_called()
        fake_cache.remember.assert_not_called()
        receipt = next((self.root / 'reports/county_law_focus_20260914/rebuilds').glob('*/receipt.json'))
        result = json.loads(receipt.read_text())
        self.assertEqual(result['publication_action'], 'unchanged_validated_snapshot_reused')
        self.assertEqual(result['steps'], [])


if __name__ == '__main__':
    unittest.main()

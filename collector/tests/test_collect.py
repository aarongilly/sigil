import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('collect', Path(__file__).parents[1] / 'collect.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CollectionTests(unittest.TestCase):
    def test_snapshot_failure_and_source_integrity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / 'vault'
            vault.mkdir()
            note = vault / 'note.md'
            note.write_text('---\n_id: abc\n_created: 2026-01-01\n---\nHello')
            before = (note.read_bytes(), note.stat().st_mtime_ns)
            config = root / 'config.json'
            config.write_text(json.dumps({'output': 'output', 'sources': [{'name': 'notes', 'adapter': 'obsidian', 'path': 'vault', 'include_body': True}]}))
            manifest = module.collect(config)
            published = (root / 'output/manifest.json').read_bytes()
            entity = json.loads((root / 'output' / manifest['entities']).read_text())
            self.assertEqual(entity['_body'], 'Hello')
            self.assertEqual(entity['_created'], '2026-01-01')
            self.assertEqual(before, (note.read_bytes(), note.stat().st_mtime_ns))
            self.assertEqual(manifest['generation'], module.collect(config)['generation'])
            published = (root / 'output/manifest.json').read_bytes()
            (vault / 'duplicate.md').write_text(note.read_text())
            with self.assertRaisesRegex(ValueError, 'Duplicate _id'):
                module.collect(config)
            self.assertEqual(published, (root / 'output/manifest.json').read_bytes())

    def test_csv_and_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'journal.csv'
            path.write_text('id,title\n001,Hello\n,Skip\n')
            source = {'id_column': 'id', 'id_prefix': 'journal-', 'fields': {'_name': 'title'}}
            records = list(module.csv_source(source, path))
            self.assertEqual(len(records), 1)
            self.assertEqual(module.validate(records[0][0])['_id'], 'journal-001')
            with self.assertRaisesRegex(ValueError, 'missing columns'):
                list(module.csv_source({**source, 'id_column': 'missing'}, path))
        for entity in [{'_id': 'a.b'}, {'_id': 'a', 'nested': {}}, {'_id': 'a', 'array': [{}]}]:
            with self.assertRaises(ValueError):
                module.validate(entity)

    def test_output_cannot_overlap_vault(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / 'config.json'
            config.write_text(json.dumps({'output': 'vault/output', 'sources': [{'name': 'notes', 'adapter': 'obsidian', 'path': 'vault'}]}))
            with self.assertRaisesRegex(ValueError, 'overlap'):
                module.collect(config)


if __name__ == '__main__':
    unittest.main()

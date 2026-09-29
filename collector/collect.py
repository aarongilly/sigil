"""Read-only source adapters and atomic SIGIL snapshot publication."""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import tempfile


def validate(entity):
    identity = entity.get('_id')
    if not isinstance(identity, str) or not identity.strip() or any(c in identity for c in '@.'):
        raise ValueError(f'Invalid SIGIL _id: {identity!r}')
    scalar = lambda v: v is None or type(v) in (str, int, float, bool)
    for key, value in entity.items():
        if not isinstance(key, str) or not (scalar(value) or isinstance(value, list) and all(scalar(v) for v in value)):
            raise ValueError(f'{identity}: {key!r} must contain scalars or an array of scalars')
    json.dumps(entity, allow_nan=False)
    return entity


def obsidian(source, path):
    import yaml
    # SafeLoader without implicit coercion preserves timestamps and textual values.
    class Loader(yaml.SafeLoader):
        yaml_implicit_resolvers = {}
    if not path.is_dir():
        raise ValueError(f'Vault does not exist: {path}')
    for note in sorted(path.rglob('*.md')):
        if note.is_symlink():
            continue
        text = note.read_text(encoding='utf-8-sig')
        lines = text.splitlines(keepends=True)
        if not lines or lines[0].strip() != '---':
            continue
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
        if end is None:
            raise ValueError(f'Unclosed frontmatter: {note}')
        entity = yaml.load(''.join(lines[1:end]), Loader=Loader)
        if entity is None:
            continue
        if not isinstance(entity, dict):
            raise ValueError(f'Frontmatter must be a mapping: {note}')
        if '_id' not in entity:
            continue
        entity.setdefault('_name', note.stem)
        entity.setdefault('_type', 'note')
        entity.setdefault('_path', note.relative_to(path).as_posix())
        if source.get('include_body', False):
            entity['_body'] = ''.join(lines[end + 1:]).strip()
        yield entity, note.relative_to(path).as_posix()


def csv_source(source, path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        required = {source['id_column'], *source.get('fields', {}).values()}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f'{path}: missing columns {sorted(required - set(reader.fieldnames or []))}')
        if '_id' in source.get('fields', {}):
            raise ValueError('Map identity with id_column, not fields._id')
        for row_number, row in enumerate(reader, 2):
            identity = row[source['id_column']]
            if not identity or not identity.strip():
                continue
            entity = {field: row[column] for field, column in source.get('fields', {}).items()}
            entity['_id'] = source.get('id_prefix', '') + identity
            entity.setdefault('_type', source.get('type', 'journal'))
            yield entity, f'{path.name}:{row_number}'


ADAPTERS = {'obsidian': obsidian, 'csv': csv_source}


def collect(config_path):
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text())
    root = config_path.parent
    output = (root / config['output']).resolve()
    entities, provenance, counts = {}, {}, {}
    for source in config['sources']:
        name = source['name']
        if name in counts:
            raise ValueError(f'Duplicate source name: {name}')
        path = (root / source['path']).resolve()
        if path == output or path in output.parents or output in path.parents:
            raise ValueError('Output and source paths must not overlap')
        counts[name] = 0
        for entity, location in ADAPTERS[source['adapter']](source, path):
            validate(entity)
            identity = entity['_id']
            if identity in entities:
                raise ValueError(f'Duplicate _id: {identity}')
            entities[identity] = entity
            provenance[identity] = {'source': name, 'location': location}
            counts[name] += 1
    payload = ''.join(json.dumps(entities[key], ensure_ascii=False, sort_keys=True, allow_nan=False) + '\n' for key in sorted(entities)).encode()
    generation = hashlib.sha256(payload).hexdigest()
    manifest = {'version': 1, 'generation': generation, 'collected_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                'entities': f'snapshots/{generation}/entities.jsonl', 'counts': counts, 'provenance': provenance}
    snapshot = output / 'snapshots' / generation
    snapshot.mkdir(parents=True, exist_ok=True)
    atomic_write(snapshot / 'entities.jsonl', payload)
    # The manifest is the commit point: readers always resolve a complete immutable snapshot.
    atomic_write(output / 'manifest.json', json.dumps(manifest, indent=2).encode())
    return manifest


def atomic_write(path, payload):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    result = collect(args.config)
    print(json.dumps({'generation': result['generation'], 'counts': result['counts']}))

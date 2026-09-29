# Sigil collection hub

Read-only source spokes publish flat SIGIL entities into a central snapshot. Source systems remain authoritative. The timeline is a separate consumer; the hub does not require Obsidian as its database.

From the repository root:

```sh
python3 -m venv .venv
.venv/bin/pip install -r collector/requirements.txt
cp collector/config.example.json collector/config.json
.venv/bin/python collector/collect.py --config collector/config.json
python3 -m http.server 8765 --bind 127.0.0.1
```

Open http://localhost:8765/stream-app/. The example configuration collects two sample entities. Edit `collector/config.json` for real sources; all relative paths resolve against the configuration's directory. Keep output outside source directories. `data/` and your local configuration are ignored by Git.

## Source profiles

- `obsidian`: recursively reads Markdown frontmatter. Includes only notes with `_id`; defaults `_name` to filename and `_type` to `note`. Preserves existing `_path`, otherwise supplies a vault-relative path. `include_body` copies prose into `_body`. Implicit YAML scalars remain strings, including dates, numbers, and booleans. Nested objects are rejected. Wikilinks remain native strings: reference resolution is not implemented. Files without IDs are skipped; the collector never assigns IDs to source files.
- `csv`: reads an exported table. `id_column` supplies identity, optional `id_prefix` namespaces it, `fields` maps SIGIL field names to CSV headers, and `type` defaults to `journal`. Empty IDs are skipped; all CSV values stay strings. Keep the prefix stable. This is an export adapter, not yet a direct Data Journal integration.

Add future spokes as generators in `ADAPTERS`, yielding `(entity, source_location)` pairs. Read access is a convention of this implementation, not an OS-level sandbox; use filesystem read-only permissions for stronger enforcement.

## Publication contract

`data/manifest.json` contains collection time, source counts, provenance, and a relative `entities` path. That path points to `snapshots/<sha256>/entities.jsonl`. Validate the entire collection before publishing. Write the snapshot first, then atomically replace the manifest. Consumers fetch the manifest once and follow its path. Failure leaves the previous manifest intact. Duplicate IDs are errors, including across sources; there is no implicit merge priority.

Snapshots are retained, so deleted source entities disappear from the current feed but remain in older files. Retention and cleanup are not automated yet. This is a current-state feed, not an edit history. Collection time never overwrites `_updated`. Avoid overlapping scheduled runs: the last successful publisher wins.

## Nightly on macOS

An editable launchd template is provided in `com.sigil.collect.plist.example`. Replace every `REPO_PATH` with the absolute repository path. After a successful collection against your real sources, copy it to `~/Library/LaunchAgents/com.sigil.collect.plist` and load it:

```sh
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.sigil.collect.plist
```

The template runs at 02:00 local time and writes logs to `/tmp`. The job needs access to locally downloaded source files; sleep, shutdown, and cloud availability can delay or prevent collection. No schedule is installed by the starter. Inspect the logs and manifest collection time after the first nights. To unload:

```sh
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.sigil.collect.plist
```

## Checks

```sh
.venv/bin/python -m unittest discover -s collector/tests -v
```

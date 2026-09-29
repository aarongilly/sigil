# Sigil timeline

A standalone PWA consuming snapshots from the [collection hub](../collector/README.md). No build step or JavaScript dependencies.

Run the collector using its quickstart, then serve the repository root:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Visit http://localhost:8765/stream-app/. The app follows `../data/manifest.json` to its immutable JSONL snapshot. **Open JSONL** also accepts a manually selected snapshot. Search matches all fields; filter cards by `_type`.

Cards sort newest first by `_updated`, falling back to `_created`. Undated entities appear last. This shows current entities, not every historical change. Use timezone-qualified timestamps for predictable ordering across devices.

## Card templates

`index.html` contains the shared HTML card template. The `templates` registry in `app.js` chooses a content renderer by `_type`; `note` and `journal` are included. Add a renderer and styles for new types. Values are inserted with `textContent`; Markdown bodies appear as plain text.

## Offline and privacy

The service worker caches only the app interface. Source data stays in memory and must be reopened from JSONL after an offline reload. This avoids silently persisting private journal data in browser storage. The app makes no requests to third-party services. PWA installation requires localhost or HTTPS and depends on browser support; the initial icon is SVG.

Serve locally: the development server has no authentication and exposes files beneath its root. A remote deployment needs an authenticated data endpoint and appropriate hosting boundaries.

## Next steps

- Map real journal data and settle the Obsidian representation profile.
- Add per-type HTML layouts as concrete SIGIL types emerge.
- Add an optional DuckDB analysis view once actual queries are known; JSONL remains the interchange format.
- Decide whether persistent offline data and a historical events feed are desirable.

# methodology_v2 — documentation viewer

A self-contained, offline documentation site for the `methodology_v2` package. The
prose lives as markdown under `src/`, organized by altitude (system → subsystem →
component), and a small vanilla-JS viewer renders it as a two-pane browser.

## View it

- **Offline:** open `index.html` directly in a browser (`file://`) — no server needed.
- **Served:** `python3 -m http.server 8802` from this directory, then open
  `http://127.0.0.1:8802/`.

## Edit it

The content is the markdown under `src/`. After editing any page, regenerate the
embedded bundle the viewer reads:

```bash
python3 build.py      # scans src/**.md -> docs-data.js
```

`docs-data.js` is generated (committed so the viewer works on a fresh clone without a
build step). `vendor/` holds the offline copies of `marked` and `highlight.js`.

## Layout

```
index.html      viewer shell (two-pane: grouped nav + markdown reader)
app.css         theme + layout (dark by default; ◐ toggles light)
app.js          nav, in-panel link routing, filter, hash routing, theme
build.py        src/**.md  ->  docs-data.js
docs-data.js    generated content bundle (window.MANIFEST + window.DOCS)
vendor/         marked + highlight.js (offline)
src/
  README.md         documentation index / reading order
  _coherence.md     coverage + design-vs-implementation audit
  architecture/     high-level subsystem docs
  modules/          one low-level walkthrough per source file
  reference/        exact schema / config / lifecycle tables
  design/           design & rationale records
```

The site's own index page (start here) is `src/README.md`.

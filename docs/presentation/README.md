# Pitch deck

16-slide deck for the hackathon submission — the problem, the reframed capability pitch, architecture, corpus stats, the full API list (agent-facing endpoints kept separate from administration/operational ones), three story vignettes, engineering highlights, trust/verification, and a close. Content mirrors [DEMO_SCRIPT.md](../DEMO_SCRIPT.md)'s narrative and reuses the same verified facts as [DEMO_WORKFLOWS.md](../DEMO_WORKFLOWS.md).

## Files

- **`Municipal-Law-Skill.pptx`** — the deck, native PowerPoint, fully editable.
- **`Municipal-Law-Skill.pdf`** — the same deck as a PDF (rendered from `deck.html`, not from the pptx — see below).
- **`deck.html`** — a standalone, browser-viewable version of the same deck (open it directly, one slide per screen-height section).
- **`content.py`** — the single source of truth: one Python list of slide specs. Every generator renders from this, so the `.pptx`, the `.pdf`/`.html`, and the markdown review copy can't drift out of sync with each other.
- **`DECK_CONTENT.md`** — the same content as plain, easy-to-review markdown, one section per slide, grouped (Hook & positioning / API reference / Stories / Engineering & trust / Close). **Edit this file to review or propose changes** — it's far easier to mark up than a `.pptx` — then port accepted edits back into `content.py` (the real source of truth) and regenerate everything else.
- **`build_pptx.py`** / **`build_html.py`** / **`build_markdown.py`** — regenerate the `.pptx` / `deck.html` / `DECK_CONTENT.md` from `content.py`.
- **`render_pdf.js`** — renders `deck.html` to `Municipal-Law-Skill.pdf` via headless Chrome (one 1280×720 slide per PDF page).

## Reviewing and editing content

1. Read/mark up **`DECK_CONTENT.md`** — it's plain markdown, easiest to comment on or edit directly.
2. Port whatever you change back into the matching slide entry in **`content.py`** (same order, same `"kind"` per slide - see the field names used in `build_markdown.py`'s `render_slide_body()` for exactly which keys each slide `kind` reads).
3. Regenerate everything:

```bash
python build_markdown.py # -> DECK_CONTENT.md (re-run after editing content.py, to keep the review copy in sync)
python build_pptx.py     # -> Municipal-Law-Skill.pptx
python build_html.py     # -> deck.html
node render_pdf.js "<path to a Chrome/Chromium executable>"   # -> Municipal-Law-Skill.pdf
```

`render_pdf.js` needs `puppeteer-core` (or `puppeteer`) installed and a real Chrome/Chromium binary path — it falls back to an existing global install (e.g. one already pulled in by `@mermaid-js/mermaid-cli`, if you have that from working on this repo's other Mermaid diagrams) if `puppeteer-core` isn't resolvable locally.

## Why the PDF isn't exported from the .pptx directly

No LibreOffice/PowerPoint CLI was available in the environment this was built in to convert `.pptx` → `.pdf` with guaranteed visual fidelity. Rendering a parallel HTML version and printing that to PDF via headless Chrome sidesteps that dependency entirely and was independently verified (screenshots taken of several slides during development) to render correctly before being trusted as the deliverable.

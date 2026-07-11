# Pitch deck

14-slide deck for the hackathon submission, ordered around the capability, not the REST surface: problem (with a visual myth-vs-real-statute panel) → the capability, including a Traditional-RAG-vs-this-skill flow comparison → three story vignettes (each a single ask→retrieve→cite flow diagram ending in a highlighted citation, with the composed answer below it) → architecture → corpus scale (with a "not a curated demo dataset" callout) → engineering issues found-and-fixed on live municipal data → a "why not just ask an LLM?" comparison (framed as LLM-memory limitations, not accusations) → agent-facing capabilities condensed to one table (with administration/operational endpoints kept separate, in small type, not a slide of their own) → trust/verification (leading with "every response is cryptographically signed (Ed25519)") → why NANDA → a checkmark-style close. Content mirrors [DEMO_SCRIPT.md](../DEMO_SCRIPT.md)'s narrative and reuses the same verified facts as [DEMO_WORKFLOWS.md](../DEMO_WORKFLOWS.md). Reordered and rebalanced across two rounds of reviewer feedback — the original 16-slide cut spent too much time on API detail (4 slides) relative to the stories that actually sell the project; round two tightened wording precision and replaced numbered-step story slides with flow diagrams.

## Files

- **`Municipal-Law-Skill.pptx`** — the deck, native PowerPoint, fully editable.
- **`Municipal-Law-Skill.pdf`** — the same deck as a PDF (rendered from `deck.html`, not from the pptx — see below).
- **`deck.html`** — a standalone, browser-viewable version of the same deck (open it directly, one slide per screen-height section).
- **`content.py`** — the single source of truth: one Python list of slide specs. Every generator renders from this, so the `.pptx`, the `.pdf`/`.html`, and the markdown review copy can't drift out of sync with each other.
- **`DECK_CONTENT.md`** — the same content as plain, easy-to-review markdown, one section per slide, grouped (Hook & positioning / Stories / Architecture & scale / Engineering & why not an LLM / API reference & trust / Close). **Edit this file to review or propose changes** — it's far easier to mark up than a `.pptx` — then port accepted edits back into `content.py` (the real source of truth) and regenerate everything else.
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

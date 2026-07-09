# Data Source

Two independent, real, first-party sources are ingested — one HTML, one PDF — demonstrating the pipeline's multi-format extensibility.

## Source 1: NYC Administrative Code (HTML)

[nycadmincode.readthedocs.io](https://nycadmincode.readthedocs.io/) — a **CC0 (public domain)**, weekly-updated mirror of the NYC Administrative Code, maintained in connection with MyGov.nyc. Pages are organized by Title → Chapter → Subchapter (e.g. `t24/c02/sch04/` = Title 24, Chapter 2, Subchapter 4), with each individual section addressable by an anchor (`#section-24-222`).

The official canonical source is the NYC Law Department's contracted site at [codelibrary.amlegal.com](https://codelibrary.amlegal.com/codes/newyorkcity/) (American Legal Publishing). That site's scraping terms aren't clearly established for automated reuse, whereas the readthedocs mirror explicitly commits to CC0/public-domain licensing and weekly refreshes from the same underlying source — that's why ingestion targets it instead.

**Coverage: Title 24, Chapter 2 (Noise Control)** — all 8 subchapters, ~110 chunks:

| Subchapter | Topic |
|---|---|
| 1 | Short Title, Policy and Definitions |
| 2 | General Provisions |
| 3 | Prohibited Noise — General Prohibition |
| 4 | Construction Noise Management (includes § 24-222) |
| 5 | Prohibited Noise — Specific Sources — Sound Level Standard |
| 6 | Specific Noise Sources — Plainly Audible and Other Standards |
| 7 | Certificates and Tunneling Permits |
| 8 | Enforcement |

Agency of record: **Department of Environmental Protection (DEP)** — confirmed directly from the ingested text itself (Subchapter 1's definitions section states "Commissioner means commissioner of environmental protection"), not assumed from outside knowledge.

## Source 2: NYC Health Code (PDF)

`https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article{N}.pdf` — first-party PDFs hosted directly by the NYC Department of Health and Mental Hygiene (confirmed via the department's own index at `nyc.gov/site/doh/about/about-doh/health-code-and-rules.page`, which lists ~38 articles at this URL pattern). Text is extracted with `pypdf`; each article PDF contains a table-of-contents block followed by full section bodies in `§X.XX  Title. Body...` format (see `app/ingestion/health_code_parser.py`), so the same TOC-vs-body disambiguation and citation approach used for the admin code applies here too — just with `#page=N` anchors instead of HTML fragment anchors, since PDF readers don't have per-section HTML ids.

**Coverage: Article 161 (Animals)** — 16 sections, ingested via `scripts/seed_health_code.py`:

- §161.01 Wild and other animals prohibited
- §161.02–§161.07 Definitions, dog control/licensing/vaccination/dangerous dogs
- §161.09 Permits to keep certain animals
- §161.11–§161.17 Nuisance prevention, self-inspection, small-animal sale/boarding rules
- **§161.19 Keeping of livestock, live poultry and rabbits** — the section a "can I keep chickens" question resolves to
- §161.21–§161.25 Stables, shelter sterilization, departmental rulemaking

Agency of record: **Department of Health and Mental Hygiene (DOHMH)**.

### A concrete no-hallucination example: §161.19 and the "6 hens" myth

It's widely repeated online that NYC caps backyard chickens at "a maximum of 6 hens." **The real text of §161.19 states no such number.** It says only:

> (a) No person shall keep a live rooster, duck, goose or turkey in the City of New York except (1) in a slaughterhouse authorized by federal or state law... or (2) as authorized by §161.01(a) of this Article. (b) A person who is authorized by applicable law to keep for sale or sell livestock, live rabbits or poultry shall keep the premises... clean and free of animal nuisances. (c) Live rabbit and poultry markets... shall be located at least 25 feet away from any building.

Hens specifically are never mentioned as restricted. This was independently verified by downloading and parsing the actual PDF (not trusting secondhand summaries), and `tests/test_health_code_parser.py`/`tests/test_sections.py` assert the ingested text contains neither "6 hens" nor "maximum" — a regression guard against ever fabricating this figure into the service's own data or documentation.

## Extending coverage

**Admin Code**: find the page(s) you want at `https://nycadmincode.readthedocs.io/t{title}/c{chapter}/` (browse the site's table of contents for title/chapter/subchapter numbers), then call `POST /api/v1/ingest` with those URLs (max `INGEST_MAX_URLS` per call, gated by `INGEST_RATE_LIMIT_PER_MINUTE` — see [API.md](./API.md#post-apiv1ingest)), or add them to `scripts/seed_admin_code.py` and re-run it.

**Health Code**: any `health-code-article{N}.pdf` follows the same URL pattern and will parse with the existing `health_code_parser.py` (it derives `article_num`/`article_name` from the PDF's own header text, not a hardcoded "161") — add the URL to `scripts/seed_health_code.py` and re-run it, or `POST /api/v1/ingest` directly (the pipeline dispatches to the PDF loader automatically based on the `.pdf` suffix).

Re-ingesting an already-seen URL is idempotent — it upserts the document record and replaces its chunks, so it's safe to re-run after either source updates.

## Known limitation: keyword search, not semantic search

Search ranks results by term frequency (see [ARCHITECTURE.md](./ARCHITECTURE.md#search-in-app-scoring-not-mongodb-text)), not by meaning. A query using different words than a section's actual text may miss it or rank a more talkative-but-less-relevant section higher. For example, § 24-222 ("After hours and weekend limits on construction work") never uses the word "noise" in its body text, so a bare `"noise"` query ranks § 24-220 ("Noise mitigation plan") above it. Query with the literal terms you expect the target section to contain.

## Known limitation: `mentions_penalty`/`mentions_permit` are keyword heuristics

Both flags are computed by substring-matching a fixed keyword list against a chunk's text (see `app/ingestion/enrich.py`), not by legal analysis. `mentions_permit` in particular is intentionally broad (it includes "authorized"/"authorization"), so it will flag sections that merely reference an exception or exemption, not only sections that establish an affirmative permit application process. Treat both as a useful filter, not a legal determination — the actual `text` should always be read before asserting a penalty or permit requirement does or doesn't apply.

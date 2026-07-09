# Data Source

Two independent, real, first-party sources are ingested — one HTML, one PDF — demonstrating the pipeline's multi-format extensibility. Coverage is now the **entire** NYC Administrative Code (all titles) and the **entire** NYC Health Code (all articles), not a curated slice.

**For the exact current coverage** (every title/chapter/subchapter/article actually ingested, with section counts and source links), see [COVERAGE.md](./COVERAGE.md) — generated directly from the live MongoDB contents by `scripts/generate_coverage_report.py`, so it can't drift out of sync with reality. Re-run that script after any re-ingestion to refresh it.

## Source 1: NYC Administrative Code (HTML)

[nycadmincode.readthedocs.io](https://nycadmincode.readthedocs.io/) — a **CC0 (public domain)**, weekly-updated mirror of the NYC Administrative Code, maintained in connection with MyGov.nyc. Pages are organized by Title → Chapter → (optionally) Subchapter (e.g. `t24/c02/sch04/` = Title 24, Chapter 2, Subchapter 4; some chapters have no subchapters and are themselves the leaf page, e.g. `t24/c04/`), with each individual section addressable by an anchor (`#section-24-222`).

The official canonical source is the NYC Law Department's contracted site at [codelibrary.amlegal.com](https://codelibrary.amlegal.com/codes/newyorkcity/) (American Legal Publishing). That site's scraping terms aren't clearly established for automated reuse, whereas the readthedocs mirror explicitly commits to CC0/public-domain licensing and weekly refreshes from the same underlying source — that's why ingestion targets it instead.

**Ingested via `scripts/crawl_and_seed_admin_code.py`**, which crawls the site's own per-page table of contents generically rather than assuming a fixed Title → Chapter → Subchapter depth: a page's local TOC links (`div.toctree-wrapper a.reference.internal` — verified to exclude the global sidebar, which lists every title on every page) are followed recursively; a page with no such links is a leaf and is parsed/persisted immediately using the HTML already fetched during the crawl (no redundant second fetch). This generic approach was necessary because chapter depth genuinely varies: some chapters have no subchapters (leaf = chapter page), most have subchapters (leaf = subchapter page), and at least one observed chapter has a further "article" level beneath its subchapter (`t27/c01/sch12/art06/`) — a fixed two-level crawl would have missed that content silently.

Agency of record for Title 24 Chapter 2 (Noise Control) specifically: **Department of Environmental Protection (DEP)** — confirmed directly from the ingested text itself (Subchapter 1's definitions section states "Commissioner means commissioner of environmental protection"), not assumed from outside knowledge. Other titles/chapters carry whatever agency their own definitions establish, or a generic default where not otherwise determinable — see `app/ingestion/parser.py`.

## Source 2: NYC Health Code (PDF)

`https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article{N}.pdf` — first-party PDFs hosted directly by the NYC Department of Health and Mental Hygiene. The full article list is discovered from the department's own index page (`nyc.gov/site/doh/about/about-doh/health-code-and-rules.page`) by `scripts/seed_all_health_code.py`, rather than hardcoded, so it stays accurate if articles are added or renumbered.

Text is extracted with `pypdf`. Formatting is **not uniform** across all ~36 articles — discovered only by actually ingesting every one of them, not by reading one article and assuming the rest match:

- Article 161 spaces headings as `"§161.19  Title."` (two spaces) and has a table-of-contents block listing every section before the real body (each section appears twice; distinguished by checking whether the text between consecutive heading matches is empty (TOC) or substantial (real body)).
- Article 1 uses `"§1.01 Title."` (one space) and has **no** table-of-contents block at all — each heading appears exactly once, which the same empty-vs-substantial-span check handles correctly without special-casing.
- Article 48's name contains commas ("DAY CAMPS, OVERNIGHT CAMPS, AND TRAVELING DAY CAMPS"), which broke an earlier, stricter article-name pattern.
- Most articles say `"ARTICLE 121"`; Article 121 itself is typeset `"Article 121"` (title case).

All four variations are pinned by fixtures and tests (`tests/fixtures/health_code_article1.txt`, `tests/test_health_code_parser.py`) — the parser's regexes were genuinely loosened to handle the variation (variable spacing, unrestricted title-line characters, case-insensitive keyword), not patched per-article.

Agency of record: **Department of Health and Mental Hygiene (DOHMH)**.

### A concrete no-hallucination example: §161.19 and the "6 hens" myth

It's widely repeated online that NYC caps backyard chickens at "a maximum of 6 hens." **The real text of §161.19 states no such number.** It says only:

> (a) No person shall keep a live rooster, duck, goose or turkey in the City of New York except (1) in a slaughterhouse authorized by federal or state law... or (2) as authorized by §161.01(a) of this Article. (b) A person who is authorized by applicable law to keep for sale or sell livestock, live rabbits or poultry shall keep the premises... clean and free of animal nuisances. (c) Live rabbit and poultry markets... shall be located at least 25 feet away from any building.

Hens specifically are never mentioned as restricted. This was independently verified by downloading and parsing the actual PDF (not trusting secondhand summaries), and `tests/test_health_code_parser.py`/`tests/test_sections.py` assert the ingested text contains neither "6 hens" nor "maximum" — a regression guard against ever fabricating this figure into the service's own data or documentation.

## Extending / re-running ingestion

**Admin Code**: `python -m scripts.crawl_and_seed_admin_code` re-crawls and re-ingests the entire site (idempotent — safe to re-run after the source updates). Use `--start-url` to scope a re-crawl to one title/chapter/subchapter subtree, or `--limit N` to stop after N leaf pages (useful for testing changes without a full re-crawl). `POST /api/v1/ingest` also works for ad hoc single-page additions (max `INGEST_MAX_URLS` per call, gated by `INGEST_RATE_LIMIT_PER_MINUTE` — see [API.md](./API.md#post-apiv1ingest)).

**Health Code**: `python -m scripts.seed_all_health_code` re-discovers the article list and re-ingests every article (also idempotent). Use `--limit N` to test against only the first N discovered articles.

**After any re-ingestion**, run `python -m scripts.generate_coverage_report` to refresh [COVERAGE.md](./COVERAGE.md).

Re-ingesting an already-seen URL is idempotent — it upserts the document record and replaces its chunks, so it's safe to re-run after either source updates.

## Known limitation: keyword search, not semantic search

Search ranks results by term frequency — MongoDB's own relevance scoring in the default `text_index` mode, or the in-app TF scorer in `in_app` mode (see [ARCHITECTURE.md](./ARCHITECTURE.md#search-two-interchangeable-modes-text-by-default)) — not by meaning, in either mode. A query using different words than a section's actual text may miss it or rank a more talkative-but-less-relevant section higher. For example, § 24-222 ("After hours and weekend limits on construction work") never uses the word "noise" in its body text, so a bare `"noise"` query ranks § 24-220 ("Noise mitigation plan") above it. Query with the literal terms you expect the target section to contain.

## Known limitation: `mentions_penalty`/`mentions_permit` are keyword heuristics

Both flags are computed by word-boundary keyword matching against a chunk's text (see `app/ingestion/enrich.py`), not by legal analysis — matching is on whole words only (a real bug caught during the full ingestion run: naive substring matching flagged §161.19 as mentioning a "fine" purely because "fine" is a substring of "def**ine**d"). `mentions_permit` is also intentionally broad (it includes "authorized"/"authorization"), so it will flag sections that merely reference an exception or exemption, not only sections that establish an affirmative permit application process. Treat both as a useful filter, not a legal determination — the actual `text` should always be read before asserting a penalty or permit requirement does or doesn't apply.

The same substring-vs-word-boundary bug was independently found a second time, in `app/search_scoring.py`'s in-app scorer, while building `/is_action_allowed`: naive `str.count()` matched "dance" inside "accor**dance**". Both this and the `enrich.py` occurrence are now word-boundary matched (`tests/test_action_rules.py::test_shares_keyword_word_boundary_not_substring`, `tests/test_enrich.py::test_mentions_any_requires_word_boundary_not_substring`).

## Known limitation: `is_action_allowed` can select an irrelevant section on a coincidental keyword match

Because ranking is keyword-based (see above), a query sharing even one common/generic word with an unrelated section can surface an off-topic citation. Found empirically, not theorized: querying `"launch a satellite from my roof"` matched an unrelated building-construction section on the word "roof" (meaning roofing *material*, not rooftop *location*) and returned a confident-looking `allowed: false` citing real but irrelevant text; separately, `"purple unicorn dance party fundraiser"` coincidentally matched an unrelated section via the word "party" (a legal term for a party to an action, not a celebration). The citation and matched text are always real — never fabricated — but the *selected section* can be wrong for homonyms or ambiguous terms, which requires semantic understanding this deliberately non-LLM design doesn't attempt. Two mitigations, not a full fix: (1) generic regulatory verbs ("keep," "operate," "use"...) are excluded from matching (`app/action_rules.py::GENERIC_ACTION_WORDS`) since they're common enough to dominate ranking on their own; (2) confidence is capped below `"high"` whenever the result rests on an absence-of-restriction inference rather than an explicit statement. Neither mitigation can catch a genuinely ambiguous *content* word like "roof" or "party." Pinned deliberately by `tests/test_is_action_allowed.py::test_known_limitation_coincidental_common_word_can_still_match` (documents current behavior so any future change is a decision, not a silent regression) rather than patched with a relevance threshold that risks breaking the correct cases (e.g. "keep a rooster," which correctly returns `allowed: false` at `"high"` confidence).

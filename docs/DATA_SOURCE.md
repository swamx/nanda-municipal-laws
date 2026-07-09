# Data Source

## Source

[nycadmincode.readthedocs.io](https://nycadmincode.readthedocs.io/) — a **CC0 (public domain)**, weekly-updated mirror of the NYC Administrative Code, maintained in connection with MyGov.nyc. Pages are organized by Title → Chapter → Subchapter (e.g. `t24/c02/sch04/` = Title 24, Chapter 2, Subchapter 4), with each individual section addressable by an anchor (`#section-24-222`).

The official canonical source is the NYC Law Department's contracted site at [codelibrary.amlegal.com](https://codelibrary.amlegal.com/codes/newyorkcity/) (American Legal Publishing). That site's scraping terms aren't clearly established for automated reuse, whereas the readthedocs mirror explicitly commits to CC0/public-domain licensing and weekly refreshes from the same underlying source — that's why ingestion targets it instead.

## Current coverage

**NYC Administrative Code, Title 24, Chapter 2 (Noise Control)** — all 8 subchapters, ~110 chunks:

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

This is intentionally a small, real slice of the code rather than the whole Administrative Code — enough to demonstrate the full ingest → search → cite pipeline against genuine legal text, seeded via `scripts/seed_admin_code.py`.

## Extending coverage

To ingest more of the NYC Admin Code:

1. Find the page(s) you want at `https://nycadmincode.readthedocs.io/t{title}/c{chapter}/` (browse the site's table of contents to find title/chapter/subchapter numbers).
2. Call `POST /api/v1/ingest` with those URLs (max `INGEST_MAX_URLS` per call — see [API.md](./API.md#post-apiv1ingest)), or add them to the `NOISE_CONTROL_SUBCHAPTER_URLS`-style list in `scripts/seed_admin_code.py` and re-run it.

Re-ingesting an already-seen URL is idempotent — it upserts the document record and replaces its chunks, so it's safe to re-run after the source site updates.

## Known limitation: keyword search, not semantic search

Search ranks results by term frequency (see [ARCHITECTURE.md](./ARCHITECTURE.md#search-in-app-scoring-not-mongodb-text)), not by meaning. A query using different words than a section's actual text may miss it or rank a more talkative-but-less-relevant section higher. For example, § 24-222 ("After hours and weekend limits on construction work") never uses the word "noise" in its body text, so a bare `"noise"` query ranks § 24-220 ("Noise mitigation plan") above it. Query with the literal terms you expect the target section to contain.

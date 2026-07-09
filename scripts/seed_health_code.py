"""Seed MongoDB with NYC Health Code Article 161 (Animals).

Source: https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf
- a first-party PDF hosted directly by the NYC Department of Health and Mental
Hygiene. Contains §161.19 (Keeping of livestock, live poultry and rabbits) and
§161.09 (Permits to keep certain animals).

Usage (from the repo root, with MONGO_ATLAS_CONN_STR set):
    python -m scripts.seed_health_code
"""

import sys

from app.db import ensure_indexes, get_db
from app.ingestion.pipeline import ingest_url

ARTICLE_161_URL = "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf"
HEALTH_CODE_URLS = [ARTICLE_161_URL]


def main(urls: list[str] = HEALTH_CODE_URLS) -> int:
    db = get_db()
    ensure_indexes(db)

    had_error = False
    for url in urls:
        try:
            chunks_ingested = ingest_url(db, url)
            print(f"OK    {url} -> {chunks_ingested} chunks")
        except Exception as exc:
            had_error = True
            print(f"ERROR {url} -> {exc}", file=sys.stderr)

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())

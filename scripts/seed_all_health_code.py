"""Discovers every NYC Health Code article listed at nyc.gov's Health Code
and Rules index page, then ingests each article PDF into MongoDB.

Usage (from the repo root, with MONGO_ATLAS_CONN_STR set):
    python -m scripts.seed_all_health_code             # every discovered article
    python -m scripts.seed_all_health_code --limit 5   # first 5 discovered articles (testing)
    python -m scripts.seed_all_health_code --article 161   # one specific article
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import httpx

from app.db import ensure_indexes, get_db
from app.ingestion.pipeline import ingest_url

INDEX_URL = "https://www.nyc.gov/site/doh/about/about-doh/health-code-and-rules.page"
ARTICLE_URL_TEMPLATE = "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article{n}.pdf"
DELAY_SECONDS = 0.5
MANIFEST_PATH = Path(__file__).parent / "data" / "health_code_manifest.json"

# nyc.gov returns 403 for non-browser-looking User-Agent strings.
_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def discover_article_numbers() -> list[str]:
    response = httpx.get(INDEX_URL, timeout=15, headers={"User-Agent": _BROWSER_USER_AGENT}, follow_redirects=True)
    response.raise_for_status()
    numbers = sorted(set(re.findall(r"healthcode/health-code-article(\d+)", response.text)), key=int)
    return numbers


def seed_all(limit: int | None = None, article: str | None = None) -> list[dict]:
    db = get_db()
    ensure_indexes(db)

    if article is not None:
        article_numbers = [article]
    else:
        article_numbers = discover_article_numbers()
        if limit is not None:
            article_numbers = article_numbers[:limit]

    if article is not None:
        print(f"ingesting article {article} only")
    else:
        print(f"discovered {len(article_numbers)} Health Code articles")

    manifest = []
    for number in article_numbers:
        url = ARTICLE_URL_TEMPLATE.format(n=number)
        try:
            chunks_ingested = ingest_url(db, url)
            print(f"OK    article {number}: {url} -> {chunks_ingested} chunks")
            manifest.append({"article_num": number, "url": url, "status": "ok", "chunks_ingested": chunks_ingested})
        except Exception as exc:
            print(f"ERROR article {number}: {url} -> {exc}", file=sys.stderr)
            manifest.append({"article_num": number, "url": url, "status": "error", "error": str(exc)})
        time.sleep(DELAY_SECONDS)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nDone. Manifest written to {MANIFEST_PATH}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="ingest only the first N discovered articles")
    parser.add_argument("--article", default=None, help="ingest one specific article number, e.g. 161")
    args = parser.parse_args()

    seed_all(limit=args.limit, article=args.article)

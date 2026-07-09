"""Crawls the entire NYC Administrative Code at nycadmincode.readthedocs.io
and ingests every leaf page (a page with real section content and no further
child pages in its own table of contents) into MongoDB.

Traverses the site's local per-page table-of-contents links generically (not
hardcoded to a fixed Title -> Chapter -> Subchapter depth), since some
chapters go straight to sections, others have subchapters, and at least one
observed chapter (t27/c01/sch12/) has a further "article" level beneath its
subchapter. A page with no local TOC links is treated as a leaf and ingested
directly using the HTML already fetched during the crawl (avoiding a second
fetch per page).

Usage (from the repo root, with MONGO_ATLAS_CONN_STR set):
    python -m scripts.crawl_and_seed_admin_code [--limit N] [--dry-run]
"""

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.db import ensure_indexes, get_db
from app.ingestion.fetcher import fetch_page
from app.ingestion.parser import parse_page
from app.ingestion.pipeline import _persist

BASE_URL = "https://nycadmincode.readthedocs.io/"
DELAY_SECONDS = 0.3
MANIFEST_PATH = Path(__file__).parent / "data" / "admin_code_manifest.json"


def _normalize(url: str) -> str:
    if url.endswith("index.html"):
        url = url[: -len("index.html")]
    return url


def _local_child_links(html: str, current_url: str) -> list[str]:
    """Links in the page's own content-area table of contents (BeautifulSoup
    selector `div.toctree-wrapper a.reference.internal`) - NOT the global
    sidebar, which lists every title on every page. Verified against known
    ground truth (Title 24 has exactly 9 chapters; this selector returns 9).
    """
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("div.toctree-wrapper a.reference.internal")
    urls = []
    for a in links:
        href = a.get("href", "")
        if not href or href == "#":
            continue
        urls.append(_normalize(urljoin(current_url, href)))
    return urls


def crawl_and_seed(limit: int | None = None, dry_run: bool = False, start_url: str = BASE_URL) -> list[dict]:
    db = None if dry_run else get_db()
    if db is not None:
        ensure_indexes(db)

    visited: set[str] = set()
    queue = [start_url]
    manifest: list[dict] = []
    leaf_count = 0

    while queue:
        if limit is not None and leaf_count >= limit:
            break
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            html = fetch_page(url)
        except Exception as exc:
            print(f"ERROR fetching {url} -> {exc}", file=sys.stderr)
            continue
        time.sleep(DELAY_SECONDS)

        children = _local_child_links(html, url)
        if children:
            for child in children:
                if child not in visited:
                    queue.append(child)
            continue

        if url == start_url:
            continue  # the crawl's own starting page is never a leaf

        # Leaf page: parse and persist using the HTML already fetched above.
        try:
            metadata, sections = parse_page(html)
        except ValueError as exc:
            print(f"SKIP  {url} -> {exc}", file=sys.stderr)
            continue

        leaf_count += 1
        chunks_ingested = 0
        if not dry_run:
            chunks_ingested = _persist(db, url, metadata, sections)

        manifest.append(
            {
                "url": url,
                "title_num": metadata.title_num,
                "title_name": metadata.title_name,
                "chapter_num": metadata.chapter_num,
                "chapter_name": metadata.chapter_name,
                "subchapter_num": metadata.subchapter_num,
                "subchapter_name": metadata.subchapter_name,
                "section_count": len(sections),
                "chunks_ingested": chunks_ingested,
            }
        )
        print(f"OK    [{leaf_count}] {url} -> {len(sections)} sections, {chunks_ingested} chunks")

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nDone. {leaf_count} leaf pages processed. Manifest written to {MANIFEST_PATH}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="stop after N leaf pages (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="crawl and print without writing to MongoDB")
    parser.add_argument("--start-url", default=BASE_URL, help="scope the crawl to a subtree (for testing)")
    args = parser.parse_args()

    crawl_and_seed(limit=args.limit, dry_run=args.dry_run, start_url=args.start_url)

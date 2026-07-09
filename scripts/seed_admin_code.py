"""Seed MongoDB with NYC Admin Code Title 24, Chapter 2 (Noise Control).

Source: https://nycadmincode.readthedocs.io/ - a CC0-licensed, weekly-updated
mirror of the official NYC Administrative Code.

Usage (from the repo root, with MONGO_ATLAS_CONN_STR set):
    python -m scripts.seed_admin_code
"""

import sys

from app.db import ensure_indexes, get_db
from app.ingestion.pipeline import ingest_url

_BASE = "https://nycadmincode.readthedocs.io/t24/c02"

NOISE_CONTROL_SUBCHAPTER_URLS = [
    f"{_BASE}/sch01/",  # Short Title, Policy and Definitions
    f"{_BASE}/sch02/",  # General Provisions
    f"{_BASE}/sch03/",  # Prohibited Noise - General Prohibition
    f"{_BASE}/sch04/",  # Construction Noise Management (includes S 24-222)
    f"{_BASE}/sch05/",  # Prohibited Noise - Specific Sources - Sound Level Standard
    f"{_BASE}/sch06/",  # Specific Noise Sources - Plainly Audible and Other Standards
    f"{_BASE}/sch07/",  # Certificates and Tunneling Permits
    f"{_BASE}/sch08/",  # Enforcement
]


def main(urls: list[str] = NOISE_CONTROL_SUBCHAPTER_URLS) -> int:
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

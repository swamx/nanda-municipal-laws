#!/usr/bin/env python
"""CLI for the municipal-bylaws Claude Agent Skill.

Calls the deployed Municipal Bylaws Knowledge API's /search endpoint and
prints the JSON response to stdout.

Usage:
    python query_bylaws.py "construction noise restrictions" [--limit N] [--title 24] [--chapter 2]

Configuration:
    API_BASE_URL  Base URL of the deployed API (e.g. https://your-app.vercel.app).
                  Defaults to http://localhost:8000 for local development.
"""

import argparse
import json
import os
import sys

import requests

DEFAULT_BASE_URL = "http://localhost:8000"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Search NYC municipal bylaws")
    parser.add_argument("query", help="Question or keywords to search for")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--title", dest="title_num", default=None)
    parser.add_argument("--chapter", dest="chapter_num", default=None)
    args = parser.parse_args(argv)

    base_url = os.environ.get("API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    payload = {"query": args.query, "limit": args.limit}
    if args.title_num:
        payload["title_num"] = args.title_num
    if args.chapter_num:
        payload["chapter_num"] = args.chapter_num

    try:
        response = requests.post(f"{base_url}/api/v1/search", json=payload, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stdout)
        return 1

    print(json.dumps(response.json(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

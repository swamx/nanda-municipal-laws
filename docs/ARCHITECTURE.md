# Architecture

## Goal and scope

Expose real NYC municipal bylaw text through a small, stateless REST API that any agent/chatbot can call: search for relevant sections, then retrieve the full document or chunk for citation. Deliberately **not** a RAG/LLM-answer system — no embeddings, no vector database, no LLM-synthesized answers. The API returns ranked, citable results; the caller (e.g. the Claude Agent Skill in `municipal-bylaws-skill/`) decides how to use them.

## Data flow

```
nycadmincode.readthedocs.io (NYC Admin Code, CC0 mirror)
            |
            |  fetch (httpx) -> parse (BeautifulSoup) -> chunk
            v
   app/ingestion/{fetcher,parser,chunker,pipeline}.py
            |
            v
   MongoDB Atlas: mithackathon.dl-laws  (single collection)
            |
            v
        FastAPI app (app/)
            |
   +--------+----------+-----------+
   |        |           |          |
 /search /documents  /ingest   /health, /version
```

Ingestion is on-demand and bounded (`POST /ingest`, max `INGEST_MAX_URLS` pages per call), not a background job — this runs as a Vercel serverless function with a hard execution-time ceiling, so there's no long-lived worker to schedule crawls.

## Storage: one collection, not several

The original design called for separate `documents` and `chunks` collections. In practice, the MongoDB Atlas custom role provisioned for this project grants read/write on exactly one collection name (`dl-laws`) and nothing else — not even `createIndex`. Rather than fight that, both record kinds live in `dl-laws`, distinguished by a `type` field:

```jsonc
// type: "document" — one per ingested chapter/subchapter page
{ "_id", "type": "document", "title_num", "title_name", "chapter_num", "chapter_name",
  "subchapter_num", "subchapter_name", "source_url", "ingested_at", "section_count" }

// type: "chunk" — one per section (or sub-split of a long section)
{ "_id", "type": "chunk", "document_id", "section_number", "section_title",
  "text", "chunk_index", "url", "title_num", "chapter_num", "subchapter_num" }

// type: "ratelimit" — per-client, per-scope request counters (see Rate limiting below)
{ "_id", "type": "ratelimit", "scope": "general" | "ingest", "client_id", "window_start", "count" }
```

`app/db.py` still calls `create_index(...)` for a handful of useful indexes (unique `source_url` for idempotent re-ingestion, a compound `(document_id, chunk_index)`, and `section_number`) but treats failure as **non-fatal** — if the Atlas role doesn't grant `createIndex`, a warning is logged and the app runs on unindexed collections. At this dataset's scale (a few hundred documents), that's a performance footnote, not a correctness problem.

## Search: in-app scoring, not MongoDB `$text`

MongoDB's native `$text`/`textScore` search requires a server-side text index — which, per the above, this Atlas role cannot create. `app/search_scoring.py` implements a small TF-style scorer instead: `POST /search` fetches all `type: "chunk"` documents matching the optional `title_num`/`chapter_num` filters via a plain equality `find()`, then scores each candidate in Python (title matches weighted 5x over body matches), sorts, and returns the top `limit`. This is a keyword search, not a semantic one — term frequency drives ranking, not phrase meaning. It's documented as a real, user-visible limitation in [DATA_SOURCE.md](./DATA_SOURCE.md) and in `SKILL.md`, not hidden: e.g. a bare "noise" query ranks § 24-220 ("Noise mitigation plan") above § 24-222 ("After hours and weekend limits on construction work"), since 24-222's body text never uses the word "noise" at all.

Fine at this scale (currently ~110 chunks); if coverage grows to the point where fetching all candidates into Python becomes a bottleneck, the fix is either getting `createIndex` granted on `dl-laws` (switch back to native `$text`) or moving to Atlas Search (Lucene-based, doesn't need the classic `createIndex` privilege).

## Rate limiting: MongoDB-backed, not in-memory

Vercel serverless functions don't share process memory across invocations or cold starts, so a naive in-process rate limiter (a `dict` of counters) would not enforce a real per-client limit once traffic spans more than one warm instance. `app/rate_limit.py` implements two FastAPI dependencies backed by the same mechanism: `rate_limiter` (applied to `search`, `documents`, and `health` routers, default `RATE_LIMIT_PER_MINUTE` = 10) and `ingest_rate_limiter` (applied only to the `ingest` router, default `INGEST_RATE_LIMIT_PER_MINUTE` = 1 — much stricter, since that endpoint triggers outbound fetches and Atlas writes rather than just reads). Both call a shared `_check_rate_limit(request, db, scope, limit)` helper that increments a per-minute counter document in `dl-laws` (`type: "ratelimit"`, keyed by `scope` + `client_id` + `window_start`) via an atomic `find_one_and_update` with `$inc`, and rejects with `429` once the count for that scope exceeds its limit in the current 60-second window. The `scope` field keeps the two limiters' counters independent, so a client hitting `/ingest` once doesn't eat into their `/search` budget or vice versa. Client identity is best-effort: the first IP in `X-Forwarded-For` (Vercel's proxy header), falling back to the raw socket address.

It **fails open**: if Mongo is unreachable, the limiter logs a warning and lets the request through rather than taking the whole API down over a rate-limiting hiccup. Stale rate-limit documents are cleaned up opportunistically (a small random-chance `delete_many` on old windows) rather than via a TTL index, since TTL indexes also require `createIndex`.

## Why a FastAPI dependency, not ASGI middleware, for rate limiting and auth

Both rate limiters and the `/ingest` API-key gate are implemented as FastAPI `Depends()` functions rather than Starlette `BaseHTTPMiddleware`. Middleware runs outside FastAPI's dependency-injection graph, so it can't be swapped out via `app.dependency_overrides` in tests — a middleware-based limiter would have forced every test through a real (and in CI, unreachable) MongoDB connection, which is slow and flaky. As a dependency, `rate_limiter`/`ingest_rate_limiter` each take `db: Database = Depends(get_db)`, so tests override `get_db` exactly once and every dependent — routes and both rate limiters alike — automatically uses the fake in-memory Mongo double (`tests/fake_mongo.py`).

## Directory layout

```
app/
  main.py              FastAPI app, middleware, routers, global exception handler
  config.py            pydantic-settings: all env-configurable behavior
  db.py                Mongo client singleton, collection name, best-effort index creation
  models.py             Pydantic request/response schemas
  search_scoring.py     in-app keyword scoring (see "Search" above)
  rate_limit.py         Mongo-backed per-client rate limiting dependency
  routers/               search, documents, ingest, health/version
  ingestion/             fetcher (httpx), parser (BeautifulSoup), chunker, pipeline (glue)
api/index.py            Vercel entrypoint (re-exports app.main:app)
scripts/seed_admin_code.py   ingest Title 24 Ch. 2 (Noise Control) into MongoDB
municipal-bylaws-skill/   the Claude Agent Skill that calls this API
tests/                   parser + ingestion + API + rate-limit tests, run against a fake Mongo
docs/                    this folder
```

## Testing strategy

No live MongoDB is required to run the test suite. `tests/fake_mongo.py` implements the small subset of the pymongo API this app actually uses (equality `find`/`find_one`, `find_one_and_update` with `$set`/`$inc`, `insert_many`, `delete_many`) as a pure-Python in-memory double, injected via `app.dependency_overrides[get_db]`. Ingestion tests monkeypatch `fetch_page` to return a real, committed HTML fixture (`tests/fixtures/t24_c02_sch04.html`, an actual fetched page from the live site) rather than synthetic markup, so the parser is pinned against genuine NYC Admin Code HTML. The full suite (parsing, ingestion, search ranking, document retrieval, rate limiting, ingest auth) runs in well under a second.

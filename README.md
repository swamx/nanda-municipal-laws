# Municipal Bylaws Knowledge API

A lightweight FastAPI service that indexes real NYC Administrative Code text in MongoDB and exposes keyword search + document/chunk retrieval, for consumption by the `municipal-bylaws-skill` Claude Agent Skill (or any other agent/chatbot). Built for the MIT Hackathon.

Scope, deliberately kept small:
- **Keyword search only** (in-app TF-style keyword scoring over the stored chunks — no MongoDB text index, since the Atlas role used here doesn't grant `createIndex`) — no embeddings, vector DB, or LLM-synthesized answers. The API returns ranked results with citations; the caller decides how to use them.
- **Source data**: [nycadmincode.readthedocs.io](https://nycadmincode.readthedocs.io/), a CC0-licensed, weekly-updated mirror of the NYC Administrative Code. Seeded content currently covers **Title 24, Chapter 2 (Noise Control)** only.
- **Storage**: MongoDB (Atlas free tier works fine for low request volume) — a single `dl-laws` collection.
- **Hosting**: Vercel free/Hobby tier (zero-config FastAPI/ASGI support), or any ASGI host via `uvicorn`.
- **Hardened for a public demo URL**: per-client rate limiting (10 req/min by default on `/search`, `/documents/*`, `/health`, `/version`; a much stricter 1 req/min on `/ingest` since it triggers outbound fetches and Atlas writes), an optional shared-secret gate on `/ingest`, fast-fail Mongo timeouts, pinned dependencies, and a global exception handler that never leaks stack traces.

📖 **Full docs:** [docs/](./docs/) — [architecture](./docs/ARCHITECTURE.md), [API reference](./docs/API.md), [deployment](./docs/DEPLOYMENT.md), [data source](./docs/DATA_SOURCE.md). Agent-facing quick reference: [SKILL.md](./SKILL.md).

## Project layout

```
app/            FastAPI app: config, db, rate limiting, search scoring, routers, ingestion pipeline
api/index.py    Vercel entrypoint (re-exports app.main:app)
scripts/        seed_admin_code.py - ingest Title 24 Ch.2 into MongoDB
tests/          parser + ingestion + API + rate-limit tests (run against a fake in-memory Mongo)
docs/           architecture, API reference, deployment, data source
municipal-bylaws-skill/   the Claude Agent Skill (SKILL.md + CLI) that calls this API
SKILL.md        agent-facing API reference (hackathon-format: endpoints, curl, usage steps)
```

## Quick start

### 1. Set up MongoDB

1. Create a free MongoDB Atlas M0 cluster at https://www.mongodb.com/cloud/atlas.
2. Create a database user and, under Network Access, allow access from anywhere (`0.0.0.0/0`) so serverless functions can reach it. Only read/write on one collection (`dl-laws`) is required — no `createIndex` privilege needed.
3. Copy the SRV connection string.

### 2. Configure environment

```
cp .env.example .env
# edit .env: set MONGO_ATLAS_CONN_STR to your Atlas connection string
```

See [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) for the full list of environment variables (rate limit, ingest API key, timeouts, etc).

### 3. Install dependencies and run locally

```
python -m venv .venv
.venv\Scripts\activate        # or: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Check `GET http://localhost:8000/api/v1/health` returns `{"status": "ok"}` (requires a reachable Mongo).

### 4. Seed real bylaw data

```
python -m scripts.seed_admin_code
```

This ingests the 8 subchapters of NYC Admin Code Title 24 Chapter 2 (Noise Control) — including § 24-222, "After hours and weekend limits on construction work" — attempting to create supporting indexes along the way (best-effort; search works fine without them).

### 5. Try it

```
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "after hours weekend limits construction work"}'
```

Note this is keyword search, not semantic search: term frequency drives ranking, so phrase meaning doesn't always win — e.g. a bare "noise" query ranks § 24-220 ("Noise mitigation plan") above § 24-222, since 24-222's body never uses the word "noise". Query with the literal terms you expect in the target section. More curl examples for every endpoint: [docs/API.md](./docs/API.md).

### 6. Run tests

```
python -m pytest tests/ -v
```

Tests run against a fake in-memory Mongo double (`tests/fake_mongo.py`), including the rate limiter and ingest auth gate, so the full suite runs in well under a second with no live database needed.

### 7. Deploy to Vercel

```
npm i -g vercel      # if you don't already have the CLI
vercel dev            # sanity-check locally first
vercel                 # deploy
vercel env add MONGO_ATLAS_CONN_STR production
vercel env add INGEST_API_KEY production     # recommended before sharing the URL publicly
```

Full deployment walkthrough, env var table, and prod-readiness notes: [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md).

## API summary

All endpoints except `/` are under `/api/v1` and rate-limited per client IP (default 10 req/min, except `/ingest` at a stricter 1 req/min). Full reference with curl examples and sample responses: [docs/API.md](./docs/API.md).

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Service info (not rate-limited) |
| `/api/v1/health` | GET | `{"status": "ok" \| "degraded"}` based on live Mongo reachability |
| `/api/v1/version` | GET | `{"version": "..."}` |
| `/api/v1/search` | POST | `{query, limit?, title_num?, chapter_num?}` → ranked `results` (section, url, score, snippet) |
| `/api/v1/documents/{id}` | GET | Document metadata (title/chapter/subchapter, source URL) |
| `/api/v1/documents/{id}/chunks` | GET | All chunks (sections) belonging to a document |
| `/api/v1/ingest` | POST | `{urls: [...]}` (max 10) — fetch, parse, and persist a bounded batch of pages. Gated by `INGEST_API_KEY` if configured; limited to 1 req/min (its own stricter bucket, separate from the general 10/min). |

## Extending coverage

To ingest more of the NYC Admin Code, call `POST /api/v1/ingest` with additional `nycadmincode.readthedocs.io` chapter/subchapter URLs (max `INGEST_MAX_URLS` per call), or add more URLs to `scripts/seed_admin_code.py` and re-run it. Re-ingesting an already-seen URL is idempotent (upserts the document, replaces its chunks). Details: [docs/DATA_SOURCE.md](./docs/DATA_SOURCE.md).

# Municipal Legal Intelligence Service

A lightweight FastAPI service that indexes real NYC municipal law text in MongoDB and exposes deterministic, citation-backed retrieval — section search, exact lookup, cross-reference resolution, and penalty/permit filtering — for consumption by an autonomous agent (via `municipal-bylaws-skill`, a Claude Agent Skill, or any other agent/chatbot). Built for the MIT Hackathon.

Positioning: agent tool calls return structured facts with citations and mechanical `reasoning`, not "search → 14 PDFs, good luck." The backend never calls an LLM and never fabricates an answer — see [SKILL.md](./SKILL.md) for exactly how a calling agent should compose its final response from what this API returns.

Scope, deliberately kept small:
- **Keyword search only** (in-app TF-style keyword scoring over the stored chunks — no MongoDB text index, since the Atlas role used here doesn't grant `createIndex`) — no embeddings, vector DB, or LLM-synthesized answers. The API returns ranked results with citations and a `reasoning` string; the caller decides how to use them.
- **Two real sources**: [nycadmincode.readthedocs.io](https://nycadmincode.readthedocs.io/) (CC0-licensed HTML mirror of the NYC Administrative Code — **Title 24, Chapter 2, Noise Control**) and first-party NYC Health Code PDFs at `nyc.gov` (**Article 161, Animals** — including §161.19, the chicken/poultry-keeping section). Two ingestion formats, one shared pipeline.
- **Storage**: MongoDB (Atlas free tier works fine for low request volume) — a single `dl-laws` collection.
- **Hosting**: Vercel free/Hobby tier (zero-config FastAPI/ASGI support), or any ASGI host via `uvicorn`.
- **Hardened for a public demo URL**: per-client rate limiting (10 req/min by default on read endpoints; a much stricter 1 req/min on `/ingest` since it triggers outbound fetches and Atlas writes), an optional shared-secret gate on `/ingest`, fast-fail Mongo timeouts, pinned dependencies, and a global exception handler that never leaks stack traces.

📖 **Full docs:** [docs/](./docs/) — [architecture](./docs/ARCHITECTURE.md), [API reference](./docs/API.md), [deployment](./docs/DEPLOYMENT.md), [data source](./docs/DATA_SOURCE.md). Agent-facing quick reference: [SKILL.md](./SKILL.md).

## Project layout

```
app/            FastAPI app: config, db, rate limiting, retrieval, models, routers, ingestion pipeline
api/index.py    Vercel entrypoint (re-exports app.main:app)
scripts/        seed_admin_code.py, seed_health_code.py - ingest both sources into MongoDB
tests/          parser + ingestion + API + rate-limit + section/related/topic-filter tests (fake in-memory Mongo)
docs/           architecture, API reference, deployment, data source
municipal-bylaws-skill/   the Claude Agent Skill (SKILL.md + CLI) that calls this API
SKILL.md        agent-facing API reference (endpoints, curl, composing a final answer, usage steps)
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

### 4. Seed real law data

```
python -m scripts.seed_admin_code
python -m scripts.seed_health_code
```

The first ingests all 8 subchapters of NYC Admin Code Title 24 Chapter 2 (Noise Control), including § 24-222. The second ingests NYC Health Code Article 161 (Animals), including §161.19 — the chicken/poultry-keeping section. Both attempt to create supporting indexes along the way (best-effort; search works fine without them).

### 5. Try it

```
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "rooster keeping poultry", "document_type": "NYC Health Code"}'

curl http://localhost:8000/api/v1/sections/161.19
```

Note this is keyword search, not semantic search: term frequency drives ranking. It's also worth knowing that popular internet folklore claims NYC caps backyard chickens at "a maximum of 6 hens" — the real ingested text of §161.19 states no such number (see [docs/DATA_SOURCE.md](./docs/DATA_SOURCE.md)). More curl examples for every endpoint: [docs/API.md](./docs/API.md).

### 6. Run tests

```
python -m pytest tests/ -v
```

Tests run against a fake in-memory Mongo double (`tests/fake_mongo.py`), including the rate limiter, ingest auth gate, both ingestion formats, and the new section/related-laws/penalty/permit endpoints, so the full suite runs in well under a second with no live database needed.

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

All endpoints except `/` and `/skill.md` are under `/api/v1` and rate-limited per client IP (default 10 req/min, except `/ingest` at a stricter 1 req/min). Full reference with curl examples and sample responses: [docs/API.md](./docs/API.md).

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Service info (not rate-limited) |
| `/skill.md` | GET | Serves the root `SKILL.md` as plain text (not rate-limited) |
| `/api/v1/health` | GET | `{"status": "ok" \| "degraded"}` based on live Mongo reachability |
| `/api/v1/version` | GET | `{"version": "..."}` |
| `/api/v1/search` | POST | `{query, limit?, title_num?, chapter_num?, document_type?, agency?, topic?}` → ranked `results` + `reasoning` |
| `/api/v1/sections/{section_number}` | GET | Exact lookup by section number — full metadata, cross-references, and a deterministic `structural_summary` |
| `/api/v1/sections/{section_number}/related` | GET | Resolves that section's cross-references into their own citations |
| `/api/v1/penalties` | POST | `{query?, topic?}` → results filtered to sections flagged as mentioning a penalty |
| `/api/v1/permits` | POST | `{query?, topic?}` → results filtered to sections flagged as mentioning a permit requirement |
| `/api/v1/documents/{id}` | GET | Document metadata (title/chapter/subchapter or article, source URL) |
| `/api/v1/documents/{id}/chunks` | GET | All chunks (sections) belonging to a document |
| `/api/v1/ingest` | POST | `{urls: [...]}` (max 10) — fetch, parse, and persist a bounded batch of pages/PDFs. Gated by `INGEST_API_KEY` if configured; limited to 1 req/min (its own stricter bucket). |

**Not supported** (documented, not faked): zoning lookup by address (needs GIS/PLUTO data, a different domain), and comparing two revisions of a section over time (needs historical snapshots this pipeline doesn't retain).

## Extending coverage

**Admin Code**: call `POST /api/v1/ingest` with additional `nycadmincode.readthedocs.io` chapter/subchapter URLs, or add them to `scripts/seed_admin_code.py`. **Health Code**: any `health-code-article{N}.pdf` follows the same URL pattern and parses automatically (article metadata is derived from the PDF's own header text, not hardcoded) — add it to `scripts/seed_health_code.py` or `POST /api/v1/ingest` directly. Re-ingesting an already-seen URL is idempotent. Details: [docs/DATA_SOURCE.md](./docs/DATA_SOURCE.md).

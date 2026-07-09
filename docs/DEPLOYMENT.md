# Deployment

## 1. MongoDB Atlas

1. Create a free M0 cluster at https://www.mongodb.com/cloud/atlas.
2. Create a database user. **Note:** this project's role only needs read/write on one collection: `dl-laws` in the `mithackathon` database (or whatever you name it via `MONGODB_DB_NAME`). It does **not** need `createIndex` — the app treats index creation as best-effort and falls back to in-app search scoring if that privilege is denied (see [ARCHITECTURE.md](./ARCHITECTURE.md)).
3. Under Network Access, allow `0.0.0.0/0` so Vercel's serverless functions (which don't have static IPs) can connect.
4. Copy the SRV connection string — this is your `MONGO_ATLAS_CONN_STR`.

## 2. Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `MONGO_ATLAS_CONN_STR` | yes | — | MongoDB connection string |
| `MONGODB_DB_NAME` | no | `mithackathon` | Database name |
| `CORS_ORIGINS` | no | `*` | Comma-separated allowed origins. Tighten before sharing widely. |
| `MONGO_CONNECT_TIMEOUT_MS` | no | `5000` | Fail fast on a bad/unreachable Mongo URI rather than hang until Vercel's own function timeout |
| `MONGO_SERVER_SELECTION_TIMEOUT_MS` | no | `5000` | Same |
| `INGEST_API_KEY` | no | unset (open) | If set, `POST /ingest` requires a matching `X-Ingest-Api-Key` header. **Set this before sharing a public deployment URL** — otherwise anyone can trigger outbound fetches and Atlas writes. |
| `INGEST_MAX_URLS` | no | `10` | Hard cap on URLs per `/ingest` call, to stay inside the serverless execution budget |
| `RATE_LIMIT_PER_MINUTE` | no | `10` | Requests/minute per client IP for `/search`, `/documents/*`, `/health`, `/version` |
| `INGEST_RATE_LIMIT_PER_MINUTE` | no | `1` | Requests/minute per client IP for `/ingest` specifically — its own stricter bucket, since it triggers outbound fetches and Atlas writes |
| `APP_VERSION` | no | `0.1.0` | Reported by `/` and `/api/v1/version` |

Copy `.env.example` to `.env` and fill these in for local development.

## 3. Local development

```bash
python -m venv .venv
.venv\Scripts\activate        # or: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Seed real data:

```bash
python -m scripts.seed_admin_code
```

## 4. Run tests

```bash
python -m pytest tests/ -v
```

No live MongoDB is needed — tests run against an in-memory fake (see [ARCHITECTURE.md](./ARCHITECTURE.md#testing-strategy)).

## 5. Deploy to Vercel (free/Hobby tier)

```bash
npm i -g vercel      # if you don't already have the CLI
vercel dev            # sanity-check locally first
vercel                 # deploy
vercel env add MONGO_ATLAS_CONN_STR production
vercel env add MONGODB_DB_NAME production
vercel env add INGEST_API_KEY production     # strongly recommended for a public URL
vercel env add RATE_LIMIT_PER_MINUTE production   # optional, defaults to 10
```

Vercel auto-discovers the FastAPI `app` instance via `api/index.py` (zero-config ASGI support — no `mangum` adapter needed). `vercel.json` sets `maxDuration: 60`, the maximum allowed on the Hobby plan without Fluid Compute, giving `/ingest` headroom to fetch multiple pages in one call. If you enable Fluid Compute, Hobby supports up to 300s — raise `maxDuration` accordingly if you plan to ingest larger batches.

After deploying, re-run the seed script against the same Atlas cluster (it's independent of which server — local or Vercel — is running; the data lives in Atlas either way), then smoke-test:

```bash
curl -s https://your-app.vercel.app/api/v1/health
curl -s -X POST https://your-app.vercel.app/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "after hours weekend limits construction work"}'
```

## Production-readiness notes (hackathon-appropriate, not enterprise-grade)

- **Rate limiting** is on by default (10 req/min/IP generally, 1 req/min/IP on `/ingest`) and backed by MongoDB so it holds up across serverless cold starts — see [ARCHITECTURE.md](./ARCHITECTURE.md#rate-limiting-mongodb-backed-not-in-memory). It fails open if Mongo is briefly unreachable, rather than blocking all traffic.
- **`/ingest` should be locked down** with `INGEST_API_KEY` before sharing a deployment URL publicly — it triggers outbound HTTP fetches and Atlas writes and is otherwise open by default for frictionless local/demo use.
- **CORS defaults to `*`** for demo convenience. Set `CORS_ORIGINS` to your actual frontend origin(s) for anything beyond a hackathon demo.
- **Errors don't leak internals**: a global exception handler catches anything unhandled and returns a generic `500` — details go to server logs (visible in the Vercel dashboard), not the response body.
- **Dependencies are pinned** (`requirements.txt`) for reproducible Vercel builds. `uvicorn` is dev-only (in `requirements-dev.txt`) since Vercel's Python runtime doesn't need it.
- **No secrets are committed** — `.env` is gitignored; `.env.example` documents the shape without real values.

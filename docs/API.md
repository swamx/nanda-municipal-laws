# API Reference

Base URL (local dev): `http://localhost:8000`
Base URL (deployed): your Vercel deployment URL, e.g. `https://nanda-municipal-laws.vercel.app`

All endpoints except `GET /` and `GET /skill.md` are under `/api/v1` and are rate-limited per client IP, in two separate buckets: `RATE_LIMIT_PER_MINUTE` (default **10**/min) for `/search`, `/documents/*`, `/health`, and `/version`; `INGEST_RATE_LIMIT_PER_MINUTE` (default **1**/min) for `/ingest`, since it triggers outbound fetches and Atlas writes rather than just reads. Exceeding either returns `429` with a `Retry-After` header.

---

## `GET /`

Service info — name, version, and links. Not rate-limited.

```bash
curl -s http://localhost:8000/
```

```json
{"name":"Municipal Bylaws Knowledge API","version":"0.1.0","docs":"/docs","health":"/api/v1/health","skill":"/skill.md"}
```

---

## `GET /skill.md`

Serves the repo's root `SKILL.md` as plain text — the agent-facing API reference, live from the running deployment rather than a file an agent has to separately clone/fetch from source. Not rate-limited.

```bash
curl -s http://localhost:8000/skill.md
```

Returns the raw Markdown content of [`SKILL.md`](../SKILL.md).

---

## `GET /api/v1/health`

Live health check — pings MongoDB. Returns `200` either way; the `status` field reflects reachability.

```bash
curl -s http://localhost:8000/api/v1/health
```

```json
{"status": "ok"}
```

`"status": "degraded"` means MongoDB is unreachable.

---

## `GET /api/v1/version`

```bash
curl -s http://localhost:8000/api/v1/version
```

```json
{"version": "0.1.0"}
```

---

## `POST /api/v1/search`

Keyword search over ingested bylaw sections. Returns a ranked list of results with citations — no synthesized answer.

Request body:

| field | type | required | notes |
|---|---|---|---|
| `query` | string | yes | keywords to search for (not a natural-language question — term frequency drives ranking) |
| `limit` | int | no | default 10, max 50 |
| `title_num` | string | no | filter to e.g. `"24"` |
| `chapter_num` | string | no | filter to e.g. `"2"` |

```bash
curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "after hours weekend limits construction work"}'
```

```json
{
  "query": "after hours weekend limits construction work",
  "results": [
    {
      "document_id": "6a4fa65d15b368181963450f",
      "section_number": "24-222",
      "section_title": "After hours and weekend limits on construction work",
      "url": "https://nycadmincode.readthedocs.io/t24/c02/sch04/#section-24-222",
      "score": 42.0,
      "snippet": "§ 24-222 After hours and weekend limits on construction work. Except as otherwise provided..."
    }
  ],
  "count": 1
}
```

---

## `GET /api/v1/documents/{id}`

Metadata for one ingested chapter/subchapter page, by the `document_id` returned from `/search`.

```bash
curl -s http://localhost:8000/api/v1/documents/6a4fa65d15b368181963450f
```

```json
{
  "id": "6a4fa65d15b368181963450f",
  "title_num": "24",
  "title_name": "ENVIRONMENTAL PROTECTION AND UTILITIES",
  "chapter_num": "2",
  "chapter_name": "NOISE CONTROL",
  "subchapter_num": "4",
  "subchapter_name": "CONSTRUCTION NOISE MANAGEMENT",
  "source_url": "https://nycadmincode.readthedocs.io/t24/c02/sch04/",
  "ingested_at": "2026-07-09T13:47:09.793000",
  "section_count": 6
}
```

Returns `404` if the id doesn't exist.

---

## `GET /api/v1/documents/{id}/chunks`

All sections belonging to a document, ordered by `chunk_index`.

```bash
curl -s http://localhost:8000/api/v1/documents/6a4fa65d15b368181963450f/chunks
```

```json
[
  {
    "section_number": "24-219",
    "section_title": "Noise mitigation rules",
    "text": "§ 24-219 Noise mitigation rules. (a) The commissioner shall adopt rules...",
    "url": "https://nycadmincode.readthedocs.io/t24/c02/sch04/#section-24-219",
    "chunk_index": 0
  }
]
```

Returns `404` if the parent document doesn't exist.

---

## `POST /api/v1/ingest`

Fetches, parses, and persists a bounded batch of `nycadmincode.readthedocs.io` chapter/subchapter pages. Max `INGEST_MAX_URLS` (default 10) URLs per call — this runs synchronously within one serverless invocation, so keep batches small.

Limited to `INGEST_RATE_LIMIT_PER_MINUTE` (default **1**) request per minute per client — its own bucket, separate from the general 10/min limit on other endpoints, since this is the one endpoint that triggers outbound fetches and writes to Atlas.

If `INGEST_API_KEY` is set in the environment, requests must include a matching `X-Ingest-Api-Key` header or get `401`. Unset by default for local/demo use.

```bash
curl -s -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -H "X-Ingest-Api-Key: <your key, if configured>" \
  -d '{"urls": ["https://nycadmincode.readthedocs.io/t24/c02/sch08/"]}'
```

```json
{
  "results": [
    {"url": "https://nycadmincode.readthedocs.io/t24/c02/sch08/", "status": "ok", "chunks_ingested": 21, "error": null}
  ]
}
```

Re-ingesting an already-seen URL is idempotent (upserts the document, replaces its chunks). A per-URL fetch/parse failure is reported as `"status": "error"` for that item — the whole request still returns `200`.

---

## Errors

| status | meaning |
|---|---|
| `400` | bad request (e.g. `/ingest` batch exceeds `INGEST_MAX_URLS`) |
| `401` | missing/invalid `X-Ingest-Api-Key` on `/ingest` (only if `INGEST_API_KEY` is configured) |
| `404` | document not found |
| `429` | rate limit exceeded (`Retry-After` header included) |
| `500` | unhandled server error — logged server-side, response body is a generic `{"detail": "internal server error"}` (no stack traces leaked to clients) |

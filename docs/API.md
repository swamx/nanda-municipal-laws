# API Reference

Base URL (local dev): `http://localhost:8000`
Base URL (deployed): `https://nanda-municipal-laws.vercel.app`

All endpoints except `GET /` and `GET /skill.md` are under `/api/v1` and are rate-limited per client IP, in two separate buckets: `RATE_LIMIT_PER_MINUTE` (default **10**/min) for `/search`, `/sections/*`, `/penalties`, `/permits`, `/documents/*`, `/health`, and `/version`; `INGEST_RATE_LIMIT_PER_MINUTE` (default **1**/min) for `/ingest`, since it triggers outbound fetches and Atlas writes rather than just reads. Exceeding either returns `429` with a `Retry-After` header.

Every retrieval endpoint returns a `reasoning: str` field explaining *how* the result was mechanically derived (terms matched, filters applied, lookup type) — never an `answer` or `confidence` field. This API is deterministic and does not call an LLM; composing a final natural-language answer (with a confidence label) is the calling agent's job. See [SKILL.md](../SKILL.md) for the exact contract agents should follow.

---

## `GET /`

Service info — name, version, and links. Not rate-limited.

```bash
curl -s http://localhost:8000/
```

```json
{"name":"Municipal Legal Intelligence Service","version":"0.1.0","docs":"/docs","health":"/api/v1/health","skill":"/skill.md"}
```

---

## `GET /skill.md`

Serves the repo's root `SKILL.md` as plain text — the agent-facing API reference, live from the running deployment. Not rate-limited.

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

Keyword search over ingested law sections. Returns a ranked list of results with citations and a `reasoning` string — no synthesized answer.

Request body:

| field | type | required | notes |
|---|---|---|---|
| `query` | string | yes | keywords to search for (not a natural-language question — term frequency drives ranking) |
| `limit` | int | no | default 10, max 50 |
| `title_num` | string | no | admin code filter, e.g. `"24"` |
| `chapter_num` | string | no | admin code filter, e.g. `"2"` |
| `document_type` | string | no | `"NYC Administrative Code"` or `"NYC Health Code"` |
| `agency` | string | no | e.g. `"Department of Health and Mental Hygiene (DOHMH)"` |
| `topic` | string | no | chapter/article name, e.g. `"ANIMALS"` |

```bash
curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "rooster keeping poultry", "document_type": "NYC Health Code"}'
```

```json
{
  "query": "rooster keeping poultry",
  "results": [
    {
      "document_id": "6a4fa65d15b368181963450f",
      "section_number": "161.19",
      "section_title": "Keeping of livestock, live poultry and rabbits",
      "url": "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf#page=14",
      "score": 12.0,
      "snippet": "§161.19 Keeping of livestock, live poultry and rabbits. (a) No person shall keep a live rooster...",
      "document_type": "NYC Health Code",
      "agency": "Department of Health and Mental Hygiene (DOHMH)",
      "topic": "ANIMALS"
    }
  ],
  "count": 1,
  "reasoning": "matched query 'rooster keeping poultry' against 41 candidate chunk(s) after applying filters; ranked by term frequency, title weighted higher than body"
}
```

---

## `GET /api/v1/sections/{section_number}`

Exact lookup by section number (`161.19`, `24-222`, ...) — not a Mongo document id. Aggregates all chunks sharing that number (a long section may have been split by the chunker) and returns full metadata plus a deterministic `structural_summary` (one bullet per lettered/numbered subsection, split on sentence-bounded markers like `(a)`/`(b)`/`(1)` — **not** abstractive summarization).

```bash
curl -s http://localhost:8000/api/v1/sections/161.19
```

```json
{
  "section_number": "161.19",
  "section_title": "Keeping of livestock, live poultry and rabbits",
  "text": "§161.19 Keeping of livestock, live poultry and rabbits. (a) No person shall keep a live rooster...",
  "url": "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf#page=14",
  "document_type": "NYC Health Code",
  "agency": "Department of Health and Mental Hygiene (DOHMH)",
  "topic": "ANIMALS",
  "jurisdiction": "New York City",
  "keywords": ["keeping", "livestock", "live", "poultry", "rabbits"],
  "cross_references": ["161.01"],
  "mentions_penalty": false,
  "mentions_permit": true,
  "effective_date": null,
  "repealed": false,
  "structural_summary": ["(a) No person shall keep a live rooster...", "(b) A person who is authorized...", "(c) Live rabbit and poultry markets..."],
  "chunk_count": 1,
  "reasoning": "exact lookup by section_number='161.19'; structural_summary derived by splitting text on sentence-bounded lettered/numbered subsection markers; no query scoring involved"
}
```

`effective_date` is always `null` (honestly untracked — neither source exposes a reliable machine-readable effective date). `repealed` defaults to `false` (documented assumption: both sources serve current in-force text). Returns `404` if the section number doesn't exist in the corpus.

---

## `GET /api/v1/sections/{section_number}/related`

Resolves the section's `cross_references` (regex-extracted `§X.XX` mentions in its own body text) into their own citations — a one-hop citation graph, no graph database required.

```bash
curl -s http://localhost:8000/api/v1/sections/161.19/related
```

```json
{
  "section_number": "161.19",
  "related": [
    {"section_number": "161.01", "section_title": "Wild and other animals prohibited", "url": "https://.../health-code-article161.pdf#page=1", "document_type": "NYC Health Code", "resolved": true}
  ],
  "reasoning": "extracted 1 cross-reference(s) from §161.19's body text via regex; 1 of 1 resolved against the ingested corpus"
}
```

A reference to a section outside the ingested corpus is included with `"resolved": false` and null `section_title`/`url`/`document_type` — shown, not silently dropped. Returns `404` if `section_number` itself doesn't exist.

---

## `POST /api/v1/penalties`

Filters to chunks flagged `mentions_penalty: true` (keyword heuristic — see [DATA_SOURCE.md](./DATA_SOURCE.md#known-limitation-mentions_penaltymentions_permit-are-keyword-heuristics)). Optional `query` (adds term-frequency ranking on top of the filter) and `topic`.

```bash
curl -s -X POST http://localhost:8000/api/v1/penalties \
  -H "Content-Type: application/json" -d '{"topic": "NOISE CONTROL"}'
```

Response shape matches `/search` (`results`/`count`/`reasoning`), scoped to penalty-flagged chunks.

---

## `POST /api/v1/permits`

Filters to chunks flagged `mentions_permit: true`. Optional `query` and `topic`.

```bash
curl -s -X POST http://localhost:8000/api/v1/permits \
  -H "Content-Type: application/json" -d '{"query": "keep certain animals"}'
```

Response shape matches `/search`, scoped to permit-flagged chunks — e.g. surfaces §161.09 ("Permits to keep certain animals") for the example above.

---

## `GET /api/v1/documents/{id}`

Metadata for one ingested source document (an admin-code chapter/subchapter page, or a health-code article), by the `document_id` returned from `/search`.

```bash
curl -s http://localhost:8000/api/v1/documents/6a4fa65d15b368181963450f
```

```json
{
  "id": "6a4fa65d15b368181963450f",
  "document_type": "NYC Health Code",
  "agency": "Department of Health and Mental Hygiene (DOHMH)",
  "topic": "ANIMALS",
  "title_num": null,
  "chapter_num": null,
  "subchapter_num": null,
  "article_num": "161",
  "article_name": "ANIMALS",
  "source_url": "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf",
  "ingested_at": "2026-07-09T13:47:09.793000",
  "section_count": 16
}
```

`title_num`/`chapter_num`/`subchapter_num` are populated for admin-code documents and `null` for health-code documents (which have `article_num`/`article_name` instead) — the two source types share one schema with the fields that don't apply left empty, rather than two incompatible response shapes. Returns `404` if the id doesn't exist.

---

## `GET /api/v1/documents/{id}/chunks`

All sections belonging to a document, ordered by `chunk_index`, each carrying the full v2 metadata (`document_type`, `agency`, `topic`, `keywords`, `cross_references`, `mentions_penalty`, `mentions_permit`).

```bash
curl -s http://localhost:8000/api/v1/documents/6a4fa65d15b368181963450f/chunks
```

Returns `404` if the parent document doesn't exist.

---

## `POST /api/v1/ingest`

Fetches, parses, and persists a bounded batch of source pages/documents. Dispatches automatically by URL suffix: `nycadmincode.readthedocs.io` HTML pages use the admin-code parser; any `.pdf` URL uses the health-code PDF parser (`pypdf`-based, reusable for other `health-code-article{N}.pdf` files beyond Article 161). Max `INGEST_MAX_URLS` (default 10) URLs per call — this runs synchronously within one serverless invocation, so keep batches small.

Limited to `INGEST_RATE_LIMIT_PER_MINUTE` (default **1**) request per minute per client — its own bucket, separate from the general 10/min limit on other endpoints.

If `INGEST_API_KEY` is set in the environment, requests must include a matching `X-Ingest-Api-Key` header or get `401`. Unset by default for local/demo use.

```bash
curl -s -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -H "X-Ingest-Api-Key: <your key, if configured>" \
  -d '{"urls": ["https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf"]}'
```

```json
{
  "results": [
    {"url": "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf", "status": "ok", "chunks_ingested": 41, "error": null}
  ]
}
```

Re-ingesting an already-seen URL is idempotent (upserts the document, replaces its chunks). A per-URL fetch/parse failure is reported as `"status": "error"` for that item — the whole request still returns `200`.

---

## Not supported

- **Zoning lookup by address** — needs NYC GIS/PLUTO address-to-district resolution, a different data domain than the ingested law text. No endpoint exists; don't fake one.
- **Comparing two revisions of a section over time** — needs historical snapshots this service doesn't retain. No endpoint exists.

---

## Errors

| status | meaning |
|---|---|
| `400` | bad request (e.g. `/ingest` batch exceeds `INGEST_MAX_URLS`) |
| `401` | missing/invalid `X-Ingest-Api-Key` on `/ingest` (only if `INGEST_API_KEY` is configured) |
| `404` | document/section not found |
| `429` | rate limit exceeded (`Retry-After` header included) |
| `500` | unhandled server error — logged server-side, response body is a generic `{"detail": "internal server error"}` (no stack traces leaked to clients) |

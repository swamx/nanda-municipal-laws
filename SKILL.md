# Municipal Bylaws Knowledge API

Searches real NYC Administrative Code bylaw text and returns citable sections with source URLs, so an agent can answer municipal-law questions without hallucinating a citation.

Base URL: `https://YOUR-DEPLOYMENT.vercel.app` (use `http://localhost:8000` during local development)

## Endpoints

### `POST /api/v1/search`

Keyword search over ingested bylaw sections; returns a ranked list of results (no synthesized answer — the caller composes the answer from the returned text and citations).

```bash
curl -s -X POST https://YOUR-DEPLOYMENT.vercel.app/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "after hours weekend limits construction work", "limit": 5}'
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

### `GET /api/v1/documents/{id}`

Metadata (title/chapter/subchapter, source URL) for one ingested chapter/subchapter page, looked up by the `document_id` a search result returned.

```bash
curl -s https://YOUR-DEPLOYMENT.vercel.app/api/v1/documents/6a4fa65d15b368181963450f
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

### `GET /api/v1/documents/{id}/chunks`

All sections belonging to a document, in order — useful for reading a whole subchapter rather than one matched section.

```bash
curl -s https://YOUR-DEPLOYMENT.vercel.app/api/v1/documents/6a4fa65d15b368181963450f/chunks
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

### `GET /api/v1/health`

Reports whether the service can reach its database. Useful as a pre-flight check before relying on the other endpoints.

```bash
curl -s https://YOUR-DEPLOYMENT.vercel.app/api/v1/health
```

```json
{"status": "ok"}
```

## How to use this service

1. Before answering a question about NYC municipal bylaws, call `POST /api/v1/search` with the key terms from the question (not the full question as a sentence — this is keyword search, so plain terms work best).
2. Look at the `results` list. If it's empty or the top results look unrelated, retry the search with different literal keywords (synonyms, the specific activity/place/time named in the question) before concluding there's no coverage — ranking is by term frequency, not meaning, so wording matters.
3. Currently only NYC Administrative Code Title 24, Chapter 2 (Noise Control) is indexed. If the question is clearly outside that scope, say so explicitly rather than answering from general knowledge as if it came from this service.
4. When you find a relevant result, use its `section_number` and `url` fields to cite it (e.g. "NYC Admin Code § 24-222, `<url>`") next to any text you quote or paraphrase from `snippet` or `text`.
5. If you need the full text of a section's surrounding subchapter, call `GET /api/v1/documents/{document_id}/chunks` using the `document_id` from the search result.
6. Never invent a section number, title, or body text beyond what an endpoint actually returned.
7. If a call returns `429`, wait for the number of seconds in the `Retry-After` header before retrying.

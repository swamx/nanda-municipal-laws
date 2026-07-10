# Municipal Law Skill for Autonomous Agents

Any autonomous agent can determine whether an action is legal in New York City by invoking this skill. It provides deterministic, citation-backed access to municipal law without using an LLM, so every answer is grounded in the official code — not "search → 14 PDFs, good luck." It returns precise, citable, structured facts — section text, metadata, cross-references, and mechanical match reasoning — for a question like "Can I keep chickens in Queens?"; it does **not** synthesize a legal answer for you (see "Composing your final answer" below for that split of responsibility).

Base URL: `https://nanda-municipal-laws.vercel.app`

## Endpoints

### `POST /api/v1/is_action_allowed`

The headline capability: ask whether a described action is legal in NYC. Deterministic — retrieval (keyword search for the closest-matching section) plus rules (keyword-based prohibition/permission classification of that section's text), **not** LLM reasoning. `allowed` is `true`/`false` only when an explicit statement was found; `null` ("unclear") when nothing relevant was found — it never guesses from silence.

```bash
curl -s -X POST https://nanda-municipal-laws.vercel.app/api/v1/is_action_allowed \
  -H "Content-Type: application/json" -d '{"action": "Keep backyard chickens"}'
```

```json
{
  "action": "Keep backyard chickens",
  "allowed": true,
  "conditions": [
    "(a) No person shall keep a live rooster, duck, goose or turkey in the City of New York except (1) in a slaughterhouse authorized by federal or state law... or (2) as authorized by §161.01 (a) of this Article.",
    "(c) Live rabbit and poultry markets. Live rabbits and poultry intended for sale shall not be kept on the same premises as a multiple dwelling..."
  ],
  "citations": [
    {"section_number": "161.19", "section_title": "Keeping of livestock, live poultry and rabbits", "url": "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf#page=16", "document_type": "NYC Health Code", "matched_text": "§161.19 Keeping of livestock, live poultry and rabbits. (a) No person shall keep a live rooster..."}
  ],
  "reasoning": "§161.19 is the closest-matching provision, but contains no explicit prohibition or permission statement matching keywords in the requested action - this is an absence-of-restriction inference, not an affirmative statement. Read the full section text before relying on it.",
  "confidence": "medium"
}
```

For a prohibited action (`{"action": "keep a rooster in my apartment"}`), the same shape returns `"allowed": false` and cites the actual prohibiting clause in `reasoning`. `confidence` for this example is `"medium"` against the full ingested corpus (not `"high"`) — with thousands of candidate sections in play, this specific query no longer has one decisively top-ranked result, even though the matched statement itself is unambiguous; always read `reasoning`, not just `confidence`, to judge how solid a result is. For an action with no relevant provision found at all, `"allowed": null`, `"citations": []`, `"confidence": "low"` — see Rules below for exactly what each `confidence` level means and a known limitation to watch for.

### `POST /api/v1/search`

Keyword search over ingested law sections. Optional filters: `title_num`, `chapter_num`, `document_type`, `agency`, `topic`. Returns ranked results plus a `reasoning` string explaining the match mechanically — never a legal conclusion.

```bash
curl -s -X POST https://nanda-municipal-laws.vercel.app/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "rooster keeping poultry", "document_type": "NYC Health Code"}'
```

```json
{
  "query": "rooster keeping poultry",
  "results": [
    {
      "document_id": "...",
      "section_number": "161.19",
      "section_title": "Keeping of livestock, live poultry and rabbits",
      "url": "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf#page=14",
      "score": 12.0,
      "snippet": "§161.19 Keeping of livestock, live poultry and rabbits. (a) No person shall keep a live rooster, duck, goose or turkey...",
      "document_type": "NYC Health Code",
      "agency": "Department of Health and Mental Hygiene (DOHMH)",
      "topic": "ANIMALS"
    }
  ],
  "count": 1,
  "reasoning": "matched query 'rooster keeping poultry' against 41 candidate chunk(s) after applying filters; ranked by term frequency, title weighted higher than body"
}
```

### `GET /api/v1/sections/{section_number}`

Exact lookup by section number (e.g. `161.19` or `24-222`) — full text, metadata, and a deterministic `structural_summary` (one bullet per lettered/numbered subsection, **not** an abstractive summary).

```bash
curl -s https://nanda-municipal-laws.vercel.app/api/v1/sections/161.19
```

```json
{
  "section_number": "161.19",
  "section_title": "Keeping of livestock, live poultry and rabbits",
  "text": "§161.19 Keeping of livestock, live poultry and rabbits. (a) No person shall keep a live rooster, duck, goose or turkey in the City of New York except (1) in a slaughterhouse authorized by federal or state law... (b) A person who is authorized... (c) Live rabbit and poultry markets...",
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
  "structural_summary": [
    "(a) No person shall keep a live rooster, duck, goose or turkey in the City of New York except...",
    "(b) A person who is authorized by applicable law to keep for sale or sell livestock, live rabbits or poultry shall keep the premises... clean and free of animal nuisances.",
    "(c) Live rabbit and poultry markets. Live rabbits and poultry intended for sale shall not be kept on the same premises as a multiple dwelling..."
  ],
  "chunk_count": 1,
  "reasoning": "exact lookup by section_number='161.19'; structural_summary derived by splitting text on sentence-bounded lettered/numbered subsection markers; no query scoring involved"
}
```

### `GET /api/v1/sections/{section_number}/related`

Resolves the section's `cross_references` into their own citations — a lightweight citation graph, one hop deep.

```bash
curl -s https://nanda-municipal-laws.vercel.app/api/v1/sections/161.19/related
```

```json
{
  "section_number": "161.19",
  "related": [
    {"section_number": "161.01", "section_title": "Wild and other animals prohibited", "url": "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf#page=1", "document_type": "NYC Health Code", "resolved": true}
  ],
  "reasoning": "extracted 1 cross-reference(s) from §161.19's body text via regex; 1 of 1 resolved against the ingested corpus"
}
```

A reference to a section outside the ingested corpus is still listed, with `"resolved": false` and null `url`/`section_title` — a gap is shown, never hidden.

### `POST /api/v1/penalties`

Filters to sections whose text was flagged as mentioning a penalty/fine/violation (a keyword heuristic, not legal certainty — see Rules below). Optional `query` and `topic`.

```bash
curl -s -X POST https://nanda-municipal-laws.vercel.app/api/v1/penalties \
  -H "Content-Type: application/json" -d '{"topic": "NOISE CONTROL"}'
```

```json
{"results": [{"section_number": "24-263", "section_title": "Civil penalties", "...": "..."}], "count": 1, "reasoning": "filtered to chunks flagged mentions_penalty=true; ..."}
```

### `POST /api/v1/permits`

Filters to sections flagged as mentioning a permit/license/authorization requirement. Optional `query` and `topic`.

```bash
curl -s -X POST https://nanda-municipal-laws.vercel.app/api/v1/permits \
  -H "Content-Type: application/json" -d '{"query": "keep certain animals"}'
```

```json
{"results": [{"section_number": "161.09", "section_title": "Permits to keep certain animals", "...": "..."}], "count": 1, "reasoning": "filtered to chunks flagged mentions_permit=true; ..."}
```

### `GET /api/v1/documents/{id}`

Metadata for one ingested source document (an admin-code chapter/subchapter page or a health-code article), by the `document_id` a search result returned.

```bash
curl -s https://nanda-municipal-laws.vercel.app/api/v1/documents/6a4fa65d15b368181963450f
```

### `GET /api/v1/documents/{id}/chunks`

All sections belonging to a document, in order.

```bash
curl -s https://nanda-municipal-laws.vercel.app/api/v1/documents/6a4fa65d15b368181963450f/chunks
```

### `GET /api/v1/health`

Reports whether the service can reach its database.

```bash
curl -s https://nanda-municipal-laws.vercel.app/api/v1/health
```

```json
{"status": "ok"}
```

## Not currently supported

- **Zoning lookup by address** (`find_zoning`) — needs NYC GIS/PLUTO address-to-district resolution, a different data domain than the ingested law text. Don't guess at coverage; say this isn't supported if asked.
- **Comparing two revisions of a section over time** (`compare_versions`) — needs historical snapshots this service doesn't retain. Don't invent a "what changed" answer.

## Composing your final answer

This API deliberately returns citations and mechanical `reasoning`, never a finished legal answer, so **you** (the calling agent) compose the final response, in exactly this shape:

```json
{
  "answer": "...",
  "sources": [{"section": "161.19", "url": "https://.../health-code-article161.pdf#page=14", "score": 12.0}],
  "reasoning": "Derived from ..."
}
```

Confidence isn't returned by the API — compute it yourself from what you got back:
- **High**: an exact `/sections/{id}` lookup, or a `/search` top result with a clearly higher score than the rest.
- **Medium**: a `/search` result that matched on keywords only, with several close-scoring results.
- **Low**: an empty `results`/`related` list, or only weakly-scored/off-topic matches.

## Rules

1. **Never state a fact or number that isn't literally present in the returned `text`.** A real, cautionary example: it's popular internet folklore that NYC limits backyard chickens to "a maximum of 6 hens" — the real text of §161.19 states no such number. It only prohibits keeping a live rooster, duck, goose, or turkey outside specific exceptions, and says nothing restricting hens. If you (or the user) assume a number, verify it against the returned `text` before repeating it — if it's not there, don't say it.
2. **Always cite `section_number` and `url`** next to anything you quote or paraphrase.
3. **This is keyword search, not semantic search.** Term frequency drives `/search` ranking, not phrase meaning — retry with different literal keywords before concluding there's no coverage.
4. **`mentions_penalty`/`mentions_permit` are heuristics** (keyword-based), not a legal determination that a penalty or permit requirement definitely does or doesn't apply — read the actual `text` before asserting either way.
5. **If results are empty, say so.** Don't answer from general knowledge as if it came from this service.
6. **Scope**: the entire NYC Administrative Code (all titles) and the entire NYC Health Code (all articles) are ingested — see [docs/COVERAGE.md](./docs/COVERAGE.md) in the source repo for the exact live manifest. If a search genuinely returns nothing, say so; don't assume it's a coverage gap before retrying with different literal keywords.
7. **`is_action_allowed`'s `allowed` field can be `true`, `false`, or `null`.** `null` means no relevant provision was found — never treat it as "probably fine." `true` from an absence-of-restriction inference (no explicit prohibition found, `confidence: "medium"`) is a materially weaker claim than `true` from an explicit permission statement (`confidence: "high"`) — the `reasoning` field tells you which one you got. Because this tool ranks by shared keywords, a query overlapping an unrelated section on just one common word (e.g. "party" as in "a party to an action," or "roof" as a building material vs. a rooftop location) can surface an off-topic citation — always read `reasoning` and the cited text yourself before repeating the verdict; don't repeat `allowed` to a user as a legal conclusion without that check.

## How to use this service

1. If the question is a yes/no legality check on a described action ("can I...", "is it legal to...", "am I allowed to..."), call `POST /api/v1/is_action_allowed` with that action described in plain terms first — it's purpose-built for exactly this and does the search + rule evaluation for you.
2. Otherwise, pull the key terms (not the full sentence) from the user's question and call `POST /api/v1/search`, optionally filtered by `document_type`/`topic`/`agency` if you can infer them.
3. If a result's `section_number` looks like the authoritative answer, call `GET /api/v1/sections/{section_number}` for its full text and `structural_summary`.
4. If you need related context, call `GET /api/v1/sections/{section_number}/related`.
5. If the question is specifically about penalties or permit requirements (not a yes/no legality check), call `POST /api/v1/penalties` or `POST /api/v1/permits` instead of a general search.
6. If `/search` or `/is_action_allowed` returns nothing relevant, retry with different literal keywords before concluding there's no coverage.
7. Compose your final answer in the `{answer, sources, reasoning}` shape above, following every rule in the Rules section — especially never inventing a number or fact absent from the returned `text`, and never repeating `is_action_allowed`'s `allowed` field as a legal conclusion without reading its `reasoning` first.
8. If a call returns `429`, wait for the number of seconds in the `Retry-After` header before retrying.

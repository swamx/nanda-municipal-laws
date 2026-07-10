# Postman collection

Infra/integration test suite for the Municipal Law Skill API, targeting the live Vercel deployment by default. Assertions are grounded in real, verified behavior against the full ingested corpus (see `tests/` and `docs/DATA_SOURCE.md`), not invented expected values — every "Success Test" and "Fail Test" in this collection was run against the live deployment while writing it, not just eyeballed.

## Conventions

- **One folder per API (endpoint).** Folder names are numbered in a sensible run order (`1. Service Info` through `8. Rate Limiting`).
- **Every request name ends in `Success Test` or `Fail Test`.** A "Success Test" validates the documented, correct behavior for a given input (which sometimes *is* a 4xx — e.g. a validation failure is the correct, successful outcome of sending a bad request). A "Fail Test" is specifically a request designed to be rejected (missing required fields, out-of-range values, missing auth), asserting the rejection is clean (right status code, no 500, no silent success).
- **`_test_note` fields document intent inside the request body itself.** Every POST request's JSON body carries an extra `"_test_note"` field explaining what that specific case is checking and why. This is not a real API field — every request model in `app/models.py` uses pydantic's default `extra="ignore"`, so the server silently drops it and it never affects the actual request/response being tested. GET requests (which have no body) carry the equivalent note in the request's own `description` field instead.
- **Known-limitation tests are intentional, not bugs.** A few requests (e.g. the "roof" and "flame/flaming" homonym-keyword cases in folder 2) deliberately exercise a documented, accepted limitation of keyword-based matching (see `docs/DATA_SOURCE.md`). These assert the response is well-formed and never fabricates a citation — not that the legal determination is topically correct. If one of these starts failing, that most likely means the underlying keyword-matching or corpus content changed, worth a deliberate look rather than a quick "fix the test" patch.

## Files

- `Municipal-Law-Skill.postman_collection.json` — the collection (v2.1 schema):
  1. **Service Info** — `/`, `/skill.md`, `/api/v1/health`, `/api/v1/version`
  2. **is_action_allowed** — the two flagship pitch examples (chickens allowed with rooster caveat, at `confidence: medium` against the full corpus; rooster keeping prohibited, at `confidence: medium` too — see the note below on why this isn't `high`), a genuinely-no-match case (using invented, non-English tokens - see note below), two documented keyword-collision limitation cases ("roof", "flame/flaming"), and two request-validation Fail Tests
  3. **Search** — both `search_mode` values, filtered and unfiltered, plus validation Fail Tests
  4. **Sections** — exact lookup, related-laws resolution, 404 handling for both, and the search term map (highlighted occurrences, zero-match term omission, 404/422 handling)
  5. **Topic Filters** — `/penalties`, `/permits`, plus validation Fail Tests
  6. **Documents** — chained from a Search response's `document_id` via a collection variable, plus 404 Fail Tests for a well-formed-but-nonexistent id and a malformed id
  7. **Ingest** — **manual/optional**, not meant for automated runs (see below)
  8. **Rate Limiting** — **manual/optional** stress test, not meant for automated runs (see below)
- `environments/Vercel.postman_environment.json` — `base_url` = the production Vercel URL (this is also the collection's own default, so the environment is optional but explicit).
- `environments/Local.postman_environment.json` — `base_url` = `http://localhost:8000`, for testing against `uvicorn app.main:app --reload` locally.

## Running in the Postman GUI

1. Import `Municipal-Law-Skill.postman_collection.json` (File → Import).
2. Import both files in `environments/` and select one from the environment dropdown (top right). This is optional — the collection's own `base_url` variable already defaults to the live Vercel URL.
3. Run folders 1–6 individually, or select the collection and folders 1–6 in the Collection Runner, **with a delay between requests** (Collection Runner has a "Delay" field — set it to at least 500ms locally, or several seconds against the live Vercel deployment; see the rate-limit note below). **Do not include folders 7 and 8 in a routine "run everything"** — see the warnings below.

## Running with Newman (CLI)

```bash
npm i -g newman
newman run postman/Municipal-Law-Skill.postman_collection.json \
  --folder "1. Service Info" \
  --folder "2. is_action_allowed" \
  --folder "3. Search" \
  --folder "4. Sections" \
  --folder "5. Topic Filters" \
  --folder "6. Documents (chained from Search)" \
  --delay-request 6500
```

Add `-e postman/environments/Local.postman_environment.json` to point at a local server instead of production (and drop `--delay-request`, since the local dev server has no rate limiting concerns worth pacing around).

Folder 6 depends on folder 3 having run first in the same collection run, since it reads the `document_id` collection variable that folder 3's test script sets. Run the folders in order (as listed above) rather than in isolation if you want folder 6 to pass.

## Why `--delay-request` matters against the live deployment

The production API rate-limits general (non-ingest) endpoints to `RATE_LIMIT_PER_MINUTE` (10) requests/minute per client IP, in a **fixed 60-second calendar window**, not a rolling one (see `app/rate_limit.py`). Folders 1–6 together fire ~28 requests. Newman with no delay fires them in well under a second, which blows through the 10/minute budget almost immediately and produces a cascade of spurious `429`s that look like test failures but aren't — they're the rate limiter correctly doing its job against an unrealistic burst of traffic. Pacing requests with `--delay-request 6500` (or more) keeps each 60-second window under budget. This was discovered empirically while writing this suite — the very first full run produced dozens of 429-shaped "failures" before the delay was added.

## Why folders 7 and 8 are excluded from normal runs

- **Folder 7 (Ingest)** calls `POST /api/v1/ingest`, which triggers a real outbound fetch and a real Atlas write, and shares the service's general rate-limit budget as well as its own stricter 1 req/min ingest-specific bucket. Its two "Fail Test" requests (no API key, empty `urls`) are always safe to run since they're rejected before any real ingestion happens. Its one "Success Test" request (re-ingesting a known-good Health Code article) only succeeds if you've filled in the `ingest_api_key` collection variable with the real `INGEST_API_KEY` value locally (this variable ships blank on purpose — **never commit a real key value into this file**); otherwise it correctly gets `401`, which the test tolerates rather than treats as a failure.
- **Folder 8 (Rate Limiting)** deliberately self-loops 11 times against `/api/v1/version` via `postman.setNextRequest()` to prove the 10 req/min limit and `Retry-After` header work, which **consumes the same rate-limit budget** every other folder relies on. Run it by itself (select just that folder in the Collection Runner) when you specifically want to verify rate limiting, not as part of a broader pass — otherwise you'll see spurious 429s in folders 1–6 for the rest of that minute.

## A confidence-level result that looks surprising but is verified correct

The "keep a rooster in my apartment" test in folder 2 asserts `confidence: "medium"`, not `"high"`, even though the underlying prohibition is an explicit, unambiguous statement. This was surprising enough while writing this suite that it was checked twice directly against production before trusting it: with the full ~10,700-chunk corpus, this query no longer has one decisively top-ranked candidate section the way it did against a small test fixture, so `_relative_confidence()` (see `app/action_evaluator.py`) caps it at `medium`. `SKILL.md` has been corrected to match this real, current behavior.

# Postman collection

Infra/integration test suite for the Municipal Law Skill API, targeting the live Vercel deployment by default. Assertions are grounded in real, verified behavior against the full ingested corpus (see the session's own testing in `tests/` and `docs/DATA_SOURCE.md`), not invented expected values.

## Files

- `Municipal-Law-Skill.postman_collection.json` — the collection (v2.1 schema), organized into folders:
  1. Service Info — `/`, `/skill.md`, `/api/v1/health`, `/api/v1/version`
  2. is_action_allowed — the headline capability, including the two flagship pitch examples (chickens allowed with rooster caveat; rooster prohibited) and the documented "unclear"/homonym-limitation cases
  3. Search — both `search_mode` values, filtered and unfiltered
  4. Sections — exact lookup, related-laws resolution, 404 handling
  5. Topic Filters — `/penalties`, `/permits`
  6. Documents — chained from a Search response's `document_id` via a collection variable
  7. Ingest — **manual/optional**, not meant for automated runs (see below)
  8. Rate Limiting — **manual/optional** stress test, not meant for automated runs (see below)
- `environments/Vercel.postman_environment.json` — `base_url` = the production Vercel URL (this is also the collection's own default, so the environment is optional but explicit).
- `environments/Local.postman_environment.json` — `base_url` = `http://localhost:8000`, for testing against `uvicorn app.main:app --reload` locally.

## Running in the Postman GUI

1. Import `Municipal-Law-Skill.postman_collection.json` (File → Import).
2. Import both files in `environments/` and select one from the environment dropdown (top right). This is optional — the collection's own `base_url` variable already defaults to the live Vercel URL.
3. Run folders 1–6 individually, or select the collection and folders 1–6 in the Collection Runner. **Do not include folders 7 and 8 in a routine "run everything"** — see the warnings below.

## Running with Newman (CLI)

```
npm i -g newman
newman run postman/Municipal-Law-Skill.postman_collection.json \
  --folder "1. Service Info" \
  --folder "2. is_action_allowed (headline capability)" \
  --folder "3. Search" \
  --folder "4. Sections" \
  --folder "5. Topic Filters" \
  --folder "6. Documents (chained from Search)"
```

Add `-e postman/environments/Local.postman_environment.json` to point at a local server instead of production.

Folder 6 depends on folder 3 having run first in the same collection run, since it reads the `document_id` collection variable that folder 3's test script sets. Run the folders in order (as listed above) rather than in isolation if you want folder 6 to pass.

## Why folders 7 and 8 are excluded from normal runs

- **Folder 7 (Ingest)** calls `POST /api/v1/ingest`, which triggers a real outbound fetch and a real Atlas write, and shares the service's general rate-limit budget as well as its own stricter 1 req/min ingest-specific bucket. Running it as part of routine testing pollutes that budget for no reason (the request is idempotent and safe to run, but there's no reason to run it every time).
- **Folder 8 (Rate Limiting)** deliberately self-loops 11 times against `/api/v1/health` via `postman.setNextRequest()` to prove the 10 req/min limit and `Retry-After` header work, which **consumes the same rate-limit budget** every other folder relies on. Run it by itself (select just that folder in the Collection Runner) when you specifically want to verify rate limiting, not as part of a broader pass — otherwise you'll see spurious 429s in folders 1–6 for the rest of that minute.

## Known-limitation tests are intentional, not bugs

Folder 2 includes a request named `KNOWN LIMITATION - homonym keyword can select an irrelevant section`. This pins documented, accepted behavior (see `docs/DATA_SOURCE.md`'s "Known limitation: `is_action_allowed` can select an irrelevant section on a coincidental keyword match" section) — it only asserts the response is well-formed and never fabricates a citation, not that the legal determination is topically correct. If this request ever starts failing its assertions, that most likely means the underlying keyword-matching behavior changed, which is worth a deliberate look, not a quick "fix the test" patch.

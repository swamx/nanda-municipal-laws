---
name: municipal-bylaws
description: Search NYC Administrative Code bylaws (e.g. noise, construction hours, sound level restrictions) and retrieve citable section text with source URLs. Use when a user asks about NYC municipal law or regulations.
---

# Municipal Bylaws Skill

Searches a Knowledge API backed by real NYC Administrative Code text and returns citable results — it does not synthesize an answer for you. Use the returned sections to compose your own answer.

## Scope

Currently indexed: **NYC Administrative Code Title 24, Chapter 2 (Noise Control)** only — short title/definitions, general provisions, prohibited noise, construction noise management, sound level standards, plainly-audible noise sources, certificates/permits, and enforcement. Do not imply broader coverage of the NYC Administrative Code than this; if a question falls outside noise control, say the skill's index doesn't cover it rather than guessing.

## How to invoke

```
python scripts/query_bylaws.py "<question or keywords>" [--limit N] [--title 24] [--chapter 2]
```

Set the `API_BASE_URL` environment variable to the deployed API's base URL (e.g. `https://your-deployment.vercel.app`) before running. The script prints a JSON object to stdout:

```json
{
  "query": "...",
  "results": [
    {"document_id": "...", "section_number": "24-222", "section_title": "...", "url": "https://...#section-24-222", "score": 3.1, "snippet": "..."}
  ],
  "count": 1
}
```

## Rules for using results

1. **Always cite the `url` field verbatim** next to any section text you quote or paraphrase. Prefer a citation format like "NYC Admin Code § 24-222" using `section_number`, not an invented format.
2. **This is keyword search, not semantic search.** Term frequency drives ranking, not phrase meaning — a query using different words than the target section's actual text may return weak or misleading results. If the top result doesn't look relevant, retry with different literal keywords (synonyms, the specific activity/place/time named in the question) before concluding there's no coverage.
3. **Never fabricate section numbers, section titles, or body text** beyond what the API actually returned. If `results` is empty, say the bylaws index doesn't have a matching section — don't guess at a plausible-sounding code section.
4. If the user's question is outside NYC Admin Code Title 24 Chapter 2 (noise), say so explicitly rather than answering from general knowledge as if it came from this skill's index.

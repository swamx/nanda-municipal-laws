---
name: municipal-bylaws
description: Search NYC municipal law (Administrative Code noise control, Health Code animal-keeping rules) and retrieve citable section text, metadata, and cross-references. Use when a user asks about NYC municipal law or regulations.
---

# Municipal Bylaws Skill

Calls the Municipal Legal Intelligence Service — a Knowledge API backed by real NYC municipal law text — and returns citable, structured results plus mechanical match `reasoning`. It does not synthesize a legal answer for you; use the returned sections to compose your own.

## Scope

Currently indexed:
- **NYC Administrative Code Title 24, Chapter 2 (Noise Control)** — short title/definitions, general provisions, prohibited noise, construction noise management, sound level standards, plainly-audible noise sources, certificates/permits, enforcement.
- **NYC Health Code Article 161 (Animals)** — wild/exotic animal restrictions, dog licensing/control, permits to keep certain animals, and §161.19 (keeping of livestock, live poultry and rabbits).

Do not imply broader coverage than this. If a question falls outside these two areas, say the skill's index doesn't cover it rather than guessing.

## How to invoke

```
python scripts/query_bylaws.py "<question or keywords>" [--limit N] [--title 24] [--chapter 2]
```

Set the `API_BASE_URL` environment variable to the deployed API's base URL (e.g. `https://nanda-municipal-laws.vercel.app`) before running. This script only exercises the `/search` endpoint; for section lookups, related-law resolution, or penalty/permit filtering, call the API directly per the root `SKILL.md`'s endpoint reference. The script prints a JSON object to stdout:

```json
{
  "query": "...",
  "results": [
    {"document_id": "...", "section_number": "161.19", "section_title": "...", "url": "https://...healthcode/health-code-article161.pdf#page=14", "score": 3.1, "snippet": "...", "document_type": "NYC Health Code", "agency": "Department of Health and Mental Hygiene (DOHMH)", "topic": "ANIMALS"}
  ],
  "count": 1,
  "reasoning": "matched query '...' against N candidate chunk(s) after applying filters; ranked by term frequency, title weighted higher than body"
}
```

## Rules for using results

1. **Always cite the `url` field verbatim** next to any section text you quote or paraphrase. Prefer a citation format like "NYC Admin Code § 24-222" or "NYC Health Code §161.19" using `section_number`, not an invented format.
2. **Never state a fact or number that isn't literally present in the returned text.** A real, cautionary example: it's popular internet folklore that NYC caps backyard chickens at "a maximum of 6 hens" — the real text of §161.19 states no such number; it only prohibits keeping a live rooster, duck, goose, or turkey outside specific exceptions. If a number or fact isn't in the returned `text`/`snippet`, don't repeat it.
3. **This is keyword search, not semantic search.** Term frequency drives ranking (the `reasoning` field explains the match mechanically), not phrase meaning — a query using different words than the target section's actual text may return weak or misleading results. If the top result doesn't look relevant, retry with different literal keywords before concluding there's no coverage.
4. **Never fabricate section numbers, section titles, or body text** beyond what the API actually returned. If `results` is empty, say the index doesn't have a matching section — don't guess at a plausible-sounding code section.
5. If the user's question is outside the two areas listed under Scope, say so explicitly rather than answering from general knowledge as if it came from this skill's index.

# Pitch deck content (editable review copy)

One section per slide, grouped below. Edit this file freely to review/comment - when you're happy with changes, port them back into `content.py` (the real source of truth both `build_pptx.py` and `build_html.py` render from) and regenerate.

## Hook & positioning

### Slide 1/16 — Municipal Law Skill

*kind: `title`*

**Municipal Law Skill for Autonomous Agents**

*Deterministic, citation-backed municipal law retrieval — no LLM in the loop*

NANDA Town · MIT Reality Hackathon 2026  
https://nanda-municipal-laws.vercel.app

### Slide 2/16 — AI agents hallucinate municipal law

*kind: `bullets`*

- Popular internet myth: “NYC caps backyard chickens at 6 hens”
- The real statute (§161.19) states no such number — it only prohibits roosters, ducks, geese, and turkeys, with narrow exceptions
- Agents relying on an LLM's training data repeat exactly this kind of confident, wrong answer
- Legal citations need to come from the actual code — not a model's memory

### Slide 3/16 — The capability

*kind: `quote`*

> A deterministic municipal law skill that any AI agent can invoke to obtain grounded, citation-backed legal evidence from the complete NYC Administrative and Health Codes.

- No LLM calls, ever — nothing for the service itself to hallucinate
- Same query → same citations → same ordering, every time
- The calling agent performs the reasoning; this service only supplies evidence

### Slide 4/16 — Architecture

*kind: `diagram`*

Official NYC sources (nyc.gov, nycadmincode.readthedocs.io) → Crawler → Normalization → MongoDB → FastAPI → AI Agent

*The service never generates legal advice — only official text and citations.*

### Slide 5/16 — The complete corpus, not a sample

*kind: `stats`*

- **NYC Administrative Code**: 32 Titles · 4,781 Sections
- **NYC Health Code**: 36 Articles · 501 Sections

*668 source documents · 10,702 searchable chunks total*

---

## API reference

### Slide 6/16 — Agent-facing APIs — Legal Determination & Search

*kind: `api_table`*

| Method | Endpoint | Use case |
|---|---|---|
| POST | `/is_action_allowed` | Headline capability — yes/no legality check on a described action. Returns allowed, conditions, citations, reasoning, confidence. |
| POST | `/search` | General keyword lookup across the entire corpus — filterable by title, chapter, document_type, agency, or topic. |
| POST | `/sections/{id}/term_map` | Highlight exactly where search terms occur within a section — built for search-results/demo UI rendering. |

### Slide 7/16 — Agent-facing APIs — Lookup & Cross References

*kind: `api_table`*

| Method | Endpoint | Use case |
|---|---|---|
| GET | `/sections/{id}` | Exact section retrieval by number — full untruncated text plus a deterministic structural summary. |
| GET | `/sections/{id}/related` | Resolve a section's own cross-references into their citations — a one-hop citation graph. |
| GET | `/documents/{id}` | Metadata for a source document (an Admin Code chapter or Health Code article). |
| GET | `/documents/{id}/chunks` | Every section belonging to one document, in order. |

### Slide 8/16 — Agent-facing APIs — Penalties & Permits

*kind: `api_table`*

| Method | Endpoint | Use case |
|---|---|---|
| POST | `/penalties` | Find sections flagged as mentioning a penalty or fine — for enforcement-related questions. |
| POST | `/permits` | Find sections flagged as requiring a permit or license. |

### Slide 9/16 — Administration & operational endpoints

*kind: `api_table`*

*Kept separate from the agent-facing retrieval surface above — not part of the reasoning loop*

| Method | Endpoint | Use case |
|---|---|---|
| GET | `/health` | Liveness check — reports MongoDB reachability. |
| GET | `/version` | Deployed app version, plus corpus freshness: last-ingested date and age in days. |
| GET | `/pubkey` | Ed25519 public key for verifying a signed response's provenance offline. |
| POST | `/ingest` | Fetch, parse, and persist new source documents. Operational only, API-key gated — not for agent use. |

---

## Stories

### Slide 10/16 — Story 1 — A resident

*kind: `story`*

**Question:** “Can I keep backyard chickens?”

1. Agent calls POST /is_action_allowed
2. allowed: true (confidence: medium) — citing §161.19
3. Agent answers: “Yes, but roosters are prohibited citywide”

### Slide 11/16 — Story 2 — A food vendor

*kind: `story`*

**Question:** “What permit do I need to operate a mobile food cart?”

1. Agent calls POST /permits {"query": "mobile food vending unit license permit"}
2. Top result: §89.11 “Applications for permits and licenses” (Mobile Food Vending)
3. Agent answers: “You need a vending permit/license under §89.11 — fees are set by §17-308”

### Slide 12/16 — Story 3 — A building owner

*kind: `story`*

**Question:** “What's the penalty if I dump construction debris illegally?”

1. Agent calls POST /penalties → GET /sections/16-119
2. §16-119 “Dumping prohibited” — misdemeanor, $1,500–$10,000 civil penalty, vehicle impoundment
3. Agent answers with real dollar figures, straight from the statute

---

## Engineering & trust

### Slide 13/16 — Engineering: bugs found and fixed, not just claimed

*kind: `bullets`*

- Naive substring search: “fine” matched inside “defined” — fixed with word-boundary matching everywhere
- 36 Health Code PDFs, each formatted slightly differently — parser normalized and verified section-by-section against real text
- The “6 hens” myth — a regression test locks in the true statute text, forever

### Slide 14/16 — Trust & verification

*kind: `bullets`*

- Every /is_action_allowed and /search response is Ed25519-signed
- /pubkey lets any downstream agent verify offline that this service — not a relay or a cache — produced a citation
- /version reports corpus freshness — law goes stale, and callers can know exactly how stale
- Same query → same citations → same ordering — no randomness, ever

---

## Close

### Slide 15/16 — Why NANDA

*kind: `quote`*

> This skill lets any autonomous agent in NANDA Town answer municipal-law questions using authoritative legal sources — instead of relying on an LLM's memory.

- Composable by design — the last hop in a chain started by another skill (a 311 complaint, a permit application, a code-enforcement lead)
- Any agent that can call an HTTP endpoint can invoke it, per SKILL.md

### Slide 16/16 — Agent-ready. Deterministic. Citation-backed.

*kind: `closing`*

- 4,781 NYC Administrative Code sections
- 501 NYC Health Code sections
- No hallucinations — grounded by citations, every time

**https://nanda-municipal-laws.vercel.app**  
https://github.com/swamx/nanda-municipal-laws

---

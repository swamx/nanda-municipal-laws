# Pitch deck content (editable review copy)

One section per slide, grouped below. Edit this file freely to review/comment - when you're happy with changes, port them back into `content.py` (the real source of truth both `build_pptx.py` and `build_html.py` render from) and regenerate.

## Hook & positioning

### Slide 1/14 — Municipal Law Skill

*kind: `title`*

**Municipal Law Skill for Autonomous Agents**

*An agent-ready municipal law skill providing deterministic, citation-backed legal evidence.*

NANDA Town · MIT Reality Hackathon 2026  
https://nanda-municipal-laws.vercel.app

### Slide 2/14 — AI agents hallucinate municipal law

*kind: `myth`*

❌ **Internet folklore**: “You may keep up to six hens.”

✅ **NYC Health Code §161.19 (the real statute)**: No such limit exists. Only certain birds (roosters, ducks, geese, turkeys) are prohibited — with narrow exceptions. Nothing restricts hens at all.

*Agents relying on an LLM's training data repeat exactly this kind of confident, wrong answer. Legal citations need to come from the actual code — not a model's memory.*

### Slide 3/14 — The capability

*kind: `quote`*

> A deterministic municipal law skill that any AI agent can invoke to obtain grounded, citation-backed legal evidence from the complete NYC Administrative and Health Codes.

- No LLM calls, ever — nothing for the service itself to hallucinate
- Same query → same citations → same ordering, every time

**The service never generates answers. It only returns legal evidence.**

---

## Stories

### Slide 4/14 — Story 1 — A resident

*kind: `story`*

**Question:** “Can I keep backyard chickens?”

1. User asks the agent a plain-language question
2. Agent calls POST /is_action_allowed
3. Evidence returned: allowed:true (confidence: medium)
4. Agent answers: “Yes, but roosters are prohibited citywide”

**Returned citation: NYC Health Code §161.19**

### Slide 5/14 — Story 2 — A food vendor

*kind: `story`*

**Question:** “What permit do I need to operate a mobile food cart?”

1. User asks the agent a plain-language question
2. Agent calls POST /permits {"query": "mobile food vending unit license permit"}
3. Evidence returned: §89.11 “Applications for permits and licenses”
4. Agent answers: “You need a vending permit/license under §89.11 — fees are set by §17-308”

**Returned citation: NYC Health Code §89.11**

### Slide 6/14 — Story 3 — A building owner

*kind: `story`*

**Question:** “What's the penalty if I dump construction debris illegally?”

1. User asks the agent a plain-language question
2. Agent calls POST /penalties → GET /sections/16-119
3. Evidence returned: §16-119 “Dumping prohibited” — misdemeanor, vehicle impoundment
4. Agent answers with real dollar figures, straight from the statute

**Returned directly from statute: $1,500 – $10,000 civil penalty**

---

## Architecture & scale

### Slide 7/14 — Architecture

*kind: `diagram`*

Official NYC sources → Crawler → Normalization → MongoDB → FastAPI Skill → Autonomous Agent → Grounded Answer

*The service never generates legal advice — only official text and citations. The last step is why it exists.*

### Slide 8/14 — The complete corpus, not a sample

*kind: `stats`*

- **Entire NYC Administrative Code**: 32 Titles · 4,781 Sections
- **Entire NYC Health Code**: 36 Articles · 501 Sections

*668 source documents · 10,702 searchable chunks · ≈55 MB total*

---

## Engineering & why not an LLM

### Slide 9/14 — Engineering: bugs found and fixed, not just claimed

*kind: `bullets`*

- Naive substring search: “fine” matched inside “defined” — fixed with word-boundary matching everywhere
- 36 Health Code PDFs, each formatted slightly differently — parser normalized and verified section-by-section against real text
- The “6 hens” myth — a regression test locks in the true statute text, forever
- Hidden ingestion size limit silently truncated requests — found and fixed before it silently dropped data

### Slide 10/14 — Why not just ask an LLM?

*kind: `comparison`*

**LLM memory**
- ✗ May hallucinate
- ✗ May be outdated
- ✗ No provenance

**Municipal Law Skill**
- ✓ Official source
- ✓ Deterministic
- ✓ Citations
- ✓ Verifiable

---

## API reference & trust

### Slide 11/14 — Agent-facing capabilities

*kind: `capability_table`*

| Capability | Endpoint | Returns |
|---|---|---|
| Determine legality | `/is_action_allowed` | Allowed, conditions, citations, confidence |
| Search law | `/search` | Ranked legal evidence, filterable by source |
| Retrieve statute | `/sections/{id}` | Official, untruncated text |
| Find penalties | `/penalties` | Enforcement provisions |
| Find permits | `/permits` | Permit/license requirements |

*Also available, kept separate from the agent-facing surface above: /health, /version, /pubkey, /ingest — operational only, not part of the reasoning loop.*

### Slide 12/14 — Trust & verification

*kind: `diagram`*

Signed → Verifiable → Deterministic → Replayable

*Every /is_action_allowed and /search response is Ed25519-signed — /pubkey lets any downstream agent verify offline that this service, not a relay or a cache, produced a citation. /version reports corpus freshness, so callers know exactly how stale the law is.*

---

## Close

### Slide 13/14 — Why NANDA

*kind: `quote`*

> This transforms municipal law from static documents into a reusable capability that any NANDA agent can invoke.

- Composable by design — the last hop in a chain started by another skill (a 311 complaint, a permit application, a code-enforcement lead)
- Any agent that can call an HTTP endpoint can invoke it, per SKILL.md

### Slide 14/14 — Agent-ready. Deterministic. Citation-backed.

*kind: `closing`*

- Complete NYC corpus
- No hallucinations
- Live today

**https://nanda-municipal-laws.vercel.app**  
https://github.com/swamx/nanda-municipal-laws

---

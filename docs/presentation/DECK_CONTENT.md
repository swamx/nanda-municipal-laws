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

- **Traditional RAG**: Question → LLM → Answer
- **Municipal Law Skill**: Question → Skill → Official Evidence → Agent → Grounded Answer


**The service never generates answers. It only returns legal evidence.**

---

## Stories

### Slide 4/14 — Story 1 — A resident

*kind: `story`*

**Question:** “Can I keep backyard chickens?”

Resident → Agent → POST /is_action_allowed → **NYC Health Code §161.19**

*“Yes, but roosters are prohibited citywide”*

### Slide 5/14 — Story 2 — A food vendor

*kind: `story`*

**Question:** “What permit do I need to operate a mobile food cart?”

Food vendor → Agent → POST /permits → **§89.11 Applications for permits and licenses**

*“You need a vending permit/license under §89.11 — fees are set by §17-308”*

### Slide 6/14 — Story 3 — A building owner

*kind: `story`*

**Question:** “What's the penalty if I dump construction debris illegally?”

Building owner → Agent → POST /penalties → GET /sections/16-119 → **$1,500 – $10,000 civil penalty**

*Real dollar figures, straight from the statute — not a vague “consult a lawyer.”*

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

**Not a curated demo dataset.**

---

## Engineering & why not an LLM

### Slide 9/14 — Production issues discovered using live municipal data

*kind: `bullets`*

- Naive substring search: “fine” matched inside “defined” — fixed with word-boundary matching everywhere
- 36 Health Code PDFs, each formatted slightly differently — parser normalized and verified section-by-section against real text
- The “6 hens” myth — a regression test locks in the true statute text, forever
- Hidden ingestion size limit silently truncated requests — found and fixed before it silently dropped data

### Slide 10/14 — Why not just ask an LLM?

*kind: `comparison`*

**LLM memory**
- ✗ May be incomplete
- ✗ May be outdated
- ✗ Cannot prove provenance

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

**Every response is cryptographically signed (Ed25519).**

Signed → Verifiable → Deterministic → Replayable

*/pubkey lets any downstream agent verify offline that this service, not a relay or a cache, produced a citation. /version reports corpus freshness, so callers know exactly how stale the law is.*

---

## Close

### Slide 13/14 — Why NANDA

*kind: `quote`*

> This transforms municipal law from static documents into a reusable capability that any NANDA agent can invoke.

- Composable by design — the last hop in a chain started by another skill (a 311 complaint, a permit application, a code-enforcement lead)
- Any agent that can call an HTTP endpoint can invoke it, per SKILL.md

**Any agent. Any language. Any framework. Just HTTP.**

### Slide 14/14 — Agent-ready. Deterministic. Citation-backed.

*kind: `closing`*

- ✓ Complete NYC Administrative & Health Codes
- ✓ Deterministic, citation-backed legal evidence
- ✓ Live, agent-ready HTTP skill

**https://nanda-municipal-laws.vercel.app**  
https://github.com/swamx/nanda-municipal-laws

---

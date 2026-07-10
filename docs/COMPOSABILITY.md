# Composing with other NANDA Town skills

This service is a citation source, not a dead end — it's designed to be the last hop in a chain started by some *other* skill that surfaces a real-world civic event (a 311 complaint, a permit application, a code-enforcement lead) but has no legal grounding of its own to attach to it.

## The pattern

```
Some other skill                 Municipal Law Skill                 Composing agent
(civic data / complaints)  ───►  /search, /penalties, /permits  ───►  cites + verifies
    topic/keyword                or /is_action_allowed                 both signatures
```

1. An upstream skill returns a real-world record with a topic or plain-language description (e.g. a 311-style complaint: `{"category": "Noise - Residential", "borough": "Queens"}`).
2. The composing agent maps that to a query against this skill — `topic: "NOISE CONTROL"` for `/penalties` or `/permits`, or the plain description for `/is_action_allowed` — and gets back real citations, never a fabricated legal conclusion.
3. If the upstream skill also signs its output (as this one does — see [PROVENANCE.md](./PROVENANCE.md)), the composing agent can verify *both* signatures independently, producing an end-to-end verifiable chain: "this civic event is real (signed by skill A) and this is the law that governs it (signed by skill B)" — without either skill trusting the other, only the composing agent verifying both.

## Worked example: enriching a noise complaint with the governing statute

Given an upstream complaint-style record (illustrative shape — any skill returning a topic/category and a location works the same way):

```json
{"category": "Noise - Residential", "borough": "Queens", "reported_at": "2026-07-09T22:14:00Z"}
```

Map `category` to this corpus's `topic` filter and call `/penalties` (the complaint implies enforcement, not just a definition):

```bash
curl -s -X POST https://nanda-municipal-laws.vercel.app/api/v1/penalties \
  -H "Content-Type: application/json" -d '{"topic": "NOISE CONTROL"}'
```

```json
{
  "results": [
    {"section_number": "24-263", "section_title": "Civil penalties", "document_type": "NYC Administrative Code", "url": "https://nycadmincode.readthedocs.io/...", "...": "..."}
  ],
  "count": 1,
  "reasoning": "filtered to chunks flagged mentions_penalty=true; ...",
  "provenance": {"signature": "...", "public_key": "...", "signed_at": "...", "algorithm": "ed25519"}
}
```

The composing agent now has: the original signed complaint record (from whatever upstream skill produced it) plus a signed citation to the actual civil-penalty provision — attach both to its own output rather than asserting "this violates noise law" as an unsupported claim. Verify this response's signature per [PROVENANCE.md](./PROVENANCE.md) before treating `results` as authoritative.

## Why this isn't a live integration test

This repo intentionally does not hard-depend on any specific external hackathon skill's live uptime in its own test suite or runtime — a dependency on another team's demo deployment would make this service's own reliability hostage to theirs. The pattern above is deliberately generic (any topic/category-bearing upstream record composes the same way) so it stays valid regardless of which specific civic-data skill is live at judging time.

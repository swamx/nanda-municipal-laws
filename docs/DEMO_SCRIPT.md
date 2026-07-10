# Demo video script

**No length or format limit is specified** — checked both the Nanda Town hackathon page and the official hackathon site (nandahack.media.mit.edu). What *is* confirmed there:

- **Deadline**: Saturday, July 11, 2026, 2:00 PM ET — same deadline as your final SkillMD.
- **Submit it as a link in the final Google form** (not a file upload) — host it wherever's convenient (YouTube unlisted, Loom, Google Drive) and paste the shareable link.
- **Required to complete your submission, not separately scored** — but explicitly needed if you land in the top 10, since organizers show it to people then. Don't skip it even though it's not part of the score.
- **What actually gets scored** (Phase 2 = 80% of your total, Phase 1's core-protocol PR = 20%): *usefulness, creativity, setup ease, and whether "agents can use it from your SKILL.md alone."* That last point matters for filming — make it obvious an agent could act on SKILL.md with zero extra hand-holding.

Target **~2.5 minutes** with the full search/term_map beat included; a tight 60-90s cut works if you're rushed (see "If you only have 60 seconds" at the bottom). Length itself isn't judged, but judges watching many submissions back-to-back will not sit through a bloated one.

## Setup before recording

- **Screen recorder**: Windows: `Win+G` (Xbox Game Bar, built in) or OBS Studio if installed. Record at 1080p, hide notifications.
- **Tabs/windows open in advance** (don't fumble live):
  1. A browser tab on `https://nanda-municipal-laws.vercel.app/docs` (Swagger UI) — this is your main stage.
  2. A terminal with `curl` ready (font size bumped up, 14-16pt) as a backup/companion to Swagger for the raw JSON.
  3. A browser tab on `https://nanda-municipal-laws.vercel.app/` (raw JSON root info) — install a JSON-formatter extension so it's not a wall of text.
  4. This repo's README open in the editor, scrolled to the top, for a 2-second establishing shot only — don't read it aloud.
- **Rehearse once** without recording so the live API calls (real network, real Mongo) don't introduce awkward dead air.

## The script

### 0:00–0:12 — Hook: state the problem, not the product

Say this over the README/title, ~5 seconds, then cut to the "6 hens" line in `docs/DATA_SOURCE.md` or just say it:

> "Autonomous agents keep answering legal questions from training-data folklore. Ask most LLMs about NYC chicken laws and they'll confidently tell you '6 hens max' — that's internet folklore. The real statute says no such thing. This skill exists so an agent never has to guess."

This is your single best hook — concrete, memorable, and it *is* the correctness story judges care about.

### 0:12–0:20 — One-line positioning

Cut to the README title / tagline on screen:

> "It's a deterministic, citation-backed municipal law lookup for autonomous agents — built for Nandatown, NYC as the example jurisdiction. No LLM in the loop on this side — every answer is grounded in the real ingested code."

### 0:20–1:35 — One worked example, start to finish, exactly as an agent does it

Rather than a grab-bag of unrelated endpoint calls, walk through **one single question** the way `SKILL.md`'s own "How to use this service" section tells a calling agent to: ask → verdict → verify → cite. Stay on this one example the whole time — it reads far more like a real agent than five disconnected demos.

**The question**: *"Can I keep a rooster in my apartment in Queens?"*

1. **`POST /api/v1/is_action_allowed`** with `{"action": "keep a rooster in my apartment"}` (Swagger `/docs`, **Try it out**, **Execute**, live). This is what SKILL.md tells an agent to call first for any yes/no legality question.
   > "The agent's first move: ask the headline endpoint directly. Back comes `allowed: false`, a citation to §161.19, and a `reasoning` string — but a careful agent doesn't just repeat that verdict to the user. It verifies it."
2. **`GET /api/v1/sections/161.19`** — take the `section_number` the previous response just cited and pull the **full, untruncated** text, `structural_summary`, and `cross_references`.
   > "The `is_action_allowed` response only echoed a snippet. Before quoting a legal provision, the agent pulls the complete official text — so nothing it tells the user is quoted out of context."
3. **`POST /api/v1/sections/161.19/term_map`** with `{"query": "rooster"}` — the highlight service. Show the response: the literal occurrence of "rooster," `<mark>`-wrapped, with character offsets.
   > "And to make its citation *auditable* — not just asserted — it can point at exactly where in that full text the word 'rooster' appears. This is the same evidence a human reviewer could check by hand: a real URL, a real section number, a highlighted span of real text."
4. **`GET /api/v1/sections/161.19/related`** — the section's own cross-reference (§161.01), resolved to its own citation.
   > "It even follows the statute's own internal cross-reference, one hop, so the agent's final answer isn't missing context the law itself points to."
5. Cut to a title card or just say the **composed final answer** the agent would now return, in the `{answer, sources, reasoning}` shape from `SKILL.md`:
   > "answer: No — §161.19 of the NYC Health Code prohibits keeping a live rooster in the city outside specific exceptions. sources: section 161.19, this URL. reasoning: derived from the cited text, verified against the full section and the highlighted match."

That's the whole loop: **one question, one verdict, one verification chain, one composed answer** — nothing in it was asserted without a traceable, highlighted source.

*(Optional 10s coda if you have time: re-run step 1 with `{"action": "Keep backyard chickens"}` to show `allowed: true`, `confidence: "medium"`, with the same rooster prohibition still surfacing in `conditions` — proving the tool distinguishes an explicit rule from an absence-of-restriction inference, not just a blunt yes/no.)*

### 1:35–2:00 — Prove the scale and the guardrails

Switch to the Swagger UI (`/docs`) or the root `/` JSON. Point at:
- Corpus stats: 668 documents, 10,702 chunks, the **entire** NYC Administrative Code + Health Code, not a curated sample.
- The full endpoint list (search, sections, related, term_map, penalties, permits) — more than a single yes/no toy.

> "It's the entire corpus — 32 titles of the Admin Code, all 36 articles of the Health Code — not a cherry-picked demo slice."

### 2:00–2:25 — What makes this different, fast

Hit these three in rapid succession (15-20s combined, don't over-explain):

1. **Signed provenance** — hit `GET /api/v1/pubkey`, then show a `/search` response's `provenance` field: "Every answer is Ed25519-signed, so another agent can verify offline that this service produced it — not a relay, not a cache."
2. **Corpus freshness** — `GET /api/v1/version`: "Law goes stale — this tells a caller exactly how stale."
3. **MCP-native** — mention (screen or just say): "It's also exposed as MCP tools, so Claude Desktop or Claude Code can call it directly, not just raw HTTP."

### 2:25–2:40 — Close

Cut back to the README or a title card:

> "Deterministic. Citation-backed. Fully tested — 135 passing tests. Live now at nanda-municipal-laws.vercel.app. That's the Municipal Law Skill."

## If you only have 60 seconds

Keep the one-example flow but trim it to three steps: hook (0:00-0:12) → `is_action_allowed` on the rooster question (0:12-0:30) → `term_map` on §161.19 as the single most visual proof of "verifiable, not asserted" (0:30-0:50) → close line (0:50-1:00). Drop `/sections`, `/related`, the backyard-chickens coda, and the scale/differentiators beats entirely at this length.

## Filming tips specific to this repo

- **Don't** scroll through source code — a demo video proves the product works, not that you can read a file tree.
- **Do** let at least one API call hit the *live* Vercel deployment on camera (not localhost) — "realism" is a named judging criterion, and a live network call is more convincing than a canned screenshot.
- If the live call is slow/flaky on the day, have a pre-recorded clip of the same call as backup, but prefer live.
- Keep captions/on-screen text terse if you add them: "No LLM. Real law. Signed answers." reads faster than a paragraph while judges skim.
- Swagger UI's response panel can be dense — zoom in (browser `Ctrl` `+`, or Windows Magnifier) on just `allowed`, `citations`, and `reasoning` so those three fields are legible on a recorded screen, rather than showing the whole raw payload at normal size.

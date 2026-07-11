# Demo video script

**No length or format limit is specified** — checked both the Nanda Town hackathon page and the official hackathon site (nandahack.media.mit.edu). What *is* confirmed there:

- **Deadline**: Saturday, July 11, 2026, 2:00 PM ET — same deadline as your final SkillMD.
- **Submit it as a link in the final Google form** (not a file upload) — host it wherever's convenient (YouTube unlisted, Loom, Google Drive) and paste the shareable link.
- **Required to complete your submission, not separately scored** — but explicitly needed if you land in the top 10, since organizers show it to people then. Don't skip it even though it's not part of the score.
- **What actually gets scored** (Phase 2 = 80% of your total, Phase 1's core-protocol PR = 20%): *usefulness, creativity, setup ease, and whether "agents can use it from your SKILL.md alone."* That last point matters for filming — make it obvious an agent could act on SKILL.md with zero extra hand-holding.

Target **~3 minutes**. Length itself isn't judged, but judges watching many submissions back-to-back will not sit through a bloated one — every second should be earning its place.

## The one idea this script is built around

**Don't frame this as "I built a legal search engine" or a product demo of REST endpoints — judges already know how to evaluate a REST API.** Frame it as a *capability*:

> "I built a deterministic municipal law skill that any AI agent can invoke to obtain grounded, citation-backed legal evidence from the complete NYC Administrative and Health Codes."

The whole video should answer one question — **"Why does an autonomous agent need this skill?"** — not "what did I implement." Everything below is structured around that.

## Setup before recording

- **Screen recorder**: Windows: `Win+G` (Xbox Game Bar, built in) or OBS Studio if installed. Record at 1080p, hide notifications.
- **Tabs/windows open in advance** (don't fumble live):
  1. A slide/title-card tool (even a plain dark-background text editor works) for the stats overlay, architecture slide, and end card.
  2. A browser tab on `https://nanda-municipal-laws.vercel.app/docs` (Swagger UI) — brief use only, see 2:15–3:00 below.
  3. A terminal with `curl` ready (font size bumped up, 14-16pt) as a companion to Swagger for the raw JSON, or `docs/demo.html` open locally for one-click real calls (see [DEMO_WORKFLOWS.md](./DEMO_WORKFLOWS.md)).
- **Rehearse once** without recording so the live API calls (real network, real Mongo) don't introduce awkward dead air.

## The script

### 0:00–0:20 — Hook: the problem, not the product

Start on a plain title card or your face, not Swagger, not code:

> "Today's AI agents frequently hallucinate municipal laws or cite regulations that don't exist. I built a deterministic municipal law skill that gives any AI agent citation-backed access to the complete NYC Administrative and Health Codes — no LLM in the loop, so there's nothing for it to hallucinate."

Cut immediately to a stats overlay, ~3-4 seconds, real numbers only:

```text
32 Titles (NYC Administrative Code)
4,781 Sections

36 Articles (NYC Health Code)
501 Sections

No LLM · Deterministic · Citation-Backed
```

### 0:20–0:45 — One architecture slide, then move on

One slide, on screen ~10-15 seconds while you say the line below — don't linger:

```text
Official NYC sources (nyc.gov, nycadmincode.readthedocs.io)
        |
     Crawler
        |
   Normalization
        |
    MongoDB
        |
    FastAPI
        |
    AI Agent
```

> "The service never generates legal advice. It only returns official text and citations — the calling agent does the reasoning."

Don't explain MongoDB, FastAPI, or any implementation detail here — that line about never generating legal advice is the only sentence in this beat that matters to a judge.

### 0:45–2:15 — Three stories, not an endpoint tour

This is the biggest structural change from a typical demo: **don't say "here are my endpoints."** Walk through three different people asking three different real questions, each following the same shape — ask → retrieve → cite → agent answers — so judges see *why* the skill exists, not just *what* it returns. Every citation below is real, copied from the live deployment, not staged.

#### Story 1 — A resident: "Can I keep backyard chickens?"

```text
Resident asks
    |
Agent calls POST /is_action_allowed
    |
allowed: true (confidence: medium) — citing §161.19
    |
Agent answers: "Yes, but roosters are prohibited citywide"
```

> "A resident wants a straight answer. The agent calls the headline endpoint, gets back an explicit citation to §161.19 of the Health Code, and composes a grounded answer — chickens are fine, roosters aren't, and here's the exact text that says so."

*(This is the one story worth showing on screen with the real API call live — `POST /api/v1/is_action_allowed {"action": "Keep backyard chickens"}` — since it's your single most memorable, most-tested example. Keep the other two as narrated diagrams to hold pace.)*

#### Story 2 — A food vendor: "What permit do I need to operate a mobile food cart?"

```text
Food vendor asks
    |
Agent calls POST /permits {"query": "mobile food vending unit license permit"}
    |
Top result: §89.11 "Applications for permits and licenses" (Mobile Food Vending)
    |
Agent answers: "You need a vending permit/license under §89.11 — fees are set by §17-308"
```

> "A food vendor asks a completely different kind of question — not yes/no, but 'what do I need.' Same skill, different endpoint: `/permits` surfaces §89.11, the real mobile-food-vending permit section, with the actual fee cross-reference."

#### Story 3 — A building owner: "What's the penalty if I dump construction debris illegally?"

```text
Building owner asks
    |
Agent calls POST /penalties {"topic": "dumping"} -> GET /sections/16-119
    |
§16-119 "Dumping prohibited" — misdemeanor, $1,500-$10,000 civil penalty,
vehicle impoundment, repeat offenses up to $20,000
    |
Agent answers: real dollar figures, straight from the statute
```

> "A third question, a third real citation — this time with actual enforcement numbers, not a vague 'consult a lawyer.' Same three-step shape every time: ask, retrieve, cite."

Close this beat with the one sentence that ties it to the hackathon's own goal:

> "This skill lets any autonomous agent in NANDA Town answer municipal-law questions using authoritative legal sources — instead of relying on an LLM's memory."

### 2:15–2:45 — Swagger, briefly

Cut to `/docs`. This section is short on purpose — **30-45 seconds, one call, done**:

1. Expand **Legal Determination**, click `is_action_allowed`, **Try it out** (already pre-filled with a real example), **Execute**.
2. Let the real response land on screen for 2-3 seconds. Don't scroll through every field.

> "Here it is live — Try it out, Execute, and that's the same call from Story 1, running for real right now."

Don't spend more time here. Judges already know how to read Swagger; you're just proving it's real, not a mockup.

### 2:45–3:10 — The engineering story, shown, not told

This is where the project is genuinely stronger than most submissions — but *"I wrote 5,000 lines"* means nothing to a judge. Show three concrete bugs-found-and-fixed as quick visual beats (a few seconds each, title-card style):

```text
Bug: naive substring search
    |
"fine" matched inside "defined"
    |
False positive
    |
Fixed: word-boundary matching everywhere
```

```text
36 Health Code PDFs
    |
Each formatted slightly differently
    |
Parser normalized all of them
    |
Verified section-by-section against real text
```

```text
Popular internet myth: "NYC caps chickens at 6 hens"
    |
Real statute text: no such limit exists
    |
Regression test locks this in
    |
Never fabricated, ever
```

> "Real bugs, caught by testing against the actual government PDFs and the actual live corpus — not assumed, verified."

### 3:10–3:20 — Close

End on one slide:

```text
Agent-ready. Deterministic. Citation-backed.

4,781 NYC Administrative Code sections
501 NYC Health Code sections

No hallucinations — grounded by citations, every time.

Live now: nanda-municipal-laws.vercel.app
```

> "Deterministic. Citation-backed. Fully tested. Live now. That's the Municipal Law Skill."

## If you only have 60 seconds

Hook (0:00-0:15, stats overlay included) → Story 1 only, live on screen (`is_action_allowed` → the rooster/chickens verdict, 0:15-0:40) → the NANDA-relevance sentence (0:40-0:50) → close line (0:50-1:00). Drop the architecture slide, Stories 2 and 3, Swagger, and the engineering-bugs beat entirely at this length.

## What NOT to show

However tempting, don't spend any time on:

- Package/folder structure or repository layout
- Docker, CI pipelines, or deployment config
- Environment variables or MongoDB collection internals
- Scrolling through source code

These matter to developers reviewing a PR, not to a judge with 3-5 minutes deciding whether this is a reusable agent capability. Every second spent on them is a second not spent on capability, correctness, and agent usability — which is what's actually being scored.

## Filming tips specific to this repo

- **Do** let at least one API call hit the *live* Vercel deployment on camera (not localhost) — "realism" is a named judging criterion, and a live network call is more convincing than a canned screenshot. Story 1's `is_action_allowed` call is the one to make live.
- If the live call is slow/flaky on the day, have a pre-recorded clip of the same call as backup, but prefer live.
- Keep captions/on-screen text terse if you add them: "No LLM. Real law. Grounded by citations." reads faster than a paragraph while judges skim.
- Swagger UI's response panel can be dense — zoom in (browser `Ctrl` `+`, or Windows Magnifier) on just `allowed`, `citations`, and `reasoning` so those three fields are legible on a recorded screen, rather than showing the whole raw payload at normal size.
- For the three-story beat (0:45–2:15), narrated diagrams at a brisk pace read as more confident than reading endpoint names off a slide — practice the three "ask → retrieve → cite → answer" lines out loud until they're fast and natural.

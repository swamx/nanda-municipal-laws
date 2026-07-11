"""Single source of truth for the pitch deck's slide content - every
generator (build_pptx.py, build_html.py, build_markdown.py) renders from
this same list, so the outputs can't drift apart.

Every fact/number here is real, verified against the live deployment or the
repo's own generated docs (docs/COVERAGE.md) while building this deck - see
docs/DEMO_WORKFLOWS.md and docs/DEMO_SCRIPT.md for the underlying verification.

Ordering follows two rounds of reviewer feedback: problem -> stories (what
sells the project) -> architecture -> corpus scale -> engineering ->
why-not-an-LLM -> APIs (condensed to one slide) -> trust -> why NANDA ->
close. The API detail that used to span 4 slides is intentionally now a
single slide - judges evaluate an agent skill, not a REST API surface.

Round 2 changes: replaced "No hallucinations" (imprecise - an LLM *agent*
calling this skill could still hallucinate; only this service's own output
is guaranteed generation-free) with "Deterministic, citation-backed legal
evidence"; added a Traditional-RAG-vs-this-skill flow comparison to slide 3;
converted the three story slides from numbered steps to a single flow
diagram per story (ending in a highlighted citation node, then the actual
composed answer below); added a "not a curated demo dataset" callout to the
stats slide; reworded the engineering slide's title and the LLM-comparison's
left column to read as an explanation rather than a criticism; added a bold
lead line to the trust slide naming Ed25519 explicitly; added a closing
"any agent / any language / any framework / just HTTP" line to the NANDA
slide.
"""

LIVE_URL = "https://nanda-municipal-laws.vercel.app"
REPO_URL = "https://github.com/swamx/nanda-municipal-laws"

SLIDES = [
    {
        "kind": "title",
        "title": "Municipal Law Skill",
        "subtitle": "for Autonomous Agents",
        "tagline": "An agent-ready municipal law skill providing deterministic, citation-backed legal evidence.",
        "footer": "NANDA Town · MIT Reality Hackathon 2026",
        "url": LIVE_URL,
    },
    {
        "kind": "myth",
        "title": "AI agents hallucinate municipal law",
        "wrong_label": "Internet folklore",
        "wrong_claim": "“You may keep up to six hens.”",
        "right_label": "NYC Health Code §161.19 (the real statute)",
        "right_claim": "No such limit exists.",
        "right_detail": "Only certain birds (roosters, ducks, geese, turkeys) are prohibited — with narrow exceptions. Nothing restricts hens at all.",
        "footer_line": "Agents relying on an LLM's training data repeat exactly this kind of confident, wrong answer. Legal citations need to come from the actual code — not a model's memory.",
    },
    {
        "kind": "quote",
        "title": "The capability",
        "quote": "A deterministic municipal law skill that any AI agent can invoke to obtain grounded, citation-backed legal evidence from the complete NYC Administrative and Health Codes.",
        "flows": [
            {"label": "Traditional RAG", "steps": ["Question", "LLM", "Answer"], "muted": True},
            {"label": "Municipal Law Skill", "steps": ["Question", "Skill", "Official Evidence", "Agent", "Grounded Answer"], "muted": False},
        ],
        "emphasis": "The service never generates answers. It only returns legal evidence.",
    },
    {
        "kind": "story",
        "title": "Story 1 — A resident",
        "question": "“Can I keep backyard chickens?”",
        "flow": ["Resident", "Agent", "POST /is_action_allowed", "NYC Health Code §161.19"],
        "citation_index": 3,
        "answer": "“Yes, but roosters are prohibited citywide”",
    },
    {
        "kind": "story",
        "title": "Story 2 — A food vendor",
        "question": "“What permit do I need to operate a mobile food cart?”",
        "flow": ["Food vendor", "Agent", "POST /permits", "§89.11 Applications for permits and licenses"],
        "citation_index": 3,
        "answer": "“You need a vending permit/license under §89.11 — fees are set by §17-308”",
    },
    {
        "kind": "story",
        "title": "Story 3 — A building owner",
        "question": "“What's the penalty if I dump construction debris illegally?”",
        "flow": ["Building owner", "Agent", "POST /penalties → GET /sections/16-119", "$1,500 – $10,000 civil penalty"],
        "citation_index": 3,
        "answer": "Real dollar figures, straight from the statute — not a vague “consult a lawyer.”",
    },
    {
        "kind": "diagram",
        "title": "Architecture",
        "diagram": [
            "Official NYC sources",
            "Crawler",
            "Normalization",
            "MongoDB",
            "FastAPI Skill",
            "Autonomous Agent",
            "Grounded Answer",
        ],
        "callout": "The service never generates legal advice — only official text and citations. The last step is why it exists.",
    },
    {
        "kind": "stats",
        "title": "The complete corpus, not a sample",
        "stat_groups": [
            {"label": "Entire NYC Administrative Code", "stats": [("32", "Titles"), ("4,781", "Sections")]},
            {"label": "Entire NYC Health Code", "stats": [("36", "Articles"), ("501", "Sections")]},
        ],
        "footnote": "668 source documents · 10,702 searchable chunks · ≈55 MB total",
        "callout": "Not a curated demo dataset.",
    },
    {
        "kind": "bullets",
        "title": "Production issues discovered using live municipal data",
        "bullets": [
            "Naive substring search: “fine” matched inside “defined” — fixed with word-boundary matching everywhere",
            "36 Health Code PDFs, each formatted slightly differently — parser normalized and verified section-by-section against real text",
            "The “6 hens” myth — a regression test locks in the true statute text, forever",
            "Hidden ingestion size limit silently truncated requests — found and fixed before it silently dropped data",
        ],
    },
    {
        "kind": "comparison",
        "title": "Why not just ask an LLM?",
        "left_label": "LLM memory",
        "left_items": ["May be incomplete", "May be outdated", "Cannot prove provenance"],
        "right_label": "Municipal Law Skill",
        "right_items": ["Official source", "Deterministic", "Citations", "Verifiable"],
    },
    {
        "kind": "capability_table",
        "title": "Agent-facing capabilities",
        "rows": [
            ("Determine legality", "/is_action_allowed", "Allowed, conditions, citations, confidence"),
            ("Search law", "/search", "Ranked legal evidence, filterable by source"),
            ("Retrieve statute", "/sections/{id}", "Official, untruncated text"),
            ("Find penalties", "/penalties", "Enforcement provisions"),
            ("Find permits", "/permits", "Permit/license requirements"),
        ],
        "admin_note": "Also available, kept separate from the agent-facing surface above: /health, /version, /pubkey, /ingest — operational only, not part of the reasoning loop.",
    },
    {
        "kind": "diagram",
        "title": "Trust & verification",
        "lead": "Every response is cryptographically signed (Ed25519).",
        "diagram": ["Signed", "Verifiable", "Deterministic", "Replayable"],
        "callout": "/pubkey lets any downstream agent verify offline that this service, not a relay or a cache, produced a citation. /version reports corpus freshness, so callers know exactly how stale the law is.",
    },
    {
        "kind": "quote",
        "title": "Why NANDA",
        "quote": "This transforms municipal law from static documents into a reusable capability that any NANDA agent can invoke.",
        "bullets": [
            "Composable by design — the last hop in a chain started by another skill (a 311 complaint, a permit application, a code-enforcement lead)",
            "Any agent that can call an HTTP endpoint can invoke it, per SKILL.md",
        ],
        "emphasis": "Any agent. Any language. Any framework. Just HTTP.",
    },
    {
        "kind": "closing",
        "title": "Agent-ready. Deterministic. Citation-backed.",
        "bullets": [
            "✓ Complete NYC Administrative & Health Codes",
            "✓ Deterministic, citation-backed legal evidence",
            "✓ Live, agent-ready HTTP skill",
        ],
        "url": LIVE_URL,
        "repo": REPO_URL,
    },
]

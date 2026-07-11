"""Single source of truth for the pitch deck's slide content - both
build_pptx.py (native .pptx) and build_html.py (-> PDF via headless Chrome)
render from this same list, so the two outputs can't drift apart.

Every fact/number here is real, verified against the live deployment or the
repo's own generated docs (docs/COVERAGE.md) while building this deck - see
docs/DEMO_WORKFLOWS.md and docs/DEMO_SCRIPT.md for the underlying verification.
"""

LIVE_URL = "https://nanda-municipal-laws.vercel.app"
REPO_URL = "https://github.com/swamx/nanda-municipal-laws"

SLIDES = [
    {
        "kind": "title",
        "title": "Municipal Law Skill",
        "subtitle": "for Autonomous Agents",
        "tagline": "Deterministic, citation-backed municipal law retrieval — no LLM in the loop",
        "footer": "NANDA Town · MIT Reality Hackathon 2026",
        "url": LIVE_URL,
    },
    {
        "kind": "bullets",
        "title": "AI agents hallucinate municipal law",
        "bullets": [
            "Popular internet myth: “NYC caps backyard chickens at 6 hens”",
            "The real statute (§161.19) states no such number — it only prohibits roosters, ducks, geese, and turkeys, with narrow exceptions",
            "Agents relying on an LLM's training data repeat exactly this kind of confident, wrong answer",
            "Legal citations need to come from the actual code — not a model's memory",
        ],
    },
    {
        "kind": "quote",
        "title": "The capability",
        "quote": "A deterministic municipal law skill that any AI agent can invoke to obtain grounded, citation-backed legal evidence from the complete NYC Administrative and Health Codes.",
        "bullets": [
            "No LLM calls, ever — nothing for the service itself to hallucinate",
            "Same query → same citations → same ordering, every time",
            "The calling agent performs the reasoning; this service only supplies evidence",
        ],
    },
    {
        "kind": "diagram",
        "title": "Architecture",
        "diagram": [
            "Official NYC sources (nyc.gov, nycadmincode.readthedocs.io)",
            "Crawler",
            "Normalization",
            "MongoDB",
            "FastAPI",
            "AI Agent",
        ],
        "callout": "The service never generates legal advice — only official text and citations.",
    },
    {
        "kind": "stats",
        "title": "The complete corpus, not a sample",
        "stat_groups": [
            {"label": "NYC Administrative Code", "stats": [("32", "Titles"), ("4,781", "Sections")]},
            {"label": "NYC Health Code", "stats": [("36", "Articles"), ("501", "Sections")]},
        ],
        "footnote": "668 source documents · 10,702 searchable chunks total",
    },
    {
        "kind": "api_table",
        "title": "Agent-facing APIs — Legal Determination & Search",
        "rows": [
            ("POST", "/is_action_allowed", "Headline capability — yes/no legality check on a described action. Returns allowed, conditions, citations, reasoning, confidence."),
            ("POST", "/search", "General keyword lookup across the entire corpus — filterable by title, chapter, document_type, agency, or topic."),
            ("POST", "/sections/{id}/term_map", "Highlight exactly where search terms occur within a section — built for search-results/demo UI rendering."),
        ],
    },
    {
        "kind": "api_table",
        "title": "Agent-facing APIs — Lookup & Cross References",
        "rows": [
            ("GET", "/sections/{id}", "Exact section retrieval by number — full untruncated text plus a deterministic structural summary."),
            ("GET", "/sections/{id}/related", "Resolve a section's own cross-references into their citations — a one-hop citation graph."),
            ("GET", "/documents/{id}", "Metadata for a source document (an Admin Code chapter or Health Code article)."),
            ("GET", "/documents/{id}/chunks", "Every section belonging to one document, in order."),
        ],
    },
    {
        "kind": "api_table",
        "title": "Agent-facing APIs — Penalties & Permits",
        "rows": [
            ("POST", "/penalties", "Find sections flagged as mentioning a penalty or fine — for enforcement-related questions."),
            ("POST", "/permits", "Find sections flagged as requiring a permit or license."),
        ],
    },
    {
        "kind": "api_table",
        "title": "Administration & operational endpoints",
        "subtitle": "Kept separate from the agent-facing retrieval surface above — not part of the reasoning loop",
        "rows": [
            ("GET", "/health", "Liveness check — reports MongoDB reachability."),
            ("GET", "/version", "Deployed app version, plus corpus freshness: last-ingested date and age in days."),
            ("GET", "/pubkey", "Ed25519 public key for verifying a signed response's provenance offline."),
            ("POST", "/ingest", "Fetch, parse, and persist new source documents. Operational only, API-key gated — not for agent use."),
        ],
    },
    {
        "kind": "story",
        "title": "Story 1 — A resident",
        "question": "“Can I keep backyard chickens?”",
        "steps": [
            "Agent calls POST /is_action_allowed",
            "allowed: true (confidence: medium) — citing §161.19",
            "Agent answers: “Yes, but roosters are prohibited citywide”",
        ],
    },
    {
        "kind": "story",
        "title": "Story 2 — A food vendor",
        "question": "“What permit do I need to operate a mobile food cart?”",
        "steps": [
            "Agent calls POST /permits {\"query\": \"mobile food vending unit license permit\"}",
            "Top result: §89.11 “Applications for permits and licenses” (Mobile Food Vending)",
            "Agent answers: “You need a vending permit/license under §89.11 — fees are set by §17-308”",
        ],
    },
    {
        "kind": "story",
        "title": "Story 3 — A building owner",
        "question": "“What's the penalty if I dump construction debris illegally?”",
        "steps": [
            "Agent calls POST /penalties → GET /sections/16-119",
            "§16-119 “Dumping prohibited” — misdemeanor, $1,500–$10,000 civil penalty, vehicle impoundment",
            "Agent answers with real dollar figures, straight from the statute",
        ],
    },
    {
        "kind": "bullets",
        "title": "Engineering: bugs found and fixed, not just claimed",
        "bullets": [
            "Naive substring search: “fine” matched inside “defined” — fixed with word-boundary matching everywhere",
            "36 Health Code PDFs, each formatted slightly differently — parser normalized and verified section-by-section against real text",
            "The “6 hens” myth — a regression test locks in the true statute text, forever",
        ],
    },
    {
        "kind": "bullets",
        "title": "Trust & verification",
        "bullets": [
            "Every /is_action_allowed and /search response is Ed25519-signed",
            "/pubkey lets any downstream agent verify offline that this service — not a relay or a cache — produced a citation",
            "/version reports corpus freshness — law goes stale, and callers can know exactly how stale",
            "Same query → same citations → same ordering — no randomness, ever",
        ],
    },
    {
        "kind": "quote",
        "title": "Why NANDA",
        "quote": "This skill lets any autonomous agent in NANDA Town answer municipal-law questions using authoritative legal sources — instead of relying on an LLM's memory.",
        "bullets": [
            "Composable by design — the last hop in a chain started by another skill (a 311 complaint, a permit application, a code-enforcement lead)",
            "Any agent that can call an HTTP endpoint can invoke it, per SKILL.md",
        ],
    },
    {
        "kind": "closing",
        "title": "Agent-ready. Deterministic. Citation-backed.",
        "bullets": [
            "4,781 NYC Administrative Code sections",
            "501 NYC Health Code sections",
            "No hallucinations — grounded by citations, every time",
        ],
        "url": LIVE_URL,
        "repo": REPO_URL,
    },
]

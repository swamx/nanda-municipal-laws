from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CorpusStats(BaseModel):
    """Static snapshot of ingested coverage - real numbers from docs/COVERAGE.md
    (generated from live MongoDB by scripts/generate_coverage_report.py), mirrored
    here by hand since both sources are already-ingested and essentially fixed.
    Re-sync both if the corpus is ever re-scoped.
    """

    admin_code_titles: int = 32
    admin_code_sections: int = 4781
    health_code_articles: int = 36
    health_code_sections: int = 501
    total_documents: int = 668
    total_chunks: int = 10702


class RootInfo(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Municipal Law Skill for Autonomous Agents",
                    "version": "0.1.0",
                    "tagline": "Deterministic, citation-backed NYC municipal law retrieval. No LLM calls, ever - this service only returns authoritative legal evidence and citations; the calling agent performs reasoning.",
                    "killer_example": {
                        "action": "Keep backyard chickens",
                        "call": "POST /api/v1/is_action_allowed",
                        "try_it": 'curl -X POST /api/v1/is_action_allowed -d \'{"action": "Keep backyard chickens"}\'',
                    },
                    "corpus": {
                        "admin_code_titles": 32,
                        "admin_code_sections": 4781,
                        "health_code_articles": 36,
                        "health_code_sections": 501,
                        "total_documents": 668,
                        "total_chunks": 10702,
                    },
                    "docs": "/docs",
                    "health": "/api/v1/health",
                    "skill": "/skill.md",
                }
            ]
        }
    )

    name: str
    version: str
    tagline: str = Field(description="This service's entire design philosophy in one sentence.")
    killer_example: dict = Field(description="A concrete, runnable example of the headline capability - see /docs to try it interactively.")
    corpus: CorpusStats
    docs: str = Field(description="Interactive Swagger UI - every endpoint, with request/response examples.")
    health: str
    skill: str = Field(description="Agent-facing reference: how to call this service, compose a final answer, and the rules for never overclaiming.")


class SearchRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"query": "rooster keeping poultry", "document_type": "NYC Health Code"},
                {"query": "food truck vendor permit"},
            ]
        }
    )

    query: str = Field(min_length=1, description="Literal keywords to search for - this is keyword search, not a natural-language question. Term frequency drives ranking, not phrase meaning.")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of ranked results to return.")
    title_num: str | None = Field(default=None, description="NYC Administrative Code title filter, e.g. '24'.")
    chapter_num: str | None = Field(default=None, description="NYC Administrative Code chapter filter, e.g. '2'.")
    document_type: str | None = Field(
        default=None, description="Restrict to one source: 'NYC Administrative Code' or 'NYC Health Code'."
    )
    agency: str | None = Field(default=None, description="Filter by the agency of record, e.g. 'Department of Health and Mental Hygiene (DOHMH)'.")
    topic: str | None = Field(default=None, description="Filter by chapter/article name, e.g. 'ANIMALS' or 'NOISE CONTROL'.")
    # Overrides settings.search_mode ("text_index" default, or "in_app")
    # for this call only. Invalid values are ignored (fall back to default).
    search_mode: str | None = Field(
        default=None,
        description="Override the default ranking engine for this call only: 'text_index' (native MongoDB $text, default) or 'in_app' (Python TF-style scoring, no index dependency).",
    )


class SearchResultItem(BaseModel):
    document_id: str = Field(description="Mongo id of the parent document - pass to GET /documents/{id} for full document metadata.")
    section_number: str = Field(description="Statute section number, e.g. '161.19' or '24-222'.")
    section_title: str
    url: str = Field(description="Direct link to the official source (readthedocs anchor for Admin Code, PDF page anchor for Health Code).")
    score: float = Field(description="Relevance score from the active ranking engine - not a probability, not a confidence level.")
    snippet: str = Field(description="A ranked excerpt of the section's text. Can be truncated - call GET /sections/{section_number} for the full, untruncated text before quoting an exact figure or wording.")
    document_type: str
    agency: str
    topic: str


class SearchResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "rooster keeping poultry",
                    "results": [
                        {
                            "document_id": "6a4fde5c15b3681819636581",
                            "section_number": "161.19",
                            "section_title": "Keeping of livestock, live poultry and rabbits",
                            "url": "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf#page=14",
                            "score": 12.0,
                            "snippet": "§161.19 Keeping of livestock, live poultry and rabbits. (a) No person shall keep a live rooster, duck, goose or turkey...",
                            "document_type": "NYC Health Code",
                            "agency": "Department of Health and Mental Hygiene (DOHMH)",
                            "topic": "ANIMALS",
                        }
                    ],
                    "count": 1,
                    "reasoning": "matched query 'rooster keeping poultry' against 41 candidate chunk(s) after applying filters; ranked by term frequency, title weighted higher than body",
                }
            ]
        }
    )

    query: str
    results: list[SearchResultItem]
    count: int
    reasoning: str = Field(description="Mechanical explanation of how this result set was derived - never a legal conclusion. This service does not call an LLM; composing a natural-language answer from these citations is the calling agent's job (see SKILL.md).")


class DocumentOut(BaseModel):
    id: str
    document_type: str
    agency: str
    topic: str
    title_num: str | None = Field(default=None, description="Set for NYC Administrative Code documents, null for NYC Health Code.")
    title_name: str | None = None
    chapter_num: str | None = None
    chapter_name: str | None = None
    subchapter_num: str | None = None
    subchapter_name: str | None = None
    article_num: str | None = Field(default=None, description="Set for NYC Health Code documents, null for NYC Administrative Code.")
    article_name: str | None = None
    source_url: str
    ingested_at: datetime
    section_count: int = Field(description="Number of sections (chunks) this document was split into.")


class ChunkOut(BaseModel):
    section_number: str
    section_title: str
    text: str = Field(description="Full, untruncated section text - safe to quote exact figures/wording from this field.")
    url: str
    chunk_index: int
    document_type: str
    agency: str
    topic: str
    keywords: list[str]
    cross_references: list[str] = Field(description="Other section_numbers this chunk's text mentions by §-prefixed citation.")
    mentions_penalty: bool = Field(description="Keyword heuristic, not a legal determination - read `text` before asserting a penalty applies.")
    mentions_permit: bool = Field(description="Keyword heuristic, not a legal determination - read `text` before asserting a permit is required.")


class HealthResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "ok"}]})

    status: str = Field(description="'ok' if MongoDB is reachable, 'degraded' otherwise. Always returns HTTP 200 either way.")


class VersionResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"version": "0.1.0"}]})

    version: str


class IngestRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"urls": ["https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf"]}
            ]
        }
    )

    # Hard schema ceiling, well above the default INGEST_MAX_URLS=10 - the
    # real, configurable limit is enforced in the route via settings.ingest_max_urls;
    # this is just a sanity bound so an operator can raise INGEST_MAX_URLS
    # (e.g. for local bulk publishing) without being silently capped here.
    urls: list[str] = Field(
        min_length=1,
        max_length=100,
        description="Source URLs to fetch, parse, and persist. Admin Code HTML pages and Health Code PDF URLs are both supported and auto-detected by suffix. Administrative/operational endpoint, not part of the agent-facing retrieval surface.",
    )


class IngestResultItem(BaseModel):
    url: str
    status: str = Field(description="'ok' or 'error' for this specific URL - a per-URL failure doesn't fail the whole request.")
    chunks_ingested: int = 0
    error: str | None = None


class IngestResponse(BaseModel):
    results: list[IngestResultItem]


class SectionOut(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "section_number": "161.19",
                    "section_title": "Keeping of livestock, live poultry and rabbits",
                    "text": "§161.19 Keeping of livestock, live poultry and rabbits. (a) No person shall keep a live rooster, duck, goose or turkey in the City of New York except (1) in a slaughterhouse authorized by federal or state law...",
                    "url": "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf#page=14",
                    "document_type": "NYC Health Code",
                    "agency": "Department of Health and Mental Hygiene (DOHMH)",
                    "topic": "ANIMALS",
                    "jurisdiction": "New York City",
                    "keywords": ["keeping", "livestock", "live", "poultry", "rabbits"],
                    "cross_references": ["161.01"],
                    "mentions_penalty": False,
                    "mentions_permit": True,
                    "effective_date": None,
                    "repealed": False,
                    "structural_summary": [
                        "(a) No person shall keep a live rooster, duck, goose or turkey in the City of New York except...",
                        "(b) A person who is authorized by applicable law to keep for sale or sell livestock, live rabbits or poultry shall keep the premises... clean and free of animal nuisances.",
                        "(c) Live rabbit and poultry markets. Live rabbits and poultry intended for sale shall not be kept on the same premises as a multiple dwelling...",
                    ],
                    "chunk_count": 1,
                    "reasoning": "exact lookup by section_number='161.19'; structural_summary derived by splitting text on sentence-bounded lettered/numbered subsection markers; no query scoring involved",
                }
            ]
        }
    )

    section_number: str
    section_title: str
    text: str = Field(description="Full, untruncated section text - the authoritative source for any quoted number or wording.")
    url: str
    document_type: str
    agency: str
    topic: str
    jurisdiction: str
    keywords: list[str]
    cross_references: list[str] = Field(description="Other section_numbers mentioned in this section's text - resolve via GET /sections/{section_number}/related.")
    mentions_penalty: bool = Field(description="Keyword heuristic, not a legal determination.")
    mentions_permit: bool = Field(description="Keyword heuristic, not a legal determination.")
    effective_date: str | None = Field(description="Always null - neither source exposes a reliable machine-readable effective date. Never fabricated.")
    repealed: bool = Field(description="Defaults false - both sources serve current in-force text, not historical snapshots.")
    structural_summary: list[str] = Field(description="One entry per lettered/numbered subsection, from a deterministic text split - not an abstractive summary.")
    chunk_count: int
    reasoning: str = Field(description="Mechanical explanation of how this lookup was performed - no query scoring involved for an exact section_number match.")


class RelatedSection(BaseModel):
    section_number: str
    section_title: str | None = None
    url: str | None = None
    document_type: str | None = None
    resolved: bool = Field(description="False if this cross-reference points outside the ingested corpus - shown, not silently dropped.")


class RelatedLawsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "section_number": "161.19",
                    "related": [
                        {
                            "section_number": "161.01",
                            "section_title": "Wild and other animals prohibited",
                            "url": "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf#page=1",
                            "document_type": "NYC Health Code",
                            "resolved": True,
                        }
                    ],
                    "reasoning": "extracted 1 cross-reference(s) from §161.19's body text via regex; 1 of 1 resolved against the ingested corpus",
                }
            ]
        }
    )

    section_number: str
    related: list[RelatedSection]
    reasoning: str


class TermMapRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"query": "rooster poultry"}]})

    query: str = Field(min_length=1, description="Search terms to locate within the section - same tokenization as /search (word-boundary matching, common stopwords dropped).")
    context_chars: int = Field(
        default=80,
        ge=10,
        le=300,
        description="How many characters of surrounding context to include on each side of a highlighted term.",
    )


class TermOccurrence(BaseModel):
    start: int = Field(description="Character offset of the match start within the section's full text.")
    end: int = Field(description="Character offset of the match end within the section's full text.")
    snippet: str = Field(description="Context-bounded excerpt with the matched term wrapped in an HTML <mark> tag - render directly on a search-results page.")


class TermMapResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "section_number": "161.19",
                    "query": "rooster poultry",
                    "term_map": {
                        "rooster": [
                            {
                                "start": 45,
                                "end": 52,
                                "snippet": "…No person shall keep a live <mark>rooster</mark>, duck, goose or turkey in the City…",
                            }
                        ],
                        "poultry": [
                            {
                                "start": 10,
                                "end": 17,
                                "snippet": "§161.19 Keeping of livestock, live <mark>poultry</mark> and rabbits. (a) No person…",
                            }
                        ],
                    },
                    "total_occurrences": 2,
                    "reasoning": "tokenized query 'rooster poultry' into 2 distinct term(s) after dropping stopwords; scanned the full section text for word-boundary matches - a display aid for highlighting, not another ranking mode",
                }
            ]
        }
    )

    section_number: str
    query: str
    term_map: dict[str, list[TermOccurrence]] = Field(description="Each distinct query term mapped to every place it occurs in the section, in document order.")
    total_occurrences: int
    reasoning: str


class TopicFilterRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"query": "keep certain animals"},
                {"topic": "NOISE CONTROL"},
            ]
        }
    )

    query: str | None = Field(default=None, description="Optional keywords to additionally rank within the filtered set.")
    topic: str | None = Field(default=None, description="Restrict to one chapter/article, e.g. 'NOISE CONTROL' or 'ANIMALS'.")
    limit: int = Field(default=10, ge=1, le=50)
    search_mode: str | None = Field(default=None, description="Override the default ranking engine for this call only: 'text_index' or 'in_app'.")


class TopicFilterResponse(BaseModel):
    results: list[SearchResultItem]
    count: int
    reasoning: str


class ActionCheckRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"action": "Keep backyard chickens"},
                {"action": "Operate a food truck in Central Park"},
            ]
        }
    )

    action: str = Field(min_length=1, description="Plain-language description of the action to check, e.g. 'Keep backyard chickens' or 'Operate a food truck in Central Park'.")
    # Accepted but not currently used to change the determination beyond what's
    # textually relevant - this corpus has no geographic/zoning-lookup
    # capability (see "Not supported" in SKILL.md), so e.g. a borough name
    # in context won't narrow a citywide provision. Kept for forward
    # compatibility and to echo back in the response for the caller's own
    # record-keeping.
    context: dict | None = Field(
        default=None,
        description="Optional extra context (e.g. {'borough': 'Queens'}), echoed back for your own record-keeping. Does not currently narrow the determination beyond what's textually relevant - this service has no geographic/zoning-lookup capability.",
    )
    limit: int = Field(default=5, ge=1, le=20, description="How many candidate sections to consider internally before picking the closest match.")


class ActionCitation(BaseModel):
    section_number: str
    section_title: str
    url: str
    document_type: str
    matched_text: str = Field(description="The specific statutory text that drove the determination - always real, taken verbatim from the ingested corpus.")


class ActionCheckResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "action": "Keep backyard chickens",
                    "allowed": True,
                    "conditions": [
                        "(a) No person shall keep a live rooster, duck, goose or turkey in the City of New York except (1) in a slaughterhouse authorized by federal or state law... or (2) as authorized by §161.01(a) of this Article."
                    ],
                    "citations": [
                        {
                            "section_number": "161.19",
                            "section_title": "Keeping of livestock, live poultry and rabbits",
                            "url": "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf#page=14",
                            "document_type": "NYC Health Code",
                            "matched_text": "§161.19 Keeping of livestock, live poultry and rabbits. (a) No person shall keep a live rooster...",
                        }
                    ],
                    "reasoning": "§161.19 is the closest-matching provision, but contains no explicit prohibition or permission statement matching keywords in the requested action - this is an absence-of-restriction inference, not an affirmative statement. Read the full section text before relying on it.",
                    "confidence": "medium",
                }
            ]
        }
    )

    action: str
    # true/false only when an explicit, keyword-matched prohibition or
    # permission statement was found; null ("unclear") whenever the corpus
    # doesn't say so plainly - silence is not evidence of legality, so this
    # never guesses to force a boolean.
    allowed: bool | None = Field(description="true/false only when an explicit statement was found in the corpus; null ('unclear') when nothing relevant was found - never a guess from silence.")
    conditions: list[str] = Field(description="Caveats or related provisions found in the same section, even when not directly blocking the requested action (e.g. the rooster prohibition surfaced as a condition on an otherwise-allowed 'keep chickens' query).")
    citations: list[ActionCitation]
    reasoning: str = Field(description="Mechanical explanation of the determination - always read this before repeating `allowed` as a legal conclusion (see SKILL.md Rule 7).")
    confidence: str = Field(description="'high' (explicit, decisively top-ranked statement), 'medium' (explicit statement with ambiguous ranking, or an absence-of-restriction inference), or 'low' (nothing relevant found).")

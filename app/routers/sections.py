from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.db import LAWS_COLLECTION, get_db
from app.models import RelatedLawsResponse, RelatedSection, SectionOut
from app.section_lookup import get_section_chunks
from app.text_structure import split_subsections

router = APIRouter()


@router.get(
    "/sections/{section_number}",
    response_model=SectionOut,
    tags=["Lookup"],
    summary="Exact section lookup by number",
    description=(
        "Look up one statute section by its exact number (e.g. `161.19` or `24-222`) - not a Mongo "
        "document id. Returns the full, untruncated `text`, complete metadata, and a deterministic "
        "`structural_summary` (one bullet per lettered/numbered subsection, produced by splitting "
        "the real text on sentence boundaries - never an AI-generated summary).\n\n"
        "**When to call this**: after `/search`/`/penalties`/`/permits` surface a section_number you "
        "need the full text for, or when the user already names a specific section. Returns `404` if "
        "the section number doesn't exist in the corpus."
    ),
)
def get_section(section_number: str, db: Database = Depends(get_db)) -> SectionOut:
    chunks = get_section_chunks(db, section_number)
    if not chunks:
        raise HTTPException(status_code=404, detail="section not found")

    first = chunks[0]
    full_text = " ".join(c["text"] for c in chunks)
    keywords = sorted({kw for c in chunks for kw in c["keywords"]})
    cross_references = sorted({ref for c in chunks for ref in c["cross_references"]})

    return SectionOut(
        section_number=first["section_number"],
        section_title=first["section_title"],
        text=full_text,
        url=first["url"],
        document_type=first["document_type"],
        agency=first["agency"],
        topic=first["topic"],
        jurisdiction=first["jurisdiction"],
        keywords=keywords,
        cross_references=cross_references,
        mentions_penalty=any(c["mentions_penalty"] for c in chunks),
        mentions_permit=any(c["mentions_permit"] for c in chunks),
        effective_date=first["effective_date"],
        repealed=any(c["repealed"] for c in chunks),
        structural_summary=split_subsections(full_text),
        chunk_count=len(chunks),
        reasoning=(
            f"exact lookup by section_number={section_number!r}; structural_summary derived by "
            "splitting text on sentence-bounded lettered/numbered subsection markers; no query "
            "scoring involved"
        ),
    )


@router.get(
    "/sections/{section_number}/related",
    response_model=RelatedLawsResponse,
    tags=["Cross References"],
    summary="Resolve a section's cross-references into their own citations",
    description=(
        "Resolves the section's `cross_references` (other section_numbers it mentions by §-prefixed "
        "citation, extracted at ingestion time) into their own citations - a one-hop citation graph, "
        "no graph database required.\n\n"
        "**When to call this**: after `/sections/{section_number}` if the user needs related context "
        "the main section only references. A reference to a section outside the ingested corpus is "
        "still listed, with `resolved: false` - a gap is shown, never hidden. Returns `404` if the "
        "section number itself doesn't exist."
    ),
)
def get_related_laws(section_number: str, db: Database = Depends(get_db)) -> RelatedLawsResponse:
    chunks = get_section_chunks(db, section_number)
    if not chunks:
        raise HTTPException(status_code=404, detail="section not found")

    cross_references = sorted({ref for c in chunks for ref in c["cross_references"]})

    related: list[RelatedSection] = []
    resolved_count = 0
    for ref in cross_references:
        target = db[LAWS_COLLECTION].find_one({"type": "chunk", "section_number": ref, "chunk_index": 0})
        if target is None:
            related.append(RelatedSection(section_number=ref, resolved=False))
            continue
        resolved_count += 1
        related.append(
            RelatedSection(
                section_number=ref,
                section_title=target["section_title"],
                url=target["url"],
                document_type=target["document_type"],
                resolved=True,
            )
        )

    return RelatedLawsResponse(
        section_number=section_number,
        related=related,
        reasoning=(
            f"extracted {len(cross_references)} cross-reference(s) from §{section_number}'s body text "
            f"via regex; {resolved_count} of {len(cross_references)} resolved against the ingested corpus"
        ),
    )

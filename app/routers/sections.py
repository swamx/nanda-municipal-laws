from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.db import LAWS_COLLECTION, get_db
from app.models import RelatedLawsResponse, RelatedSection, SectionOut
from app.section_lookup import get_section_chunks
from app.text_structure import split_subsections

router = APIRouter(tags=["sections"])


@router.get("/sections/{section_number}", response_model=SectionOut)
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


@router.get("/sections/{section_number}/related", response_model=RelatedLawsResponse)
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

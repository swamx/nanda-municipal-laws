import bisect
import re

from app.ingestion.parser import SectionChunk, SourceMetadata

HEALTH_CODE_AGENCY = "Department of Health and Mental Hygiene (DOHMH)"

_ARTICLE_RE = re.compile(r"ARTICLE\s+(\d+)\s*\n\s*([A-Z][A-Z \-]+)\s*\n")

# Matches a section heading ("§161.19  Title spanning\nup to two lines.") at the
# start of a line. Titles may wrap across a couple of lines in the source PDF
# (confirmed against a real fetched Health Code article), so the title group
# allows up to two full lines before the sentence-ending period.
_HEADING_RE = re.compile(r"(?:^|\n)§(\d+\.\d+)\s\s+((?:[^\n]*\n){0,2}?[^\n]*?\.)\s*\n", re.MULTILINE)


def _parse_article_metadata(text: str) -> SourceMetadata:
    match = _ARTICLE_RE.search(text)
    if not match:
        raise ValueError("could not parse article header from PDF text")

    article_num = match.group(1)
    article_name = match.group(2).strip()

    return SourceMetadata(
        document_type="NYC Health Code",
        agency=HEALTH_CODE_AGENCY,
        topic=article_name,
        article_num=article_num,
        article_name=article_name,
    )


def _page_for_offset(offset: int, page_offsets: list[int]) -> int:
    return bisect.bisect_right(page_offsets, offset)


def _parse_sections(text: str, page_offsets: list[int]) -> list[SectionChunk]:
    """Finds every '§X.XX  Title.' heading. Each heading appears twice in a
    Health Code article PDF: once in the table of contents (immediately
    followed by the next heading, i.e. an empty body span) and once as the
    real section (followed by substantial body text before the next heading).
    Keeping only non-empty spans discards the TOC without hardcoding "first
    half is TOC" - verified against a real fetched article (16 sections, 32
    heading matches, first 16 empty, last 16 substantial).
    """
    matches = list(_HEADING_RE.finditer(text))
    chunks: list[SectionChunk] = []

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = re.sub(r"\s+", " ", text[start:end]).strip()
        if not body:
            continue  # table-of-contents entry, no body

        section_number = match.group(1)
        title = re.sub(r"\s+", " ", match.group(2)).strip().rstrip(".")
        page_number = _page_for_offset(match.start(), page_offsets)

        chunks.append(
            SectionChunk(
                section_number=section_number,
                section_title=title,
                text=f"§{section_number} {title}. {body}",
                anchor_id=f"page={page_number}",
            )
        )

    return chunks


def parse_health_code(pages: list[str], url: str) -> tuple[SourceMetadata, list[SectionChunk]]:
    page_offsets: list[int] = []
    full_text = ""
    for page_text in pages:
        page_offsets.append(len(full_text))
        full_text += page_text + "\n"

    metadata = _parse_article_metadata(full_text)
    sections = _parse_sections(full_text, page_offsets)
    return metadata, sections

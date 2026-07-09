import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

_SECTION_ID_RE = re.compile(r"^section-([\w]+-[\w.]+)$")
_HEADER_RE = re.compile(r"^\s*§\s*[\w\-.]+\s+(?P<title>.+?)\.\s*(?P<body>.*)$", re.DOTALL)
_BREADCRUMB_RE = re.compile(r"^(Title|Chapter|Subchapter)\s+([\w-]+)\s*-\s*(.+)$")

ADMIN_CODE_AGENCY = "Department of Environmental Protection (DEP)"


@dataclass
class SectionChunk:
    section_number: str
    section_title: str
    text: str
    anchor_id: str


@dataclass
class SourceMetadata:
    """Common metadata shape produced by every ingestion loader (HTML admin
    code, PDF health code, ...), so app/ingestion/pipeline.py can persist a
    document record without caring which loader ran.
    """

    document_type: str
    agency: str
    topic: str
    title_num: str | None = None
    title_name: str | None = None
    chapter_num: str | None = None
    chapter_name: str | None = None
    subchapter_num: str | None = None
    subchapter_name: str | None = None
    article_num: str | None = None
    article_name: str | None = None


def parse_metadata(soup: BeautifulSoup) -> SourceMetadata:
    title_num = title_name = chapter_num = chapter_name = None
    subchapter_num = subchapter_name = None

    for li in soup.select("ol.breadcrumb li"):
        match = _BREADCRUMB_RE.match(li.get_text(strip=True))
        if not match:
            continue
        kind, num, name = match.groups()
        if kind == "Title":
            title_num, title_name = num, name
        elif kind == "Chapter":
            chapter_num, chapter_name = num, name
        elif kind == "Subchapter":
            subchapter_num, subchapter_name = num, name

    if not title_num or not chapter_num:
        raise ValueError("could not parse title/chapter breadcrumb metadata from page")

    return SourceMetadata(
        document_type="NYC Administrative Code",
        agency=ADMIN_CODE_AGENCY,
        topic=chapter_name or chapter_num,
        title_num=title_num,
        title_name=title_name,
        chapter_num=chapter_num,
        chapter_name=chapter_name,
        subchapter_num=subchapter_num,
        subchapter_name=subchapter_name,
    )


def parse_sections(soup: BeautifulSoup) -> list[SectionChunk]:
    chunks: list[SectionChunk] = []

    for div in soup.find_all("div", class_="section"):
        div_id = div.get("id", "")
        match = _SECTION_ID_RE.match(div_id)
        if not match:
            continue

        pre = div.find("pre")
        if pre is None:
            continue

        normalized = re.sub(r"\s+", " ", pre.get_text()).strip()
        header_match = _HEADER_RE.match(normalized)
        title = header_match.group("title").strip() if header_match else ""

        chunks.append(
            SectionChunk(
                section_number=match.group(1),
                section_title=title,
                text=normalized,
                anchor_id=div_id,
            )
        )

    return chunks


def parse_page(html: str) -> tuple[SourceMetadata, list[SectionChunk]]:
    soup = BeautifulSoup(html, "html.parser")
    return parse_metadata(soup), parse_sections(soup)

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

_SECTION_ID_RE = re.compile(r"^section-([\w]+-[\w.]+)$")
_HEADER_RE = re.compile(r"^\s*§\s*[\w\-.]+\s+(?P<title>.+?)\.\s*(?P<body>.*)$", re.DOTALL)
_BREADCRUMB_RE = re.compile(r"^(Title|Chapter|Subchapter)\s+([\w-]+)\s*-\s*(.+)$")


@dataclass
class SectionChunk:
    section_number: str
    section_title: str
    text: str
    anchor_id: str


@dataclass
class PageMetadata:
    title_num: str
    title_name: str | None
    chapter_num: str
    chapter_name: str | None
    subchapter_num: str | None
    subchapter_name: str | None


def parse_metadata(soup: BeautifulSoup) -> PageMetadata:
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

    return PageMetadata(title_num, title_name, chapter_num, chapter_name, subchapter_num, subchapter_name)


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


def parse_page(html: str) -> tuple[PageMetadata, list[SectionChunk]]:
    soup = BeautifulSoup(html, "html.parser")
    return parse_metadata(soup), parse_sections(soup)

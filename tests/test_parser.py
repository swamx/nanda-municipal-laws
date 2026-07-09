from pathlib import Path

from app.ingestion.parser import parse_page

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "t24_c02_sch04.html"
FIXTURE_URL = "https://nycadmincode.readthedocs.io/t24/c02/sch04/"


def test_parse_page_extracts_metadata_and_sections():
    html = FIXTURE_PATH.read_text(encoding="utf-8")

    metadata, sections = parse_page(html)

    assert metadata.title_num == "24"
    assert "ENVIRONMENTAL PROTECTION" in metadata.title_name
    assert metadata.chapter_num == "2"
    assert "NOISE CONTROL" in metadata.chapter_name
    assert metadata.subchapter_num == "4"
    assert "CONSTRUCTION NOISE MANAGEMENT" in metadata.subchapter_name

    assert len(sections) >= 6

    section_222 = next(s for s in sections if s.section_number == "24-222")
    assert "construction" in section_222.section_title.lower()
    assert "7 a.m." in section_222.text
    assert section_222.anchor_id == "section-24-222"

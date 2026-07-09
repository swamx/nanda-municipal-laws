from pathlib import Path

from app.ingestion.health_code_parser import parse_health_code

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "health_code_article161.txt"
FIXTURE_URL = "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf"


def _pages() -> list[str]:
    # The fixture was dumped with a page-break marker between real PDF pages,
    # mirroring what fetch_pdf_pages() would return as list[str].
    return FIXTURE_PATH.read_text(encoding="utf-8").split("\n\n===PAGE BREAK===\n\n")


def test_parse_health_code_extracts_article_metadata():
    metadata, _ = parse_health_code(_pages(), FIXTURE_URL)

    assert metadata.document_type == "NYC Health Code"
    assert metadata.article_num == "161"
    assert metadata.article_name == "ANIMALS"
    assert metadata.topic == "ANIMALS"
    assert metadata.agency == "Department of Health and Mental Hygiene (DOHMH)"


def test_parse_health_code_finds_all_real_sections_and_skips_toc():
    _, sections = parse_health_code(_pages(), FIXTURE_URL)

    section_numbers = [s.section_number for s in sections]
    assert len(section_numbers) == len(set(section_numbers)) == 16  # no TOC duplicates
    assert "161.19" in section_numbers
    assert "161.17" in section_numbers  # title wraps across two lines in the source


def test_parse_health_code_section_161_19_matches_real_text():
    _, sections = parse_health_code(_pages(), FIXTURE_URL)
    section = next(s for s in sections if s.section_number == "161.19")

    assert section.section_title == "Keeping of livestock, live poultry and rabbits"
    assert "rooster" in section.text.lower()
    assert "duck" in section.text.lower()
    # The real text never states a numeric hen limit - guard against ever
    # fabricating the common "max 6 hens" internet myth into our own data.
    assert "6 hens" not in section.text.lower()
    assert "maximum" not in section.text.lower()
    assert section.anchor_id.startswith("page=")


def test_parse_health_code_section_161_17_title_reassembled_from_wrapped_lines():
    _, sections = parse_health_code(_pages(), FIXTURE_URL)
    section = next(s for s in sections if s.section_number == "161.17")

    assert "physical" in section.section_title.lower()
    assert "facilities and maintenance" in section.section_title.lower()

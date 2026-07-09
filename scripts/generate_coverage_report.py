"""Generates docs/COVERAGE.md directly from the current MongoDB contents -
a manifest of every document ingested, not a hand-maintained list, so it
can't drift out of sync with what's actually in the database.

Usage (from the repo root, with MONGO_ATLAS_CONN_STR set):
    python -m scripts.generate_coverage_report
"""

from datetime import datetime, timezone
from pathlib import Path

from app.db import LAWS_COLLECTION, get_db

OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "COVERAGE.md"


def _sort_key(value: str | None) -> tuple[int, str]:
    """Sorts numeric-looking values ("2", "24") in numeric order and mixed
    values ("16-A", "20-A") after them in natural string order - always
    returns a (bucket, str) tuple so mixed types never get compared directly.
    """
    if value is None:
        return (2, "")
    try:
        return (0, f"{int(value):06d}")
    except ValueError:
        return (1, str(value))


def _admin_code_section(documents: list[dict]) -> str:
    lines = ["## NYC Administrative Code", ""]

    by_title: dict[str, list[dict]] = {}
    for doc in documents:
        by_title.setdefault(doc.get("title_num") or "?", []).append(doc)

    total_titles = len(by_title)
    total_chapters = len({(d.get("title_num"), d.get("chapter_num")) for d in documents})
    total_sections = sum(d.get("section_count", 0) for d in documents)
    lines.append(
        f"**{total_titles} titles, {total_chapters} chapters, {len(documents)} ingested pages, "
        f"{total_sections} sections total.**"
    )
    lines.append("")
    lines.append("| Title | Chapter | Subchapter | Sections | Source |")
    lines.append("|---|---|---|---|---|")

    for title_num in sorted(by_title, key=_sort_key):
        docs = by_title[title_num]
        title_name = next((d.get("title_name") for d in docs if d.get("title_name")), "")
        docs_sorted = sorted(
            docs, key=lambda d: (_sort_key(d.get("chapter_num")), _sort_key(d.get("subchapter_num")))
        )
        for i, doc in enumerate(docs_sorted):
            title_cell = f"Title {title_num} - {title_name}" if i == 0 else ""
            chapter_num = doc.get("chapter_num") or ""
            chapter_name = doc.get("chapter_name") or ""
            chapter_cell = f"Ch. {chapter_num} - {chapter_name}" if chapter_name else f"Ch. {chapter_num}"
            subchapter_num = doc.get("subchapter_num")
            subchapter_name = doc.get("subchapter_name") or ""
            subchapter_cell = f"Sch. {subchapter_num} - {subchapter_name}" if subchapter_num else "(no subchapters)"
            source_cell = f"[link]({doc['source_url']})"
            lines.append(
                f"| {title_cell} | {chapter_cell} | {subchapter_cell} | {doc.get('section_count', 0)} | {source_cell} |"
            )

    return "\n".join(lines)


def _health_code_section(documents: list[dict]) -> str:
    lines = ["## NYC Health Code", ""]

    total_sections = sum(d.get("section_count", 0) for d in documents)
    lines.append(f"**{len(documents)} articles ingested, {total_sections} sections total.**")
    lines.append("")
    lines.append("| Article | Name | Sections | Source |")
    lines.append("|---|---|---|---|")

    docs_sorted = sorted(documents, key=lambda d: _sort_key(d.get("article_num")))
    for doc in docs_sorted:
        article_num = doc.get("article_num") or "?"
        article_name = doc.get("article_name") or ""
        source_cell = f"[link]({doc['source_url']})"
        lines.append(f"| {article_num} | {article_name} | {doc.get('section_count', 0)} | {source_cell} |")

    return "\n".join(lines)


def generate_report() -> str:
    db = get_db()
    laws = db[LAWS_COLLECTION]

    all_documents = list(laws.find({"type": "document"}))
    admin_code_docs = [d for d in all_documents if d.get("document_type") == "NYC Administrative Code"]
    health_code_docs = [d for d in all_documents if d.get("document_type") == "NYC Health Code"]

    total_chunks = laws.count_documents({"type": "chunk"})
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    parts = [
        "# Ingested Content Coverage",
        "",
        f"Generated {generated_at} directly from the live `mithackathon.dl-laws` MongoDB collection "
        "by `scripts/generate_coverage_report.py` - this file reflects what's actually ingested, not a "
        "hand-maintained plan.",
        "",
        f"**Totals: {len(all_documents)} source documents, {total_chunks} chunks "
        f"({len(admin_code_docs)} NYC Admin Code pages, {len(health_code_docs)} NYC Health Code articles).**",
        "",
        _admin_code_section(admin_code_docs),
        "",
        _health_code_section(health_code_docs),
        "",
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    report = generate_report()
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")

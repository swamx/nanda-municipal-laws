from typing import Protocol

from app.ingestion.parser import SectionChunk, SourceMetadata


class SourceLoader(Protocol):
    def load(self, url: str) -> tuple[SourceMetadata, list[SectionChunk]]: ...


class HtmlAdminCodeLoader:
    def load(self, url: str) -> tuple[SourceMetadata, list[SectionChunk]]:
        from app.ingestion.fetcher import fetch_page
        from app.ingestion.parser import parse_page

        return parse_page(fetch_page(url))


class PdfHealthCodeLoader:
    def load(self, url: str) -> tuple[SourceMetadata, list[SectionChunk]]:
        from app.ingestion.health_code_parser import parse_health_code
        from app.ingestion.pdf_fetcher import fetch_pdf_pages

        return parse_health_code(fetch_pdf_pages(url), url)


def select_loader(url: str) -> SourceLoader:
    return PdfHealthCodeLoader() if url.lower().endswith(".pdf") else HtmlAdminCodeLoader()

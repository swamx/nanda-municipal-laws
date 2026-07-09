import io

import httpx
from pypdf import PdfReader

# nyc.gov returns 403 for non-browser-looking User-Agent strings (confirmed:
# our default "municipal-bylaws-api/0.1" UA was blocked, a browser UA wasn't).
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_pdf_pages(url: str, timeout: float = 15.0, retries: int = 2) -> list[str]:
    """Fetch a PDF and return its extracted text, one string per page."""
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = httpx.get(url, timeout=timeout, headers={"User-Agent": _USER_AGENT}, follow_redirects=True)
            response.raise_for_status()
            reader = PdfReader(io.BytesIO(response.content))
            return [page.extract_text() or "" for page in reader.pages]
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            last_error = exc
    raise RuntimeError(f"failed to fetch {url} after {retries + 1} attempts") from last_error

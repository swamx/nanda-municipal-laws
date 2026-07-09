import httpx

_USER_AGENT = "municipal-bylaws-api/0.1 (+https://github.com/)"


def fetch_page(url: str, timeout: float = 10.0, retries: int = 2) -> str:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = httpx.get(url, timeout=timeout, headers={"User-Agent": _USER_AGENT}, follow_redirects=True)
            response.raise_for_status()
            return response.text
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            last_error = exc
    raise RuntimeError(f"failed to fetch {url} after {retries + 1} attempts") from last_error

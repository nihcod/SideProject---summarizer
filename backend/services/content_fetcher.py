from __future__ import annotations

import re
from typing import List, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36"
)

ALT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
)

BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

FALLBACK_HEADERS = {
    **BASE_HEADERS,
    "User-Agent": ALT_USER_AGENT,
    "Referer": "https://www.google.com/",
}


def normalize_url(raw_url: str) -> str:
    raw_url = (raw_url or "").strip()
    if not raw_url:
        raise ValueError("URL이 비어 있습니다.")
    parsed = urlparse(raw_url)
    if not parsed.scheme:
        return f"https://{raw_url}"
    return raw_url


def fetch_webpage(url: str, timeout: int = 8) -> Tuple[str, str, str, str]:
    """Return title, clean text, final_url, and raw html for the page."""
    normalized = normalize_url(url)
    attempts: List[Tuple[str, dict]] = [
        (normalized, BASE_HEADERS),
    ]

    if normalized.startswith("https://"):
        attempts.append((normalized.replace("https://", "http://", 1), BASE_HEADERS))

    attempts.append((normalized, FALLBACK_HEADERS))

    last_exc: Exception | None = None
    response: requests.Response | None = None
    for candidate_url, headers in attempts:
        try:
            response = requests.get(
                candidate_url,
                timeout=(5, timeout),
                headers=headers,
                allow_redirects=True,
            )
            if response.status_code >= 500:
                response.raise_for_status()
            if response.status_code == 403:
                # Try next header set
                response = None
                continue
            response.raise_for_status()
            break
        except requests.RequestException as exc:
            last_exc = exc
            response = None
            continue

    if response is None:
        detail = f"{last_exc}" if last_exc else "알 수 없는 오류"
        raise ValueError(f"웹 페이지를 불러오지 못했습니다: {detail}")

    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "iframe", "form", "footer", "nav"]):
        tag.decompose()

    paragraphs = [collapse_spaces(el.get_text(" ", strip=True)) for el in soup.find_all(["p", "h1", "h2", "h3"])]
    text = "\n".join([p for p in paragraphs if len(p) > 40])
    text = text[:5000]  # guardrail for prompt size
    title = soup.title.get_text(strip=True) if soup.title else url
    final_url = response.url
    return title, text, final_url, html


def collapse_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

from __future__ import annotations

from typing import Dict, Tuple

import requests

from .content_fetcher import fetch_webpage
from .perplexity_client import PerplexityClient


def summarize_url(url: str, client: PerplexityClient) -> Tuple[str, Dict]:
    title, text, final_url, _ = fetch_webpage(url)
    if not text:
        raise ValueError("콘텐츠를 추출하지 못했습니다. 다른 URL을 시도해 주세요.")
    used_fallback = False
    fallback_reason = None
    citations = []
    try:
        summary, citations = client.summarize_webpage(title, text)
    except requests.HTTPError as exc:
        fallback_reason = _describe_http_error(exc)
        summary = local_summary_fallback(title, text)
        used_fallback = True
    except requests.RequestException as exc:
        fallback_reason = f"Perplexity API 네트워크 오류: {exc}"
        summary = local_summary_fallback(title, text)
        used_fallback = True
    payload = {
        "summary": summary,
        "citations": citations,
        "sourceTitle": title,
        "sourceUrl": final_url,
        "usedFallback": used_fallback,
        "fallbackReason": fallback_reason,
    }
    return summary, payload


def local_summary_fallback(title: str, text: str) -> str:
    paragraphs = [line.strip() for line in text.split("\n") if line.strip()]
    snippet = "\n".join(paragraphs[:5])
    if not snippet:
        snippet = text[:500]
    return (
        f"[로컬 요약] Perplexity API와 통신하지 못해 단순 요약을 제공합니다.\n"
        f"제목: {title}\n\n"
        f"{snippet}"
    )


def _describe_http_error(exc: requests.HTTPError) -> str:
    response = getattr(exc, "response", None)
    if response is not None:
        status = f"{response.status_code} {response.reason}"
        try:
            payload = response.json()
            message = payload.get("error") if isinstance(payload, dict) else None
        except ValueError:
            message = response.text[:200]
        detail = message or response.text[:200] or "응답 본문이 비어 있습니다."
        return f"{status}: {detail}"
    return f"Perplexity API 오류: {exc}"

from __future__ import annotations

import re
from typing import List, Optional, Tuple

import wikipedia

from .perplexity_client import PerplexityClient


KOREAN_REGEX = re.compile(r"[\u3130-\u318F\uAC00-\uD7A3]")

CURATED_RESOURCES = [
    {
        "title": "OWASP Top 10",
        "summary": "OWASP 재단이 정리한 최신 웹 취약점 순위와 완화 전략을 확인할 수 있습니다.",
        "url": "https://owasp.org/Top10/",
        "via": "curated",
    },
    {
        "title": "MITRE ATT&CK",
        "summary": "공격 기법·탐지·대응 전략을 망라한 MITRE ATT&CK 지식베이스입니다.",
        "url": "https://attack.mitre.org/",
        "via": "curated",
    },
    {
        "title": "Google Scholar",
        "summary": "키워드로 최신 학술 논문과 특허를 검색할 수 있는 Google Scholar 링크입니다.",
        "url": "https://scholar.google.com/",
        "via": "curated",
    },
]


def research_by_keywords(
    keywords: List[str],
    client: Optional[PerplexityClient],
    client_error: Optional[str] = None,
) -> Tuple[List[dict], dict]:
    query = ", ".join(kw.strip() for kw in keywords if kw.strip())
    if not query:
        raise ValueError("키워드가 비어 있습니다.")

    used_fallback = False
    fallback_reason = None
    resources: List[dict] = []

    if client is None:
        used_fallback = True
        fallback_reason = client_error or "Perplexity API를 사용할 수 없습니다."
        resources = fallback_resources(query)
    else:
        try:
            resources = client.research_resources(query)
            resources = [_attach_source(item, "perplexity") for item in resources]
        except Exception as exc:  # pylint: disable=broad-except
            used_fallback = True
            fallback_reason = f"Perplexity 호출 실패: {exc}"
            resources = fallback_resources(query)

    meta = {"usedFallback": used_fallback, "fallbackReason": fallback_reason}
    return resources, meta


def fallback_resources(query: str, limit: int = 3) -> List[dict]:
    lang = "ko" if KOREAN_REGEX.search(query) else "en"
    wikipedia.set_lang(lang)
    entries = []
    for title in wikipedia.search(query)[:limit]:
        try:
            summary = wikipedia.summary(title, sentences=2)
        except wikipedia.exceptions.DisambiguationError as exc:
            summary = f"관련 문서가 많습니다: {', '.join(exc.options[:3])}"
        except wikipedia.exceptions.PageError:
            summary = "문서를 찾을 수 없습니다."
        entries.append(
            {
                "title": title,
                "summary": summary,
                "url": f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}",
            }
        )

    if not entries:
        entries = [
            {
                **item,
                "summary": f"{item['summary']} (검색어: {query})",
            }
            for item in CURATED_RESOURCES
        ]

    tagged_entries = [
        _attach_source(item, "wikipedia" if "wikipedia.org" in (item.get("url") or "") else item.get("via", "curated"))
        for item in entries
    ]
    return tagged_entries


def _attach_source(item: dict, source: str) -> dict:
    if "via" in item and item["via"]:
        return item
    return {**item, "via": source}

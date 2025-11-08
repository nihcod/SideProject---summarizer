from __future__ import annotations

import wikipedia


def summarize_keyword(keyword: str, lang: str = "ko", max_sentences: int = 5) -> dict:
    wikipedia.set_lang(lang)
    try:
        summary = wikipedia.summary(keyword, sentences=max_sentences)
        page = wikipedia.page(keyword, auto_suggest=False)
        return {
            "summary": summary,
            "url": page.url,
            "options": [],
            "message": None,
        }
    except wikipedia.exceptions.DisambiguationError as exc:
        options = exc.options[:5]
        return _build_result(message="검색어가 모호합니다. 아래 후보 중 선택해 주세요.", options=options)
    except wikipedia.exceptions.PageError:
        return _build_result(message="해당 검색어에 대한 문서를 찾지 못했습니다.")
    except Exception as exc:  # pylint: disable=broad-except
        return _build_result(message=f"알 수 없는 오류가 발생했습니다: {exc}")


def force_summary(keyword: str, lang: str = "ko") -> dict:
    wikipedia.set_lang(lang)
    try:
        summary = wikipedia.summary(keyword, sentences=5, auto_suggest=False)
        page = wikipedia.page(keyword, auto_suggest=False)
        return _build_result(summary=summary, url=page.url)
    except wikipedia.exceptions.DisambiguationError as exc:
        resolved = _resolve_disambiguation(exc.options, lang)
        if resolved:
            return resolved
        return _build_result(message="여전히 모호한 용어입니다. 아래에서 다시 선택해 주세요.", options=exc.options[:5])
    except wikipedia.exceptions.PageError:
        # fall back to best-effort search results
        return _search_fallback(keyword, lang)
    except Exception as exc:  # pylint: disable=broad-except
        return _build_result(message=f"요약 중 오류가 발생했습니다: {exc}")


def _search_fallback(keyword: str, lang: str) -> dict:
    search_results = wikipedia.search(keyword)
    for title in search_results:
        try:
            summary = wikipedia.summary(title, sentences=5)
            page = wikipedia.page(title)
            return _build_result(summary=summary, url=page.url)
        except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
            continue
    return _build_result(message="다른 키워드로 시도해 주세요.")


def _build_result(summary: str | None = None, url: str | None = None, options=None, message: str | None = None) -> dict:
    return {
        "summary": summary,
        "url": url,
        "options": options or [],
        "message": message,
    }


def _resolve_disambiguation(options: list[str], lang: str, depth: int = 0) -> dict | None:
    if depth > 3:
        return None
    wikipedia.set_lang(lang)
    for candidate in options:
        try:
            summary = wikipedia.summary(candidate, sentences=5)
            page = wikipedia.page(candidate)
            return _build_result(summary=summary, url=page.url)
        except wikipedia.exceptions.DisambiguationError as inner_exc:
            # keep drilling down with the narrowed options
            deeper = _resolve_disambiguation(inner_exc.options[:5], lang, depth + 1)
            if deeper:
                return deeper
        except wikipedia.exceptions.PageError:
            continue
    return None

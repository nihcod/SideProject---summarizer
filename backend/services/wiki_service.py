from __future__ import annotations

from urllib.parse import quote

import wikipedia


PREFERRED_KEYWORDS = {
    "배": ["과일", "fruit", "나무", "식물", "선박", "동음이의어"],
}


def summarize_keyword(keyword: str, lang: str = "ko", max_sentences: int = 8) -> dict | str:
    wikipedia.set_lang(lang)
    try:
        summary = wikipedia.summary(keyword, sentences=max_sentences, auto_suggest=False)
        return summary
    except wikipedia.exceptions.DisambiguationError:
        summary, _ = force_summary(keyword, lang, max_sentences)
        return summary
    except wikipedia.exceptions.PageError:
        return "검색 결과가 없습니다."
    except Exception as exc:  # pylint: disable=broad-except
        return f"알 수 없는 오류가 발생 하였습니다.: {exc}"


def force_summary(keyword: str, lang: str = "ko", max_sentences: int = 8) -> tuple[str, str | None]:
    wikipedia.set_lang(lang)
    ordered = _prioritize_options(wikipedia.search(keyword), target=keyword)
    for title in ordered:
        try:
            summary = wikipedia.summary(title, sentences=max_sentences, auto_suggest=False)
            link = f"https://{lang}.wikipedia.org/wiki/{quote(title)}"
            return summary, link
        except wikipedia.exceptions.DisambiguationError as exc:
            preferred = _pick_best_candidate(keyword, exc.options)
            if preferred:
                try:
                    summary = wikipedia.summary(preferred, sentences=max_sentences, auto_suggest=False)
                    link = f"https://{lang}.wikipedia.org/wiki/{quote(preferred)}"
                    return summary, link
                except Exception:
                    continue
            continue
        except wikipedia.exceptions.PageError:
            continue
        except Exception as exc:  # pylint: disable=broad-except
            return f"알 수 없는 오류 발생: {exc}", None
    return "항목을 찾을 수 없습니다.", None


def original_link(keyword: str, lang: str = "ko") -> str | None:
    try:
        wikipedia.set_lang(lang)
        wikipedia.page(keyword, auto_suggest=False)
        encoded = quote(keyword)
        return f"https://{lang}.wikipedia.org/wiki/{encoded}"
    except Exception:  # pragma: no cover - optional
        return None


def _pick_best_candidate(keyword: str, options: list[str]) -> str | None:
    prioritized = _prioritize_options(options, target=keyword)
    return prioritized[0] if prioritized else None


def _prioritize_options(options: list[str], target: str | None) -> list[str]:
    if not options:
        return []
    normalized_target = _normalize_title(target or "")
    hints = PREFERRED_KEYWORDS.get(target or "", [])

    def score(option: str) -> tuple[int, int]:
        option_norm = _normalize_title(option)
        if option_norm == normalized_target:
            return (0, 0)
        for idx, hint in enumerate(hints):
            if hint.lower() in option.lower():
                return (1, idx)
        if normalized_target and (option_norm.startswith(normalized_target) or normalized_target in option_norm):
            return (2, 0)
        if option.endswith("(동음이의어)"):
            return (3, 0)
        return (4, 0)

    ranked = sorted(((score(opt), opt) for opt in options), key=lambda pair: (pair[0][0], pair[0][1], pair[1]))
    return [opt for _, opt in ranked]


def _normalize_title(title: str) -> str:
    return "".join(ch for ch in (title or "").lower() if ch.isalnum())


def _dedup_options(options: list[str]) -> list[str]:
    seen = set()
    unique = []
    for option in options:
        normalized = _normalize_title(option)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(option)
    return unique

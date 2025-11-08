from __future__ import annotations

import logging
import re
from typing import List

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.config import settings
from backend.services.perplexity_client import PerplexityClient
from backend.services.search_service import research_by_keywords
from backend.services.url_service import summarize_url
from backend.services.wiki_service import force_summary, original_link, summarize_keyword


logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    perplexity_error = None
    client = None
    if settings.perplexity_enabled:
        try:
            client = PerplexityClient(
                api_key=settings.perplexity_api_key,
                model=settings.perplexity_model,
                temperature=settings.perplexity_temperature,
                timeout=settings.request_timeout,
            )
        except ValueError as exc:
            perplexity_error = str(exc)
            logger.warning("Perplexity 클라이언트 초기화 실패: %s", exc)
    else:
        perplexity_error = "; ".join(settings.validation_errors)

    app.config["perplexity_client"] = client
    app.config["perplexity_error"] = perplexity_error

    @app.get("/health")
    def health() -> tuple:
        client_ready = app.config["perplexity_client"] is not None
        return jsonify({"status": "ok", "perplexity": client_ready, "detail": app.config.get("perplexity_error")})

    @app.post("/api/summarize-url")
    def api_summarize_url():
        data = request.get_json(force=True, silent=True) or {}
        url = (data.get("url") or "").strip()
        if not url:
            return jsonify({"error": "URL을 입력해 주세요."}), 400
        client = app.config.get("perplexity_client")
        try:
            _, payload = summarize_url(url, client, app.config.get("perplexity_error"))
            return jsonify(payload)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except requests.RequestException as exc:
            logger.warning("URL fetch 실패: %s", exc)
            return jsonify({"error": "웹 페이지를 불러오지 못했습니다.", "detail": str(exc)}), 502
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("URL 요약 중 오류", exc_info=exc)
            return jsonify({"error": "요약 중 오류가 발생했습니다.", "detail": str(exc)}), 500

    @app.get("/api/wiki/search")
    def api_wiki_search():
        term = (request.args.get("term") or "").strip()
        lang = request.args.get("lang", "ko")
        if not term:
            return jsonify({"message": "검색어를 입력해 주세요."}), 400
        result = summarize_keyword(term, lang=lang)
        return jsonify(_normalize_wiki_response(result, term, lang))

    @app.get("/api/wiki/force")
    def api_wiki_force():
        term = (request.args.get("term") or "").strip()
        lang = request.args.get("lang", "ko")
        if not term:
            return jsonify({"message": "검색어를 입력해 주세요."}), 400
        summary, url = force_summary(term, lang=lang)
        return jsonify(
            {
                "summary": summary,
                "url": url,
                "options": None,
                "message": None if url else "다른 키워드를 시도해 주세요.",
            }
        )

    @app.post("/api/resources/search")
    def api_resource_search():
        data = request.get_json(force=True, silent=True) or {}
        keywords = normalize_keywords(data.get("keywords"))
        if not keywords:
            return jsonify({"error": "최소 한 개의 키워드를 입력해 주세요."}), 400
        client = app.config.get("perplexity_client")
        try:
            resources, meta = research_by_keywords(keywords, client, app.config.get("perplexity_error"))
            return jsonify({"results": resources, **meta})
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("키워드 탐색 실패", exc_info=exc)
            return jsonify({"error": "자료를 불러오지 못했습니다.", "detail": str(exc)}), 500

    return app


KEYWORD_SANITIZER = re.compile(r"[^0-9A-Za-z가-힣#\+\-\s]")


def normalize_keywords(raw_keywords) -> List[str]:
    tokens: List[str] = []
    if isinstance(raw_keywords, str):
        raw_items = raw_keywords.split(",")
    elif isinstance(raw_keywords, list):
        raw_items = raw_keywords
    else:
        raw_items = []

    for item in raw_items:
        token = str(item).strip()
        if not token:
            continue
        tokens.append(token)

    cleaned = []
    for token in tokens:
        normalized = KEYWORD_SANITIZER.sub(" ", token)
        normalized = " ".join(normalized.split())
        normalized = normalized.strip(" ,;/")
        if normalized:
            cleaned.append(normalized)
    return cleaned


def _normalize_wiki_response(result, keyword: str, lang: str) -> dict:
    if isinstance(result, dict) and result.get("disambiguation"):
        return {
            "summary": None,
            "url": None,
            "options": result.get("options", []),
            "message": result.get("message", "검색어가 모호합니다."),
        }

    summary = result if isinstance(result, str) else None
    url = None
    message = None
    if summary and not summary.startswith("검색 결과") and not summary.startswith("알 수"):
        try:
            url = original_link(keyword, lang)
        except Exception:
            url = None
    else:
        message = summary
        summary = None

    return {"summary": summary, "url": url, "options": None, "message": message}


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.backend_port, debug=True)

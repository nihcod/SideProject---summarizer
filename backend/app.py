from __future__ import annotations

import logging
from typing import List

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.config import settings
from backend.services.perplexity_client import PerplexityClient
from backend.services.search_service import research_by_keywords
from backend.services.url_service import summarize_url
from backend.services.wiki_service import force_summary, summarize_keyword


logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    try:
        app.config["perplexity_client"] = PerplexityClient(
            api_key=settings.perplexity_api_key,
            model=settings.perplexity_model,
            temperature=settings.perplexity_temperature,
            timeout=settings.request_timeout,
        )
    except ValueError as exc:
        logger.warning("Perplexity 클라이언트 초기화 실패: %s", exc)
        app.config["perplexity_client"] = None

    @app.get("/health")
    def health() -> tuple:
        client_ready = app.config["perplexity_client"] is not None
        return jsonify({"status": "ok", "perplexity": client_ready})

    @app.post("/api/summarize-url")
    def api_summarize_url():
        data = request.get_json(force=True, silent=True) or {}
        url = (data.get("url") or "").strip()
        if not url:
            return jsonify({"error": "URL을 입력해 주세요."}), 400
        client = app.config.get("perplexity_client")
        if client is None:
            return jsonify({"error": "Perplexity API 키가 설정되지 않았습니다."}), 500
        try:
            _, payload = summarize_url(url, client)
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
        return jsonify(result)

    @app.get("/api/wiki/force")
    def api_wiki_force():
        term = (request.args.get("term") or "").strip()
        lang = request.args.get("lang", "ko")
        if not term:
            return jsonify({"message": "검색어를 입력해 주세요."}), 400
        result = force_summary(term, lang=lang)
        return jsonify(result)

    @app.post("/api/resources/search")
    def api_resource_search():
        data = request.get_json(force=True, silent=True) or {}
        raw_keywords = data.get("keywords") or ""
        keywords: List[str]
        if isinstance(raw_keywords, str):
            keywords = [kw.strip() for kw in raw_keywords.split(",")]
        elif isinstance(raw_keywords, list):
            keywords = [str(kw).strip() for kw in raw_keywords]
        else:
            keywords = []
        keywords = [kw for kw in keywords if kw]
        if not keywords:
            return jsonify({"error": "최소 한 개의 키워드를 입력해 주세요."}), 400
        client = app.config.get("perplexity_client")
        if client is None:
            return jsonify({"error": "API 키가 설정되지 않았습니다."}), 500
        try:
            resources = research_by_keywords(keywords, client)
            return jsonify({"results": resources})
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("키워드 탐색 실패", exc_info=exc)
            return jsonify({"error": "자료를 불러오지 못했습니다.", "detail": str(exc)}), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.backend_port, debug=True)

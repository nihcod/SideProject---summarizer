from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Tuple

import requests

logger = logging.getLogger(__name__)


class PerplexityClient:
    """Lightweight wrapper around the Perplexity chat-completions API."""

    API_URL = "https://api.perplexity.ai/chat/completions"

    def __init__(self, api_key: str, model: str, temperature: float, timeout: int = 20) -> None:
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY가 설정되어 있지 않습니다.")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    def _post(self, messages: List[Dict[str, str]], **extra: Any) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            **extra,
        }
        response = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:  # pragma: no cover - network errors
            body = response.text[:500]
            raise requests.HTTPError(f"{exc}; body={body}", response=response) from exc
        return response.json()

    def summarize_webpage(self, title: str, text: str) -> Tuple[str, List[Dict[str, str]]]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a security-aware technical writer. Summaries must remove ads, "
                    "menus, and scripts, and highlight risks if the content looks suspicious."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"제목이 '{title}'인 웹페이지에서 추출한 본문입니다.\n"
                    "핵심 개념, 주요 경고, 실행 가능한 인사이트를 8줄 이내 bullet 형식으로 요약해 주세요.\n"
                    "본문:\n"
                    f"{text}"
                ),
            },
        ]
        data = self._post(messages, return_citations=True)
        choice = data["choices"][0]
        content = choice["message"]["content"].strip()
        citations = choice.get("citations") or []
        return content, citations

    def research_resources(self, keyword: str) -> List[Dict[str, str]]:
        prompt = (
            "You are a metasearch analyst. Return JSON with 3-5 helpful resources.\n"
            "JSON schema: [{\"title\": str, \"summary\": str, \"url\": str}]. "
            "Only include trustworthy official sources when possible.\n"
            f"Focus topic: {keyword}"
        )
        messages = [
            {"role": "system", "content": "You output valid JSON arrays only."},
            {"role": "user", "content": prompt},
        ]
        data = self._post(messages)
        text = data["choices"][0]["message"]["content"]
        return self._parse_json_array(text)

    def _parse_json_array(self, text: str) -> List[Dict[str, str]]:
        """Extract and parse a JSON array from the model response."""
        try:
            start = text.index("[")
            end = text.rindex("]") + 1
            array_text = text[start:end]
            parsed = json.loads(array_text)
            if isinstance(parsed, list):
                normalized = []
                for item in parsed:
                    if not isinstance(item, dict):
                        continue
                    normalized.append(
                        {
                            "title": str(item.get("title", "제목 없음")),
                            "summary": str(item.get("summary", "요약이 제공되지 않았습니다.")),
                            "url": str(item.get("url", "")),
                        }
                    )
                return normalized
        except (ValueError, json.JSONDecodeError) as exc:
            logger.warning("JSON 파싱에 실패했습니다: %s", exc)
        return [
            {
                "title": "결과를 불러오지 못했습니다",
                "summary": "Perplexity 응답 형식이 올바르지 않습니다. 다시 시도해 주세요.",
                "url": "",
            }
        ]

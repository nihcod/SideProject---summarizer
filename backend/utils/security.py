from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import List
from urllib.parse import urlparse


SUSPICIOUS_KEYWORDS = [
    "javascript:",
    "data:text/html",
    "onerror=",
    "document.cookie",
    "window.location",
]

SUSPICIOUS_TAGS = ("script", "iframe", "object", "embed", "form")


@dataclass
class SecurityFinding:
    name: str
    level: str
    detail: str


@dataclass
class SecurityReport:
    original_url: str
    final_url: str
    findings: List[SecurityFinding] = field(default_factory=list)

    @property
    def risk_score(self) -> int:
        levels = {"info": 1, "warning": 3, "critical": 5}
        return sum(levels.get(f.level, 1) for f in self.findings)

    def to_dict(self) -> dict:
        return {
            "originalUrl": self.original_url,
            "finalUrl": self.final_url,
            "riskScore": self.risk_score,
            "findings": [asdict(f) for f in self.findings],
        }


class SecurityScanner:
    """Light-weight heuristic scanner to flag suspicious characteristics in a URL response."""

    def __init__(self, original_url: str, final_url: str, html: str) -> None:
        self.original_url = original_url
        self.final_url = final_url
        self.html = html or ""
        self.report = SecurityReport(original_url=original_url, final_url=final_url)
        self.parsed = urlparse(final_url or original_url)

    def run_all(self) -> SecurityReport:
        self._check_scheme()
        self._check_ip_hostname()
        self._check_keyword_patterns()
        self._check_tag_density()
        return self.report

    def _add_finding(self, name: str, level: str, detail: str) -> None:
        self.report.findings.append(SecurityFinding(name=name, level=level, detail=detail))

    def _check_scheme(self) -> None:
        if self.parsed.scheme != "https":
            self._add_finding(
                name="Insecure protocol",
                level="warning",
                detail="연결이 HTTPS가 아니어서 중간자 공격에 취약할 수 있습니다.",
            )

    def _check_ip_hostname(self) -> None:
        host = self.parsed.hostname or ""
        if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
            self._add_finding(
                name="IP address host",
                level="warning",
                detail="도메인 대신 IP 주소를 바로 사용하고 있어 피싱 가능성을 확인하세요.",
            )

    def _check_keyword_patterns(self) -> None:
        lowered = self.html.lower()
        hits = [kw for kw in SUSPICIOUS_KEYWORDS if kw in lowered]
        if hits:
            self._add_finding(
                name="Suspicious markup",
                level="critical",
                detail=f"다음과 같은 잠재적으로 위험한 문자열이 발견되었습니다: {', '.join(hits)}",
            )

    def _check_tag_density(self) -> None:
        lowered = self.html.lower()
        counts = {tag: lowered.count(f"<{tag}") for tag in SUSPICIOUS_TAGS}
        flagged = {
            tag: count
            for tag, count in counts.items()
            if (tag == "script" and count >= 80) or (tag != "script" and count >= 5)
        }
        if flagged:
            detail = ", ".join(f"{tag}:{count}" for tag, count in flagged.items())
            self._add_finding(
                name="Embedded active content",
                level="warning",
                detail=f"다량의 활성 태그가 포함되어 있습니다 ({detail}).",
            )

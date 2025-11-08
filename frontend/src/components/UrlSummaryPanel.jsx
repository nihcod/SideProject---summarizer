import { useState } from "react";

export default function UrlSummaryPanel({ apiBase }) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!url) {
      setError("URL을 입력해 주세요.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${apiBase}/api/summarize-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "요약에 실패했습니다.");
      }
      setResult(data);
    } catch (err) {
      setError(err.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <article className="panel">
      <header className="panel__head">
        <h2>웹 페이지 요약</h2>
        <p>AI가 핵심 내용을 요약합니다.</p>
      </header>

      <form className="panel__form" onSubmit={handleSubmit}>
        <input
          type="url"
          placeholder="https://example.com/article"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "요약 중..." : "요약하기"}
        </button>
      </form>

      {error && <p className="panel__error">{error}</p>}

      {result && (
        <div className="panel__body">
          <article className="card">
            <header className="card__head">
              <div>
                <p className="card__eyebrow">요약 결과</p>
                <h3>{result.sourceTitle}</h3>
              </div>
              <a className="panel__link" href={result.sourceUrl} target="_blank" rel="noreferrer">
                원문 보기
              </a>
            </header>

            {result.usedFallback && (
              <p className="panel__note">
                Perplexity 호출이 실패하여 기본 요약으로 대체했습니다.
                {result.fallbackReason && <span className="panel__note-detail">{result.fallbackReason}</span>}
              </p>
            )}

            <pre className="panel__summary">{result.summary}</pre>

            {result.citations?.length ? (
              <div className="citation-list">
                <p>출처</p>
                <ul>
                  {result.citations.map((citation, idx) => (
                    <li key={`${citation.url}-${idx}`}>
                      <a href={citation.url || citation.metadata?.url} target="_blank" rel="noreferrer">
                        {citation.url || citation.metadata?.title || `출처 ${idx + 1}`}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </article>
        </div>
      )}
    </article>
  );
}

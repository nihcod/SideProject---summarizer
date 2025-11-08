import { useState } from "react";

export default function ResourcePanel({ apiBase }) {
  const [keywords, setKeywords] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState([]);
  const [meta, setMeta] = useState({ usedFallback: false, fallbackReason: "" });

  const handleSearch = async () => {
    if (!keywords.trim()) {
      setError("키워드를 입력해 주세요.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${apiBase}/api/resources/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keywords }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "자료 검색에 실패했습니다.");
      }
      setResults(data.results || []);
      setMeta({ usedFallback: Boolean(data.usedFallback), fallbackReason: data.fallbackReason || "" });
    } catch (err) {
      setError(err.message);
      setResults([]);
      setMeta({ usedFallback: false, fallbackReason: "" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <article className="panel">
      <header className="panel__head">
        <h2>키워드 리서치</h2>
        <p>AI가 신뢰할 만한 자료를 찾아 요약과 링크를 제공합니다.</p>
      </header>

      <div className="panel__form horizontal">
        <input
          type="text"
          placeholder="키워드를 입력하세요."
          value={keywords}
          onChange={(event) => setKeywords(event.target.value)}
        />
        <button type="button" onClick={handleSearch} disabled={loading}>
          {loading ? "탐색 중..." : "자료 찾기"}
        </button>
      </div>

      {error && <p className="panel__error">{error}</p>}

      {meta.usedFallback && meta.fallbackReason && (
        <p className="panel__note">
          Perplexity 응답을 받지 못해 대체 자료를 제공 중입니다.
          <span className="panel__note-detail">{meta.fallbackReason}</span>
        </p>
      )}

      {results.length > 0 && (
        <div className="resource-list">
          {results.map((item) => (
            <article key={item.url || item.title} className="resource-card">
              <div className="resource-card__meta">
                <h3>{item.title}</h3>
                {item.via && <span className={`tag tag--${item.via}`}>{item.via}</span>}
              </div>
              <p>{item.summary}</p>
              {item.url && (
                <a href={item.url} target="_blank" rel="noreferrer">
                  링크 열기
                </a>
              )}
            </article>
          ))}
        </div>
      )}

      {!results.length && !error && <p className="panel__note">키워드를 입력하면 관련 자료를 보여줍니다.</p>}
    </article>
  );
}

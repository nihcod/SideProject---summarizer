import { useState } from "react";

export default function WikipediaPanel({ apiBase }) {
  const [term, setTerm] = useState("");
  const [lang, setLang] = useState("ko");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const search = async (nextTerm, force = false) => {
    const actualTerm = (nextTerm ?? term).trim();
    if (!actualTerm) {
      setError("검색어를 입력해 주세요.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const endpoint = force ? "force" : "search";
      const url =
        apiBase +
        "/api/wiki/" +
        endpoint +
        "?term=" +
        encodeURIComponent(actualTerm) +
        "&lang=" +
        lang;
      const response = await fetch(url);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || data.error || "검색에 실패했습니다.");
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
        <h2>Wikipedia 검색</h2>
        <p>검색어에 대한 위키피디아 검색 결과를 제공합니다.</p>
      </header>

      <div className="panel__form horizontal">
        <input type="text" placeholder="검색어를 입력하세요." value={term} onChange={(event) => setTerm(event.target.value)} />
        <select value={lang} onChange={(event) => setLang(event.target.value)}>
          <option value="ko">한국어</option>
          <option value="en">English</option>
          <option value="ja">日本語</option>
        </select>
        <button type="button" onClick={() => search()} disabled={loading}>
          {loading ? "검색 중..." : "검색"}
        </button>
      </div>

      {error && <p className="panel__error">{error}</p>}

      {result && (
        <div className="panel__body">
          <article className="card">
            <header className="card__head">
              <div>
                <p className="card__eyebrow">검색 결과</p>
                <h3>{result.title || term || "검색 결과"}</h3>
              </div>
              {result.url && (
                <a className="panel__link" href={result.url} target="_blank" rel="noreferrer">
                  위키 문서 열기
                </a>
              )}
            </header>

            {result.summary ? (
              <pre className="panel__summary">{result.summary}</pre>
            ) : (
              <>
                <p>{result.message || "결과를 찾지 못했습니다."}</p>
                {result.options?.length ? (
                  <ul className="option-list">
                    {result.options.map((option) => (
                      <li key={option}>
                        <button type="button" className="chip" onClick={() => search(option, true)} disabled={loading}>
                          {option}
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </>
            )}
          </article>
        </div>
      )}
    </article>
  );
}
